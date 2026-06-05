from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.routers.auth import get_current_user
from app.models import (
    User, Course, GeneratedSlide, InstructorNote, Assessment, PersonalizationProfile
)

router = APIRouter(prefix="/studio", tags=["AI Studio"])

# Pydantic schemas for edits
class SlideUpdatePayload(BaseModel):
    title: str
    content: List[str]
    suggested_visuals: Optional[str] = None

class NoteUpdatePayload(BaseModel):
    talking_points: List[str]
    teaching_tips: Optional[str] = None
    examples: Optional[List[str]] = None

class AssessmentUpdatePayload(BaseModel):
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    bloom_level: str

class PersonalizationPayload(BaseModel):
    profile: Dict[str, Any]

@router.put("/slides/{slide_id}")
def update_slide(
    slide_id: int,
    payload: SlideUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    slide = db.query(GeneratedSlide).filter(GeneratedSlide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")
        
    # Verify course ownership
    course = db.query(Course).filter(Course.id == slide.course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=403, detail="Not authorized to edit this course content")
        
    slide.title = payload.title
    slide.content = payload.content
    slide.suggested_visuals = payload.suggested_visuals
    
    db.commit()
    return {"status": "Success", "message": f"Slide {slide_id} updated successfully", "slide": {
        "id": slide.id, "title": slide.title, "content": slide.content, "suggested_visuals": slide.suggested_visuals
    }}

@router.put("/notes/{note_id}")
def update_note(
    note_id: int,
    payload: NoteUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(InstructorNote).filter(InstructorNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Instructor note not found")
        
    course = db.query(Course).filter(Course.id == note.course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=403, detail="Not authorized to edit this course content")
        
    note.talking_points = payload.talking_points
    note.teaching_tips = payload.teaching_tips
    note.examples = payload.examples
    
    db.commit()
    return {"status": "Success", "message": f"Note {note_id} updated successfully", "note": {
        "id": note.id, "talking_points": note.talking_points, "teaching_tips": note.teaching_tips, "examples": note.examples
    }}

@router.put("/assessments/{assessment_id}")
def update_assessment(
    assessment_id: int,
    payload: AssessmentUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    course = db.query(Course).filter(Course.id == assessment.course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=403, detail="Not authorized to edit this course content")
        
    assessment.question_text = payload.question_text
    assessment.question_type = payload.question_type
    assessment.options = payload.options
    assessment.correct_answer = payload.correct_answer
    assessment.bloom_level = payload.bloom_level
    
    db.commit()
    return {"status": "Success", "message": f"Assessment {assessment_id} updated successfully"}

@router.post("/courses/{course_id}/personalize")
def configure_personalization(
    course_id: int,
    payload: PersonalizationPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    profile = db.query(PersonalizationProfile).filter(PersonalizationProfile.course_id == course_id).first()
    if not profile:
        profile = PersonalizationProfile(course_id=course_id, profile=payload.profile)
        db.add(profile)
    else:
        profile.profile = payload.profile
        
    db.commit()
    return {"status": "Success", "message": "Personalization profile configured successfully", "profile": profile.profile}
