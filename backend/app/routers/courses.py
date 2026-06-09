import os
import shutil
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.routers.auth import get_current_user
from app.models import (
    User, Course, Syllabus, CurriculumAnalysis, LearningOutcome,
    GeneratedSlide, InstructorNote, Assessment, ReadinessScore, UploadedDocument
)
from app.agents.workflow import build_workflow
from app.services.rag_service import process_and_index_document
from app.security import limit_course_creation, limit_syllabus_upload, limit_analysis_generation

router = APIRouter(prefix="/courses", tags=["Courses"])

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    created_at: Any
    
    class Config:
        orm_mode = True

@router.get("/")
def list_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Course).filter(Course.user_id == current_user.id).all()

@router.post("/", dependencies=[Depends(limit_course_creation)])
def create_course(payload: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not payload.title or not payload.title.strip():
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body", "title"], "msg": "Course title cannot be empty", "type": "value_error"}]
        )
    if not payload.description or not payload.description.strip():
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body", "description"], "msg": "Course description cannot be empty", "type": "value_error"}]
        )
    course = Course(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

@router.get("/{course_id}")
def get_course_details(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify ownership
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    analysis = db.query(CurriculumAnalysis).filter(CurriculumAnalysis.course_id == course_id).first()
    outcomes = db.query(LearningOutcome).filter(LearningOutcome.course_id == course_id).all()
    slides = db.query(GeneratedSlide).filter(GeneratedSlide.course_id == course_id).order_by(GeneratedSlide.slide_index).all()
    notes = db.query(InstructorNote).filter(InstructorNote.course_id == course_id).order_by(InstructorNote.slide_index).all()
    assessments = db.query(Assessment).filter(Assessment.course_id == course_id).all()
    score = db.query(ReadinessScore).filter(ReadinessScore.course_id == course_id).first()
    
    return {
        "course": {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "created_at": course.created_at
        },
        "curriculum_analysis": {
            "curriculum_map": analysis.curriculum_map if analysis else None,
            "gap_analysis": analysis.gap_analysis if analysis else None,
            "industry_gap_report": analysis.industry_gap_report if analysis else None,
            "pipeline_telemetry": getattr(analysis, "pipeline_telemetry", []) if analysis else []
        } if analysis else None,
        "learning_outcomes": [
            {"id": o.id, "text": o.outcome_text, "bloom_level": o.bloom_level} for o in outcomes
        ],
        "slides": [
            {"id": s.id, "slide_index": s.slide_index, "title": s.title, "content": s.content, "suggested_visuals": s.suggested_visuals}
            for s in slides
        ],
        "notes": [
            {"id": n.id, "slide_index": n.slide_index, "talking_points": n.talking_points, "teaching_tips": n.teaching_tips, "examples": n.examples}
            for n in notes
        ],
        "assessments": [
            {
                "id": a.id,
                "question_text": a.question_text,
                "question_type": a.question_type,
                "options": a.options,
                "correct_answer": a.correct_answer,
                "bloom_level": a.bloom_level,
                "learning_outcome_id": a.learning_outcome_id
            } for a in assessments
        ],
        "readiness_score": {
            "score": score.score,
            "completeness": score.completeness,
            "outcome_coverage": score.outcome_coverage,
            "assessment_quality": score.assessment_quality,
            "bloom_coverage": score.bloom_coverage,
            "industry_relevance": score.industry_relevance,
            "breakdown": score.breakdown
        } if score else None
    }

@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"message": f"Course {course_id} deleted successfully"}

def save_workflow_outputs(db: Session, course_id: int, final_state: Dict[str, Any]):
    # Clean previous generated course details to ensure clean overwrite
    db.query(CurriculumAnalysis).filter(CurriculumAnalysis.course_id == course_id).delete()
    db.query(LearningOutcome).filter(LearningOutcome.course_id == course_id).delete()
    db.query(GeneratedSlide).filter(GeneratedSlide.course_id == course_id).delete()
    db.query(InstructorNote).filter(InstructorNote.course_id == course_id).delete()
    db.query(Assessment).filter(Assessment.course_id == course_id).delete()
    db.query(ReadinessScore).filter(ReadinessScore.course_id == course_id).delete()
    db.commit()

    # Conditionally save Curriculum Analysis
    if final_state.get("curriculum_map") and isinstance(final_state["curriculum_map"], dict) and len(final_state["curriculum_map"]) > 0:
        bloom_rec = None
        if final_state.get("bloom_report") and isinstance(final_state["bloom_report"], dict) and len(final_state["bloom_report"]) > 0:
            bloom_rec = final_state["bloom_report"].get("recommendation")
            
        ind_gap = None
        if final_state.get("industry_gap_report") and isinstance(final_state["industry_gap_report"], dict) and len(final_state["industry_gap_report"]) > 0:
            ind_gap = final_state["industry_gap_report"]
            
        analysis = CurriculumAnalysis(
            course_id=course_id,
            curriculum_map=final_state["curriculum_map"],
            gap_analysis=bloom_rec if bloom_rec else "Review learning modules completeness.",
            industry_gap_report=ind_gap,
            pipeline_telemetry=final_state.get("pipeline_telemetry", [])
        )
        db.add(analysis)
        db.commit()

    # Conditionally save Learning Outcomes
    outcome_map = {}
    if final_state.get("learning_outcomes") and isinstance(final_state["learning_outcomes"], list) and len(final_state["learning_outcomes"]) > 0:
        for item in final_state["learning_outcomes"]:
            if isinstance(item, dict) and "text" in item and "bloom_level" in item:
                outcome = LearningOutcome(
                    course_id=course_id,
                    outcome_text=item["text"],
                    bloom_level=item["bloom_level"]
                )
                db.add(outcome)
                db.commit()
                outcome_map[item.get("id")] = outcome.id

    # Conditionally save Slides
    if final_state.get("slide_deck") and isinstance(final_state["slide_deck"], list) and len(final_state["slide_deck"]) > 0:
        for slide_item in final_state["slide_deck"]:
            if isinstance(slide_item, dict) and "slide_index" in slide_item and "title" in slide_item and "content" in slide_item:
                slide = GeneratedSlide(
                    course_id=course_id,
                    slide_index=slide_item["slide_index"],
                    title=slide_item["title"],
                    content=slide_item["content"],
                    suggested_visuals=slide_item.get("suggested_visuals", "")
                )
                db.add(slide)

    # Conditionally save Speaker Notes
    if final_state.get("instructor_notes") and isinstance(final_state["instructor_notes"], list) and len(final_state["instructor_notes"]) > 0:
        for note_item in final_state["instructor_notes"]:
            if isinstance(note_item, dict) and "slide_index" in note_item and "talking_points" in note_item:
                note = InstructorNote(
                    course_id=course_id,
                    slide_index=note_item["slide_index"],
                    talking_points=note_item["talking_points"],
                    teaching_tips=note_item.get("teaching_tips", ""),
                    examples=note_item.get("examples", [])
                )
                db.add(note)

    # Conditionally save Assessments
    if final_state.get("assessment_bank") and isinstance(final_state["assessment_bank"], list) and len(final_state["assessment_bank"]) > 0:
        for q_item in final_state["assessment_bank"]:
            if isinstance(q_item, dict) and "question_text" in q_item and "question_type" in q_item:
                mapped_outcome_id = outcome_map.get(q_item.get("learning_outcome_id")) if outcome_map else None
                assessment = Assessment(
                    course_id=course_id,
                    learning_outcome_id=mapped_outcome_id,
                    question_text=q_item["question_text"],
                    question_type=q_item["question_type"],
                    options=q_item.get("options"),
                    correct_answer=q_item.get("correct_answer"),
                    bloom_level=q_item.get("bloom_level", "Remembering")
                )
                db.add(assessment)

    # Conditionally save Readiness Score
    if final_state.get("readiness_score") and isinstance(final_state["readiness_score"], dict) and len(final_state["readiness_score"]) > 0:
        scr = final_state["readiness_score"]
        score = ReadinessScore(
            course_id=course_id,
            score=scr.get("score", 70.0),
            completeness=scr.get("completeness", 70.0),
            outcome_coverage=scr.get("outcome_coverage", 70.0),
            assessment_quality=scr.get("assessment_quality", 70.0),
            bloom_coverage=scr.get("bloom_coverage", 70.0),
            industry_relevance=scr.get("industry_relevance", 70.0),
            breakdown=scr.get("breakdown", {})
        )
        db.add(score)

    db.commit()


@router.post("/{course_id}/analyze", dependencies=[Depends(limit_syllabus_upload)])
def analyze_syllabus(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validation checks
    if not file.filename or not file.filename.strip():
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body", "file"], "msg": "No file uploaded", "type": "value_error"}]
        )
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".txt"]:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body", "file"], "msg": "Unsupported file format. Only PDF and TXT are supported.", "type": "value_error"}]
        )
        
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size == 0:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body", "file"], "msg": "Uploaded syllabus file is empty", "type": "value_error"}]
        )
        
    if size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body", "file"], "msg": "File is too large. Maximum size allowed is 10MB.", "type": "value_error"}]
        )

    # 1. Verify course ownership
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Create scratch uploads folder in app workspace
    upload_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Extract syllabus raw text
    from app.services.rag_service import extract_text_from_pdf
    
    raw_text = ""
    if file.filename.lower().endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_path)
    else:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
        except Exception:
            raise HTTPException(status_code=400, detail="Could not read uploaded syllabus file.")
            
    if not raw_text or len(raw_text.strip()) == 0:
        raw_text = f"Syllabus file: {file.filename}\nDefault Course: Advanced Machine Learning and Neural Networks"
        
    # Save Syllabus record
    syllabus_record = Syllabus(
        course_id=course_id,
        raw_text=raw_text,
        file_name=file.filename,
        file_path=file_path
    )
    db.add(syllabus_record)
    
    # Process document for RAG search
    try:
        process_and_index_document(db, course_id, file.filename, file_path, document_type="SYLLABUS")
    except Exception as e:
        print(f"[RAG] Indexing syllabus document: {e}")
        
    db.commit()
    
    # 2. RUN LANGGRAPH WORKFLOW
    compiled_graph = build_workflow()
    
    from app.models import PersonalizationProfile
    profile_record = db.query(PersonalizationProfile).filter(PersonalizationProfile.course_id == course_id).first()
    personalization_profile = profile_record.profile if profile_record else {}
    
    initial_state = {
        "course_id": course_id,
        "syllabus_text": raw_text,
        "curriculum_map": {},
        "learning_outcomes": [],
        "curriculum_plan": {},
        "slide_deck": [],
        "instructor_notes": [],
        "assessment_bank": [],
        "bloom_report": {},
        "readiness_score": {},
        "industry_gap_report": {},
        "personalization_profile": personalization_profile,
        "logs": ["Starting multi-agent syllabus analysis pipeline..."],
        "current_agent": "Curriculum Intelligence Agent",
        "pipeline_telemetry": []
    }
    
    # Invoke State Graph
    final_state = compiled_graph.invoke(initial_state)
    
    error_info = final_state.get("error_info")
    save_workflow_outputs(db, course_id, final_state)
    
    if error_info:
        return {
            "status": "partial_generation",
            "failed_agent": error_info.get("failed_agent"),
            "error_type": error_info.get("error_type"),
            "successful_agents": error_info.get("successful_agents", []),
            "retry_recommended": error_info.get("retry_recommended", True),
            "logs": final_state["logs"],
            "pipeline_telemetry": final_state.get("pipeline_telemetry", [])
        }
        
    return {
        "status": "Success",
        "message": "Syllabus processed and educational package generated successfully.",
        "course_id": course_id,
        "logs": final_state["logs"],
        "pipeline_telemetry": final_state.get("pipeline_telemetry", [])
    }

