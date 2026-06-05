import os
import shutil
from typing import List, Optional, Any
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

@router.post("/")
def create_course(payload: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
            "industry_gap_report": analysis.industry_gap_report if analysis else None
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

@router.post("/{course_id}/analyze")
def analyze_syllabus(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
        "current_agent": "Curriculum Analysis Agent"
    }
    
    # Invoke State Graph
    final_state = compiled_graph.invoke(initial_state)
    
    # Clean previous generated course details to ensure clean overwrite
    db.query(CurriculumAnalysis).filter(CurriculumAnalysis.course_id == course_id).delete()
    db.query(LearningOutcome).filter(LearningOutcome.course_id == course_id).delete()
    db.query(GeneratedSlide).filter(GeneratedSlide.course_id == course_id).delete()
    db.query(InstructorNote).filter(InstructorNote.course_id == course_id).delete()
    db.query(Assessment).filter(Assessment.course_id == course_id).delete()
    db.query(ReadinessScore).filter(ReadinessScore.course_id == course_id).delete()
    db.commit()
    
    # 3. SAVE WORKFLOW OUTPUTS TO DATABASE TABLES
    
    # A. Curriculum Analysis
    analysis = CurriculumAnalysis(
        course_id=course_id,
        curriculum_map=final_state["curriculum_map"],
        gap_analysis=final_state["bloom_report"].get("recommendation", "Review learning modules completeness."),
        industry_gap_report=final_state["industry_gap_report"]
    )
    db.add(analysis)
    
    # B. Learning Outcomes
    outcome_map = {} # Maps mock ID or indexes to actual DB items for assessment relational binding
    for item in final_state["learning_outcomes"]:
        outcome = LearningOutcome(
            course_id=course_id,
            outcome_text=item["text"],
            bloom_level=item["bloom_level"]
        )
        db.add(outcome)
        db.commit()
        outcome_map[item.get("id")] = outcome.id
        
    # C. Slides
    for slide_item in final_state["slide_deck"]:
        slide = GeneratedSlide(
            course_id=course_id,
            slide_index=slide_item["slide_index"],
            title=slide_item["title"],
            content=slide_item["content"],
            suggested_visuals=slide_item.get("suggested_visuals", "")
        )
        db.add(slide)
        
    # D. Speaker Notes
    for note_item in final_state["instructor_notes"]:
        note = InstructorNote(
            course_id=course_id,
            slide_index=note_item["slide_index"],
            talking_points=note_item["talking_points"],
            teaching_tips=note_item.get("teaching_tips", ""),
            examples=note_item.get("examples", [])
        )
        db.add(note)
        
    # E. Assessments
    for q_item in final_state["assessment_bank"]:
        # Map back to newly created outcome ID in SQLite/Postgres
        mapped_outcome_id = outcome_map.get(q_item.get("learning_outcome_id"))
        
        assessment = Assessment(
            course_id=course_id,
            learning_outcome_id=mapped_outcome_id,
            question_text=q_item["question_text"],
            question_type=q_item["question_type"],
            options=q_item.get("options"),
            correct_answer=q_item.get("correct_answer"),
            bloom_level=q_item["bloom_level"]
        )
        db.add(assessment)
        
    # F. Readiness Score
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
    
    return {
        "status": "Success",
        "message": "Syllabus processed and educational package generated successfully.",
        "course_id": course_id,
        "logs": final_state["logs"]
    }

@router.post("/{course_id}/regenerate")
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
        "current_agent": "Curriculum Analysis Agent"
    }
    
    final_state = compiled_graph.invoke(initial_state)
    
    db.query(CurriculumAnalysis).filter(CurriculumAnalysis.course_id == course_id).delete()
    db.query(LearningOutcome).filter(LearningOutcome.course_id == course_id).delete()
    db.query(GeneratedSlide).filter(GeneratedSlide.course_id == course_id).delete()
    db.query(InstructorNote).filter(InstructorNote.course_id == course_id).delete()
    db.query(Assessment).filter(Assessment.course_id == course_id).delete()
    db.query(ReadinessScore).filter(ReadinessScore.course_id == course_id).delete()
    db.commit()
    
    analysis = CurriculumAnalysis(
        course_id=course_id,
        curriculum_map=final_state["curriculum_map"],
        gap_analysis=final_state["bloom_report"].get("recommendation", "Review learning modules completeness."),
        industry_gap_report=final_state["industry_gap_report"]
    )
    db.add(analysis)
    
    outcome_map = {}
    for item in final_state["learning_outcomes"]:
        outcome = LearningOutcome(
            course_id=course_id,
            outcome_text=item["text"],
            bloom_level=item["bloom_level"]
        )
        db.add(outcome)
        db.commit()
        outcome_map[item.get("id")] = outcome.id
        
    for slide_item in final_state["slide_deck"]:
        slide = GeneratedSlide(
            course_id=course_id,
            slide_index=slide_item["slide_index"],
            title=slide_item["title"],
            content=slide_item["content"],
            suggested_visuals=slide_item.get("suggested_visuals", "")
        )
        db.add(slide)
        
    for note_item in final_state["instructor_notes"]:
        note = InstructorNote(
            course_id=course_id,
            slide_index=note_item["slide_index"],
            talking_points=note_item["talking_points"],
            teaching_tips=note_item.get("teaching_tips", ""),
            examples=note_item.get("examples", [])
        )
        db.add(note)
        
    for q_item in final_state["assessment_bank"]:
        mapped_outcome_id = outcome_map.get(q_item.get("learning_outcome_id"))
        assessment = Assessment(
            course_id=course_id,
            learning_outcome_id=mapped_outcome_id,
            question_text=q_item["question_text"],
            question_type=q_item["question_type"],
            options=q_item.get("options"),
            correct_answer=q_item.get("correct_answer"),
            bloom_level=q_item["bloom_level"]
        )
        db.add(assessment)
        
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
    
    return {
        "status": "Success",
        "message": "Syllabus processed and educational package generated successfully.",
        "course_id": course_id,
        "logs": final_state["logs"]
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
