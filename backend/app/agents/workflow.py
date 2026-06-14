import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from app.agents.state import SharedState
from app.services.rag_service import retrieve_relevant_chunks
from app.database import SessionLocal

logger = logging.getLogger("kalyx.agents")

# Helper to strip unsupported additionalProperties for Developer API mode compatibility
def strip_additional_properties(schema: Any) -> Any:
    if isinstance(schema, dict):
        schema.pop("additionalProperties", None)
        schema.pop("extraProperties", None)
        for k, v in list(schema.items()):
            schema[k] = strip_additional_properties(v)
    elif isinstance(schema, list):
        return [strip_additional_properties(item) for item in schema]
    return schema

# Helper to recursively inline references from $defs to simplify schema for LLMs
def resolve_defs(schema: Any, defs: Optional[Dict[str, Any]] = None) -> Any:
    if defs is None and isinstance(schema, dict):
        defs = schema.get("$defs", {})
        
    if isinstance(schema, dict):
        if "$ref" in schema:
            ref_path = schema["$ref"]
            def_name = ref_path.split("/")[-1]
            if def_name in defs:
                resolved = resolve_defs(defs[def_name], defs)
                # Merge keys other than $ref if any
                for k, v in schema.items():
                    if k != "$ref" and k not in resolved:
                        resolved[k] = v
                return resolved
        new_schema = {}
        for k, v in schema.items():
            if k == "$defs":
                continue
            new_schema[k] = resolve_defs(v, defs)
        return new_schema
    elif isinstance(schema, list):
        return [resolve_defs(item, defs) for item in schema]
    return schema