@router.post("/{course_id}/regenerate", dependencies=[Depends(limit_analysis_generation)])
def regenerate_course_deck(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    syllabus_record = db.query(Syllabus).filter(Syllabus.course_id == course_id).order_by(Syllabus.id.desc()).first()
    if not syllabus_record:
        raise HTTPException(status_code=400, detail="No syllabus found for this course. Please upload a syllabus first.")
        
    raw_text = syllabus_record.raw_text
    compiled_graph = build_workflow()
    
    from app.models import PersonalizationProfile
    profile_record = db.query(PersonalizationProfile).filter(PersonalizationProfile.course_id == course_id).first()
    personalization_profile = profile_record.profile if profile_record else {}
    
    initial_state = {
        "course_id": course_id,
        "syllabus_text": raw_text,
        "curriculum_map": {},
        "learning_outcomes": [],
        "curriculum_plan": {},
        "slide_deck": [],
        "instructor_notes": [],
        "assessment_bank": [],
        "bloom_report": {},
        "readiness_score": {},
        "industry_gap_report": {},
        "personalization_profile": personalization_profile,
        "logs": ["Initiating personalized multi-agent regeneration workflow..."],
        "current_agent": "Curriculum Intelligence Agent",
        "pipeline_telemetry": []
    }
    
    final_state = compiled_graph.invoke(initial_state)
    
    error_info = final_state.get("error_info")
    save_workflow_outputs(db, course_id, final_state)
    
    if error_info:
        return {
            "status": "partial_generation",
            "failed_agent": error_info.get("failed_agent"),
            "error_type": error_info.get("error_type"),
            "successful_agents": error_info.get("successful_agents", []),
            "retry_recommended": error_info.get("retry_recommended", True),
            "logs": final_state["logs"],
            "pipeline_telemetry": final_state.get("pipeline_telemetry", [])
        }
        
    return {
        "status": "Success",
        "message": "Syllabus processed and educational package generated successfully.",
        "course_id": course_id,
        "logs": final_state["logs"],
        "pipeline_telemetry": final_state.get("pipeline_telemetry", [])
    }

@router.get("/{course_id}/traceability")
def get_course_traceability(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify course ownership
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    outcomes = db.query(LearningOutcome).filter(LearningOutcome.course_id == course_id).all()
    slides = db.query(GeneratedSlide).filter(GeneratedSlide.course_id == course_id).order_by(GeneratedSlide.slide_index).all()
    notes = db.query(InstructorNote).filter(InstructorNote.course_id == course_id).order_by(InstructorNote.slide_index).all()
    assessments = db.query(Assessment).filter(Assessment.course_id == course_id).all()
    
    notes_by_index = {n.slide_index: n for n in notes}
    
    stop_words = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", "of", "about", 
        "against", "across", "recall", "explain", "apply", "analyze", "evaluate", "design", "create", 
        "basic", "core", "techniques", "models", "understands", "comprehends", "methods"
    }
    
    traceability_report = []
    
    for outcome in outcomes:
        outcome_words = [
            w.strip(",.()\"':;").lower() 
            for w in outcome.outcome_text.split() 
            if w.strip(",.()\"':;").lower() not in stop_words and len(w.strip(",.()\"':;")) > 2
        ]
        
        # Scored matching slides
        scored_slides = []
        for s in slides:
            slide_text = (s.title + " " + " ".join(s.content)).lower()
            score = sum(1 for w in outcome_words if w in slide_text)
            if score > 0:
                scored_slides.append((s, score))
                
        # Sort by match score descending, then by slide index ascending
        scored_slides.sort(key=lambda x: (-x[1], x[0].slide_index))
        related_slides = [s for s, score in scored_slides[:3]]
        
        related_slides_data = [
            {"slide_index": s.slide_index, "title": s.title}
            for s in related_slides
        ]
        
        related_notes_data = []
        for s in related_slides:
            n = notes_by_index.get(s.slide_index)
            if n:
                related_notes_data.append({
                    "slide_index": n.slide_index,
                    "talking_points_count": len(n.talking_points) if n.talking_points else 0
                })
                
        related_assessments = [
            a for a in assessments if a.learning_outcome_id == outcome.id
        ]
        
        related_assessments_data = [
            {
                "id": a.id,
                "question_text": a.question_text,
                "bloom_level": a.bloom_level,
                "question_type": a.question_type,
                "correct_answer": a.correct_answer,
                "options": a.options
            }
            for a in related_assessments
        ]
        
        # Calculate coverage score
        slides_part = min(len(related_slides_data), 3) / 3.0 * 50.0
        assessments_part = min(len(related_assessments_data), 2) / 2.0 * 50.0
        coverage = int(slides_part + assessments_part)
        
        traceability_report.append({
            "id": outcome.id,
            "outcome_text": outcome.outcome_text,
            "bloom_level": outcome.bloom_level,
            "related_slides": related_slides_data,
            "related_notes": related_notes_data,
            "related_assessments": related_assessments_data,
            "coverage_percentage": coverage
        })
        
    return traceability_report