# Helper to run LLM prompts safely using Groq API via OpenAI client
def call_llm(system_prompt: str, user_prompt: str, response_format: str = "json", response_schema: Any = None) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.strip() == "" or api_key.startswith("your_"):
        raise ValueError("GROQ_API_KEY environment variable is not set. Please configure it in your .env file.")
        
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    
    # Pre-process Pydantic models to strip unsupported additionalProperties and resolve defs
    if response_schema is not None:
        if isinstance(response_schema, type) and issubclass(response_schema, BaseModel):
            schema_dict = response_schema.model_json_schema()
            schema_dict = strip_additional_properties(schema_dict)
            schema_dict = resolve_defs(schema_dict)
            response_schema = schema_dict

    import time
    backoff_times = [2, 5, 10, 20, 30, 45]
    attempt = 0
    while True:
        try:
            sys_content = system_prompt
            if response_schema is not None:
                sys_content += f"\n\nYou MUST return a JSON response matching the required structure/schema. Output actual data values for the fields defined in the schema, NOT the schema definition itself.\n\nCRITICAL: Do NOT output the schema itself. Do NOT output keys like '$defs', 'properties', 'type', 'required', etc., unless they are part of the actual data. Output concrete values.\n\nStrict JSON Schema target:\n{json.dumps(response_schema)}"
            elif response_format == "json":
                sys_content += "\n\nYou MUST return a JSON response. Do not output any markdown formatting (like ```json ... ```) or conversational filler; return raw JSON only."
                
            messages = [
                {"role": "system", "content": sys_content},
                {"role": "user", "content": user_prompt}
            ]
            
            response = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                messages=messages,
                response_format={"type": "json_object"} if (response_format == "json" or response_schema is not None) else None,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            err_str = str(e)
            is_transient = "429" in err_str or "503" in err_str or "rate limit" in err_str.lower()
            
            if is_transient and attempt < len(backoff_times):
                import re
                sleep_time = None
                try:
                    err_str_lower = err_str.lower()
                    if "try again in" in err_str_lower:
                        match = re.search(r"try again in ([\d\.]+)(ms|s)", err_str_lower)
                        if match:
                            val = float(match.group(1))
                            unit = match.group(2)
                            if unit == "ms":
                                sleep_time = (val / 1000.0) + 0.5
                            else:
                                sleep_time = val + 0.5
                except Exception:
                    pass
                
                if sleep_time is None:
                    sleep_time = backoff_times[attempt]
                
                logger.warning(f"[Groq API] Rate limit or transient error ({err_str}). Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
                attempt += 1
            else:
                logger.error(f"Error calling Groq API: {e}")
                raise e



# PYDANTIC STRUCTURED OUT-SCHEMAS (Enforcing educational standards at runtime)
class ModuleItem(BaseModel):
    id: int
    title: str
    topics: List[str]

class CurriculumMap(BaseModel):
    course_title: str
    modules: List[ModuleItem]
    gaps: List[str]

class LearningOutcomeItem(BaseModel):
    id: int
    text: str
    bloom_level: str

class LearningOutcomesList(BaseModel):
    learning_outcomes: List[LearningOutcomeItem]

class LessonItem(BaseModel):
    week: int
    module_id: int
    title: str
    objectives: str

class CurriculumPlan(BaseModel):
    duration_weeks: int
    lesson_sequence: List[LessonItem]

class SlideItem(BaseModel):
    slide_index: int
    title: str
    content: List[str]
    suggested_visuals: str

class SlideDeck(BaseModel):
    slides: List[SlideItem]

class NoteItem(BaseModel):
    slide_index: int = Field(..., description="The 1-based index of the slide this note corresponds to")
    talking_points: List[str] = Field(..., description="At least 8 to 10 highly detailed, comprehensive lecture talking points/explanations for this slide (MUST be at least 8 to 10 points)")
    teaching_tips: str = Field(..., description="Detailed interactive pedagogy tips and whiteboard layout guidelines")
    examples: List[str] = Field(..., description="At least 5 to 6 concrete, distinct, real-world clarifying examples/scenarios for this slide (MUST be at least 5 to 6 examples)")

class InstructorNotesList(BaseModel):
    notes: List[NoteItem] = Field(..., description="List of instructor notes, one for each slide in the deck")

class AssessmentItem(BaseModel):
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    bloom_level: str
    learning_outcome_id: int

class AssessmentBank(BaseModel):
    assessments: List[AssessmentItem]

class BloomReport(BaseModel):
    Remembering: int
    Understanding: int
    Applying: int
    Analyzing: int
    Evaluating: int
    Creating: int
    average_coverage: float
    recommendation: str

class ReadinessScore(BaseModel):
    score: float
    completeness: float
    outcome_coverage: float
    assessment_quality: float
    bloom_coverage: float
    industry_relevance: float
    breakdown: Dict[str, str]

class IndustryGapReport(BaseModel):
    status: str
    missing_topics: List[str]
    recommendations: List[str]

# Agent 1: Curriculum Analysis Agent
def curriculum_analysis_agent(state: SharedState) -> SharedState:
    state["logs"].append("Curriculum Analysis Agent started.")
    state["current_agent"] = "Curriculum Analysis Agent"
    
    if state.get("error_info"):
        state["logs"].append("Curriculum Analysis Agent skipped due to previous error.")
        return state
        
    course_id = state.get("course_id")
    rag_context = ""
    if course_id:
        try:
            db = SessionLocal()
            chunks = retrieve_relevant_chunks(db, course_id=course_id, query="syllabus course details topics modules learning outcomes objectives", limit=8)
            db.close()
            if chunks:
                rag_context = "\n### RELEVANT SYLLABUS REFERENCE CHUNKS:\n" + "\n".join([f"- {c['chunk_text']}" for c in chunks])
        except Exception as e:
            logger.warning(f"RAG context search bypassed: {e}")
            
    try:
        # Self-healing warning detection
        alert_context = ""
        if any("Audit Alert" in log for log in state["logs"]):
            alert_context = "\n### ACCREDITATION AUDIT WARNING:\nYour previous curriculum plan had insufficient higher-order Bloom levels. You MUST enrich the topics and structures to support advanced learning outcomes mapped strictly to 'Evaluating' or 'Creating' cognitive levels to ensure curriculum balance."

        sys_prompt = (
            "You are a Principal Curriculum Architect. "
            "Extract the core course title, structured modules, and comprehensive topics from the syllabus. "
            "Identify internal content/topic gaps within the syllabus structure. "
            "Return JSON matching the schema."
        )
        user_prompt = f"Analyze the following syllabus:\n{state['syllabus_text']}\n{rag_context}\n{alert_context}"
        
        res = call_llm(sys_prompt, user_prompt, response_schema=CurriculumMap)
        data = json.loads(res)
        
        state["curriculum_map"] = data
        state["logs"].append("Curriculum Analysis successfully processed via LLM.")
    except Exception as e:
        logger.error(f"Curriculum Analysis Error: {e}")
        err_str = str(e)
        err_type = "429" if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str else "503" if "503" in err_str or "UNAVAILABLE" in err_str else "500"
        state["error_info"] = {
            "status": "partial_generation",
            "failed_agent": "Curriculum Analysis Agent",
            "error_type": err_type,
            "successful_agents": [],
            "retry_recommended": True
        }
        state["logs"].append(f"Curriculum Analysis Agent failed: {err_str}")
        
    return state


# Agent 2: Learning Outcome Agent
def learning_outcome_agent(state: SharedState) -> SharedState:
    state["logs"].append("Learning Outcome Agent started.")
    state["current_agent"] = "Learning Outcome Agent"
    
    if state.get("error_info"):
        state["logs"].append("Learning Outcome Agent skipped due to previous error.")
        return state
        
    try:
        sys_prompt = (
            "You are an Educational Standards Director. "
            "Based on the provided curriculum map, generate clear, actionable, measurable learning outcomes. "
            "Each outcome must be mapped strictly to one of the six Bloom's Revised Taxonomy levels (Remembering, Understanding, Applying, Analyzing, Evaluating, Creating). "
            "Return JSON matching the schema."
        )
        user_prompt = f"Generate learning outcomes for the curriculum map: {json.dumps(state['curriculum_map'])}"
        
        res = call_llm(sys_prompt, user_prompt, response_schema=LearningOutcomesList)
        data = json.loads(res)
        
        outcomes_list = []
        if isinstance(data, list):
            outcomes_list = data
        elif isinstance(data, dict):
            outcomes_list = data.get("learning_outcomes", [])
            
        state["learning_outcomes"] = [{"id": o.get("id"), "text": o.get("text"), "bloom_level": o.get("bloom_level")} for o in outcomes_list if isinstance(o, dict)]
        state["logs"].append("Learning Outcome Agent successfully processed via LLM.")
    except Exception as e:
        logger.error(f"Learning Outcome Error: {e}")
        err_str = str(e)
        err_type = "429" if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str else "503" if "503" in err_str or "UNAVAILABLE" in err_str else "500"
        state["error_info"] = {
            "status": "partial_generation",
            "failed_agent": "Learning Outcome Agent",
            "error_type": err_type,
            "successful_agents": ["Curriculum Analysis Agent"],
            "retry_recommended": True
        }
        state["logs"].append(f"Learning Outcome Agent failed: {err_str}")
        
    return state


# Agent 3: Curriculum Planning Agent
def curriculum_planning_agent(state: SharedState) -> SharedState:
    state["logs"].append("Curriculum Planning Agent started.")
    state["current_agent"] = "Curriculum Planning Agent"
    
    if state.get("error_info"):
        state["logs"].append("Curriculum Planning Agent skipped due to previous error.")
        return state
        
    try:
        sys_prompt = (
            "You are an Academic Planning Expert. "
            "Design a detailed, week-by-week lesson roadmap (sequence of lessons) of at least 25 to 30 detailed lessons/weeks. "
            "Ensure it sequences all topics from the curriculum map logically and aligns with the generated learning outcomes. "
            "Return JSON matching the schema."
        )
        user_prompt_base = (
            f"Create a weekly curriculum plan for curriculum map: {json.dumps(state['curriculum_map'])} "
            f"and learning outcomes: {json.dumps(state['learning_outcomes'])}. "
            f"CRITICAL REQUIREMENT: You MUST generate at least 25 to 30 distinct weeks in the lesson_sequence. Break down topics and subtopics into multiple weeks if necessary."
        )
        
        attempts = 3
        data = {}
        for attempt in range(attempts):
            feedback = ""
            if attempt > 0:
                feedback = f"\n\nWARNING: In your previous attempt, you only generated {len(data.get('lesson_sequence', []))} weeks. You MUST generate at least 25 to 30 weeks (lesson sequence items). Please expand the topics and create more fine-grained weekly lessons."
            
            res = call_llm(sys_prompt, user_prompt_base + feedback, response_schema=CurriculumPlan)
            data = json.loads(res)
            
            lesson_sequence = data.get("lesson_sequence", [])
            if len(lesson_sequence) >= 25:
                break
        
        state["curriculum_plan"] = data
        state["logs"].append(f"Curriculum Planning Agent successfully processed via LLM with {len(data.get('lesson_sequence', []))} weeks.")
    except Exception as e:
        logger.error(f"Curriculum Planning Error: {e}")
        err_str = str(e)
        err_type = "429" if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str else "503" if "503" in err_str or "UNAVAILABLE" in err_str else "500"
        state["error_info"] = {
            "status": "partial_generation",
            "failed_agent": "Curriculum Planning Agent",
            "error_type": err_type,
            "successful_agents": ["Curriculum Analysis Agent", "Learning Outcome Agent"],
            "retry_recommended": True
        }
        state["logs"].append(f"Curriculum Planning Agent failed: {err_str}")
        
    return state


# Agent 4: Slide Generation Agent
def slide_generation_agent(state: SharedState) -> SharedState:
    state["logs"].append("Slide Generation Agent started.")
    state["current_agent"] = "Slide Generation Agent"
    
    if state.get("error_info"):
        state["logs"].append("Slide Generation Agent skipped due to previous error.")
        return state
        
    course_id = state.get("course_id")
    rag_context = ""
    if course_id:
        try:
            db = SessionLocal()
            chunks = retrieve_relevant_chunks(db, course_id=course_id, query="course content core concepts theory details lecture explanations student examples", limit=5)
            db.close()
            if chunks:
                rag_context = "\n### RELEVANT CONCEPT DETAILS:\n" + "\n".join([f"- {c['chunk_text']}" for c in chunks])
        except Exception as e:
            logger.warning(f"RAG context search bypassed: {e}")
            
    try:
        personalization = state.get("personalization_profile", {})
        style_instruction = ""
        if personalization:
            style_instruction = f" Apply style/theme: {personalization.get('style', 'Sleek Dark Mode')} and tone: {personalization.get('tone', 'Professional & Academic')}."
            if personalization.get("customInstructions"):
                style_instruction += f" Additional instructions: {personalization.get('customInstructions')}"

        sys_prompt = (
            "You are an Elite Instructional Designer. "
            "Generate beautiful, logically organized, highly detailed slides based on the curriculum sequence. "
            "For each slide, construct complete concepts, and extensive detailed explanations. "
            "Each item in the content list MUST be a long, highly informative paragraph of 3-4 sentences containing deep academic/technical explanations, NOT short summary bullet points. Make the slide deck extremely detailed. "
            f"Return JSON matching the schema.{style_instruction}"
        )
        
        lesson_sequence = []
        if isinstance(state.get("curriculum_plan"), dict):
            lesson_sequence = state["curriculum_plan"].get("lesson_sequence", [])
        elif isinstance(state.get("curriculum_plan"), list):
            lesson_sequence = state["curriculum_plan"]
            
        slides_list = []
        batch_size = 5
        for i in range(0, len(lesson_sequence), batch_size):
            batch_lessons = lesson_sequence[i:i+batch_size]
            user_prompt = f"Generate slide deck items for this batch of lessons/weeks: {json.dumps(batch_lessons)}\n{rag_context}"
            
            res = call_llm(sys_prompt, user_prompt, response_schema=SlideDeck)
            data = json.loads(res)
            
            batch_slides = []
            if isinstance(data, list):
                batch_slides = data
            elif isinstance(data, dict):
                batch_slides = data.get("slides", [])
                
            slides_list.extend(batch_slides)
            
        state["slide_deck"] = [{"slide_index": s.get("slide_index"), "title": s.get("title"), "content": s.get("content", []), "suggested_visuals": s.get("suggested_visuals", "")} for s in slides_list if isinstance(s, dict)]
        state["logs"].append(f"Slide Generation Agent successfully processed {len(state['slide_deck'])} slides via LLM.")
    except Exception as e:
        logger.error(f"Slide Generation Error: {e}")
        err_str = str(e)
        err_type = "429" if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str else "503" if "503" in err_str or "UNAVAILABLE" in err_str else "500"
        state["error_info"] = {
            "status": "partial_generation",
            "failed_agent": "Slide Generation Agent",
            "error_type": err_type,
            "successful_agents": ["Curriculum Analysis Agent", "Learning Outcome Agent", "Curriculum Planning Agent"],
            "retry_recommended": True
        }
        state["logs"].append(f"Slide Generation Agent failed: {err_str}")
        
    return state


# Agent 5: Instructor Notes Agent
def instructor_notes_agent(state: SharedState) -> SharedState:
    state["logs"].append("Instructor Notes Agent started.")
    state["current_agent"] = "Instructor Notes Agent"
    
    if state.get("error_info"):
        state["logs"].append("Instructor Notes Agent skipped due to previous error.")
        return state
        
    try:
        personalization = state.get("personalization_profile", {})
        style_instruction = ""
        if personalization:
            style_instruction = f" Apply tone: {personalization.get('tone', 'Professional & Academic')}."
            if personalization.get("customInstructions"):
                style_instruction += f" Additional instructions: {personalization.get('customInstructions')}"

        sys_prompt = (
            "You are an Expert Educator. "
            "Generate instructor lecture scripts/notes for the generated slides. "
            "For each slide note, you MUST generate at least 8-10 highly detailed, comprehensive lecture talking points/explanations (minimum 8 talking points), detailed interactive pedagogy tips, whiteboard layout guidelines, and at least 5-6 concrete real-world clarifying examples (minimum 5 examples). Make notes extremely detailed and comprehensive. "
            f"Return JSON matching the schema.{style_instruction}"
        )
        
        slide_deck = state.get("slide_deck", [])
        notes_list = []
        batch_size = 5
        
        for i in range(0, len(slide_deck), batch_size):
            batch_slides = slide_deck[i:i+batch_size]
            user_prompt = f"Generate instructor notes for this batch of slides: {json.dumps(batch_slides)}"
            
            res = call_llm(sys_prompt, user_prompt, response_schema=InstructorNotesList)
            data = json.loads(res)
            
            batch_notes = []
            if isinstance(data, list):
                batch_notes = data
            elif isinstance(data, dict):
                batch_notes = data.get("notes", [])
                
            notes_list.extend(batch_notes)
            
        state["instructor_notes"] = [{"slide_index": n.get("slide_index"), "talking_points": n.get("talking_points", []), "teaching_tips": n.get("teaching_tips", ""), "examples": n.get("examples", [])} for n in notes_list if isinstance(n, dict)]
        state["logs"].append(f"Instructor Notes Agent successfully processed {len(state['instructor_notes'])} slide notes via LLM.")
    except Exception as e:
        logger.error(f"Instructor Notes Error: {e}")
        err_str = str(e)
        err_type = "429" if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str else "503" if "503" in err_str or "UNAVAILABLE" in err_str else "500"
        state["error_info"] = {
            "status": "partial_generation",
            "failed_agent": "Instructor Notes Agent",
            "error_type": err_type,
            "successful_agents": ["Curriculum Analysis Agent", "Learning Outcome Agent", "Curriculum Planning Agent", "Slide Generation Agent"],
            "retry_recommended": True
        }
        state["logs"].append(f"Instructor Notes Agent failed: {err_str}")
        
    return state


# Agent 6: Assessment Agent
def assessment_agent(state: SharedState) -> SharedState:
    state["logs"].append("Assessment Agent started.")
    state["current_agent"] = "Assessment Agent"
    
    if state.get("error_info"):
        state["logs"].append("Assessment Agent skipped due to previous error.")
        return state
        
    try:
        sys_prompt = (
            "You are a Psychometric Evaluator and Examination Director. "
            "Design highly rigorous multiple-choice assessment questions (MCQs with options and correct answers). "
            "You MUST generate distinct high-quality MCQs covering all aspects of the curriculum mapped to learning outcomes. "
            "Return JSON matching the schema."
        )
        
        learning_outcomes = state.get("learning_outcomes", [])
        slide_deck = state.get("slide_deck", [])
        # Extract only index and title to reduce prompt token footprint
        slide_summary = [{"slide_index": s.get("slide_index"), "title": s.get("title")} for s in slide_deck]
        
        assessments_list = []
        num_questions_per_batch = 6
        num_batches = 5
        
        for b in range(num_batches):
            user_prompt = (
                f"Generate exactly {num_questions_per_batch} distinct high-quality MCQs (Batch {b+1}/5) covering outcomes: {json.dumps(learning_outcomes)} "
                f"and slides: {json.dumps(slide_summary)}. Each question must be uniquely mapped to a learning_outcome_id."
            )
            
            res = call_llm(sys_prompt, user_prompt, response_schema=AssessmentBank)
            data = json.loads(res)
            
            batch_assessments = []
            if isinstance(data, list):
                batch_assessments = data
            elif isinstance(data, dict):
                batch_assessments = data.get("assessments", [])
                
            assessments_list.extend(batch_assessments)
            
        state["assessment_bank"] = [
            {
                "question_text": a.get("question_text"), 
                "question_type": a.get("question_type"), 
                "options": a.get("options", []), 
                "correct_answer": a.get("correct_answer"), 
                "bloom_level": a.get("bloom_level", "Remembering"), 
                "learning_outcome_id": a.get("learning_outcome_id")
            } 
            for a in assessments_list 
            if isinstance(a, dict) and a.get("question_text") and a.get("question_type")
        ]
        state["logs"].append(f"Assessment Agent successfully processed {len(state['assessment_bank'])} MCQs via LLM.")
    except Exception as e:
        logger.error(f"Assessment Error: {e}")
        err_str = str(e)
        err_type = "429" if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str else "503" if "503" in err_str or "UNAVAILABLE" in err_str else "500"
        state["error_info"] = {
            "status": "partial_generation",
            "failed_agent": "Assessment Agent",
            "error_type": err_type,
            "successful_agents": ["Curriculum Analysis Agent", "Learning Outcome Agent", "Curriculum Planning Agent", "Slide Generation Agent", "Instructor Notes Agent"],
            "retry_recommended": True
        }
        state["logs"].append(f"Assessment Agent failed: {err_str}")
        
    return state


# Agent 7: Bloom Audit Agent
def bloom_audit_agent(state: SharedState) -> SharedState:
    state["logs"].append("Bloom Audit Agent started.")
    state["current_agent"] = "Bloom Audit Agent"
    
    if state.get("error_info"):
        state["logs"].append("Bloom Audit Agent skipped due to previous error.")
        return state
        
    try:
        sys_prompt = (
            "You are an Educational Quality Assurance Auditor. "
            "Review the learning outcomes and assessments to calculate the exact cognitive balance across the six Bloom dimensions, "
            "and provide high-impact recommendations to improve cognitive depth. "
            "You MUST calculate and return the average_coverage as a decimal float value between 0.0 and 100.0 (e.g., 75.5 or 63.3). "
            "Do NOT output mathematical expressions, divisions, slashes, or formulas (like '38 / 60') for average_coverage. It must be a raw float value. "
            "Return JSON matching the schema."
        )
        user_prompt = (
            f"Perform a Bloom audit for outcomes: {json.dumps(state['learning_outcomes'])} "
            f"and assessments: {json.dumps(state['assessment_bank'])}"
        )
        
        res = call_llm(sys_prompt, user_prompt, response_schema=BloomReport)
        data = json.loads(res)
        
        state["bloom_report"] = data
        state["logs"].append("Bloom Audit Agent successfully processed via LLM.")
    except Exception as e:
        logger.error(f"Bloom Audit Error: {e}")
        err_str = str(e)
        err_type = "429" if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str else "503" if "503" in err_str or "UNAVAILABLE" in err_str else "500"
        state["error_info"] = {
            "status": "partial_generation",
            "failed_agent": "Bloom Audit Agent",
            "error_type": err_type,
            "successful_agents": ["Curriculum Analysis Agent", "Learning Outcome Agent", "Curriculum Planning Agent", "Slide Generation Agent", "Instructor Notes Agent", "Assessment Agent"],
            "retry_recommended": True
        }
        state["logs"].append(f"Bloom Audit Agent failed: {err_str}")
        
    return state


# Agent 8: Industry Gap Agent
def industry_gap_agent(state: SharedState) -> SharedState:
    state["logs"].append("Industry Gap Agent started.")
    state["current_agent"] = "Industry Gap Agent"
    
    if state.get("error_info"):
        state["logs"].append("Industry Gap Agent skipped due to previous error.")
        return state
        
    course_id = state.get("course_id")
    rag_context = ""
    if course_id:
        try:
            db = SessionLocal()
            chunks = retrieve_relevant_chunks(db, course_id=course_id, query="modern industrial requirements skills tools technology", limit=5)
            db.close()
            if chunks:
                rag_context = "\n### RELEVANT INDUSTRIAL STANDARD CHUNKS:\n" + "\n".join([f"- {c['chunk_text']}" for c in chunks])
        except Exception as e:
            logger.warning(f"RAG context search bypassed: {e}")
            
    try:
        sys_prompt = (
            "You are a Silicon Valley Tech Lead and Industry Readiness Auditor. "
            "Compare the course modules and topics against modern technology and industry requirements to identify missing critical topics and recommend updates. "
            "Return JSON matching the schema."
        )
        user_prompt = (
            f"Analyze industry gaps for curriculum map: {json.dumps(state['curriculum_map'])} "
            f"and learning outcomes: {json.dumps(state['learning_outcomes'])}.\n"
            f"Industrial context: {rag_context}"
        )
        
        res = call_llm(sys_prompt, user_prompt, response_schema=IndustryGapReport)
        data = json.loads(res)
        
        state["industry_gap_report"] = data
        state["logs"].append("Industry Gap Agent successfully processed via LLM.")
    except Exception as e:
        logger.error(f"Industry Gap Error: {e}")
        err_str = str(e)
        err_type = "429" if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str else "503" if "503" in err_str or "UNAVAILABLE" in err_str else "500"
        state["error_info"] = {
            "status": "partial_generation",
            "failed_agent": "Industry Gap Agent",
            "error_type": err_type,
            "successful_agents": ["Curriculum Analysis Agent", "Learning Outcome Agent", "Curriculum Planning Agent", "Slide Generation Agent", "Instructor Notes Agent", "Assessment Agent", "Bloom Audit Agent"],
            "retry_recommended": True
        }
        state["logs"].append(f"Industry Gap Agent failed: {err_str}")
        
    return state


# Agent 9: Readiness Score Agent
def readiness_score_agent(state: SharedState) -> SharedState:
    state["logs"].append("Readiness Score Agent started.")
    state["current_agent"] = "Readiness Score Agent"
    
    if state.get("error_info"):
        state["logs"].append("Readiness Score Agent skipped due to previous error.")
        return state
        
    try:
        sys_prompt = (
            "You are a Curriculum Quality Director. "
            "Evaluate the overall quality, completeness, and readiness of the generated course deck on a scale of 0 to 100. "
            "Each score or coverage attribute must be a raw decimal float value between 0.0 and 100.0 (e.g., 85.0 or 92.5). "
            "Do NOT output mathematical expressions, divisions, slashes, or formulas for any float fields. It must be a raw float value. "
            "Return JSON matching the schema."
        )
        slide_summary = [{"slide_index": s.get("slide_index"), "title": s.get("title")} for s in state.get("slide_deck", [])]
        
        # Summarize assessments to avoid Groq TPM limits
        assessments_raw = state.get("assessment_bank", [])
        if isinstance(assessments_raw, dict):
            assessments_list = assessments_raw.get("assessments", [])
        else:
            assessments_list = assessments_raw

        assessment_summary = []
        if isinstance(assessments_list, list):
            for a in assessments_list:
                if isinstance(a, dict):
                    assessment_summary.append({
                        "question_text": a.get("question_text", "")[:60] + "...",
                        "bloom_level": a.get("bloom_level", "")
                    })
        
        user_prompt = (
            f"Evaluate course readiness for curriculum: {json.dumps(state['curriculum_map'])}, "
            f"outcomes: {json.dumps(state['learning_outcomes'])}, slides: {json.dumps(slide_summary)}, "
            f"assessments_summary: {json.dumps(assessment_summary)}, and Bloom audit: {json.dumps(state['bloom_report'])}."
        )
        
        res = call_llm(sys_prompt, user_prompt, response_schema=ReadinessScore)
        data = json.loads(res)
        
        state["readiness_score"] = data
        state["logs"].append("Readiness Score Agent successfully processed via LLM.")
    except Exception as e:
        logger.error(f"Readiness Score Error: {e}")
        err_str = str(e)
        err_type = "429" if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str else "503" if "503" in err_str or "UNAVAILABLE" in err_str else "500"
        state["error_info"] = {
            "status": "partial_generation",
            "failed_agent": "Readiness Score Agent",
            "error_type": err_type,
            "successful_agents": ["Curriculum Analysis Agent", "Learning Outcome Agent", "Curriculum Planning Agent", "Slide Generation Agent", "Instructor Notes Agent", "Assessment Agent", "Bloom Audit Agent", "Industry Gap Agent"],
            "retry_recommended": True
        }
        state["logs"].append(f"Readiness Score Agent failed: {err_str}")
        
    state["logs"].append("LangGraph workflow execution completed successfully.")
    state["current_agent"] = "Done"
    
    return state


# Helper conditional function for self-healing Bloom taxonomy loops
def route_bloom_coverage(state: SharedState) -> str:
    if state.get("error_info"):
        return "industry_gap"
        
    report = state.get("bloom_report", {})
    if not report:
        return "industry_gap"
    avg = report.get("average_coverage", 100)
    
    # Count previous loop iterations in the logs
    loops = sum(1 for log in state.get("logs", []) if "Triggering self-healing feedback loop" in log)
    
    if avg < 75 and loops < 1:
        state["logs"].append("Audit Alert: Higher-order Bloom cognitive coverage is below 75%. Triggering self-healing feedback loop back to Curriculum Analysis Agent to enrich outcome balance.")
        return "curriculum_analysis"
    else:
        return "industry_gap"


def make_telemetry_agent(agent_fn, agent_name):
    def wrapped_agent(state: SharedState) -> SharedState:
        import time
        from datetime import datetime
        
        start_time = time.time()
        started_at = datetime.utcnow().isoformat() + "Z"
        
        has_error_before = bool(state.get("error_info"))
        
        new_state = agent_fn(state)
        
        end_time = time.time()
        completed_at = datetime.utcnow().isoformat() + "Z"
        duration_ms = int(round((end_time - start_time) * 1000))
        
        has_error_after = bool(new_state.get("error_info"))
        
        if has_error_after and not has_error_before:
            status = "failure"
        else:
            status = "success"
            
        telemetry_item = {
            "agent": agent_name,
            "status": status,
            "start_time": started_at,
            "end_time": completed_at,
            "duration_ms": duration_ms
        }
        
        if "pipeline_telemetry" not in new_state or not isinstance(new_state["pipeline_telemetry"], list):
            new_state["pipeline_telemetry"] = []
            
        existing_idx = -1
        for idx, item in enumerate(new_state["pipeline_telemetry"]):
            if item["agent"] == agent_name:
                existing_idx = idx
                break
                
        if existing_idx != -1:
            new_state["pipeline_telemetry"][existing_idx] = telemetry_item
        else:
            new_state["pipeline_telemetry"].append(telemetry_item)
            
        return new_state
    return wrapped_agent


# Compile the Workflow Graph
def build_workflow() -> StateGraph:
    workflow = StateGraph(SharedState)
    
    # Register the 9 nodes wrapped in telemetry recorder
    workflow.add_node("curriculum_analysis", make_telemetry_agent(curriculum_analysis_agent, "Curriculum Analysis Agent"))
    workflow.add_node("learning_outcome", make_telemetry_agent(learning_outcome_agent, "Learning Outcome Agent"))
    workflow.add_node("curriculum_planning", make_telemetry_agent(curriculum_planning_agent, "Curriculum Planning Agent"))
    workflow.add_node("slide_generation", make_telemetry_agent(slide_generation_agent, "Slide Generation Agent"))
    workflow.add_node("instructor_notes", make_telemetry_agent(instructor_notes_agent, "Instructor Notes Agent"))
    workflow.add_node("assessment", make_telemetry_agent(assessment_agent, "Assessment Agent"))
    workflow.add_node("bloom_audit", make_telemetry_agent(bloom_audit_agent, "Bloom Audit Agent"))
    workflow.add_node("industry_gap", make_telemetry_agent(industry_gap_agent, "Industry Gap Agent"))
    workflow.add_node("readiness_score", make_telemetry_agent(readiness_score_agent, "Readiness Score Agent"))
    
    # Establish entry point
    workflow.set_entry_point("curriculum_analysis")
    
    # Sequential flow edges
    workflow.add_edge("curriculum_analysis", "learning_outcome")
    workflow.add_edge("learning_outcome", "curriculum_planning")
    workflow.add_edge("curriculum_planning", "slide_generation")
    workflow.add_edge("slide_generation", "instructor_notes")
    workflow.add_edge("instructor_notes", "assessment")
    workflow.add_edge("assessment", "bloom_audit")
    
    # Conditional routing edge for self-healing taxonomy auditing
    workflow.add_conditional_edges(
        "bloom_audit",
        route_bloom_coverage,
        {
            "curriculum_analysis": "curriculum_analysis",
            "industry_gap": "industry_gap"
        }
    )
    
    workflow.add_edge("industry_gap", "readiness_score")
    workflow.add_edge("readiness_score", END)
    
    return workflow.compile()
