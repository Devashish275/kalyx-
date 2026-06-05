import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime, JSON, Boolean, Table
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    courses = relationship("Course", back_populates="user", cascade="all, delete-orphan")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="courses")
    syllabi = relationship("Syllabus", back_populates="course", cascade="all, delete-orphan")
    curriculum_analyses = relationship("CurriculumAnalysis", back_populates="course", cascade="all, delete-orphan")
    learning_outcomes = relationship("LearningOutcome", back_populates="course", cascade="all, delete-orphan")
    slides = relationship("GeneratedSlide", back_populates="course", cascade="all, delete-orphan")
    notes = relationship("InstructorNote", back_populates="course", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="course", cascade="all, delete-orphan")
    readiness_scores = relationship("ReadinessScore", back_populates="course", cascade="all, delete-orphan")
    uploaded_documents = relationship("UploadedDocument", back_populates="course", cascade="all, delete-orphan")
    personalization = relationship("PersonalizationProfile", back_populates="course", uselist=False, cascade="all, delete-orphan")
    exports = relationship("PptExport", back_populates="course", cascade="all, delete-orphan")

class Syllabus(Base):
    __tablename__ = "syllabi"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    raw_text = Column(Text, nullable=False)
    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="syllabi")

class CurriculumAnalysis(Base):
    __tablename__ = "curriculum_analysis"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    curriculum_map = Column(JSON, nullable=True)  # Structure: Modules, topics, subtopics
    gap_analysis = Column(JSON, nullable=True)     # Detected internal content/topic gaps
    industry_gap_report = Column(JSON, nullable=True) # Modern trends comparison
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="curriculum_analyses")

class LearningOutcome(Base):
    __tablename__ = "learning_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    outcome_text = Column(Text, nullable=False)
    bloom_level = Column(String, nullable=False)  # Remembering, Understanding, Applying, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="learning_outcomes")
    assessments = relationship("Assessment", back_populates="learning_outcome")

class GeneratedSlide(Base):
    __tablename__ = "generated_slides"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    slide_index = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    content = Column(JSON, nullable=False)  # List of bullet points / section details
    suggested_visuals = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="slides")

class InstructorNote(Base):
    __tablename__ = "instructor_notes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    slide_index = Column(Integer, nullable=False)
    talking_points = Column(JSON, nullable=False)  # List of speaker notes
    teaching_tips = Column(Text, nullable=True)
    examples = Column(JSON, nullable=True)        # Clarifying examples
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="notes")

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    learning_outcome_id = Column(Integer, ForeignKey("learning_outcomes.id"), nullable=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False) # MCQ, Short Answer, Long Answer, Viva
    options = Column(JSON, nullable=True)         # JSON List of options if MCQ
    correct_answer = Column(Text, nullable=True)
    bloom_level = Column(String, nullable=False)   # Bloom taxonomy tier
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="assessments")
    learning_outcome = relationship("LearningOutcome", back_populates="assessments")

class ReadinessScore(Base):
    __tablename__ = "readiness_scores"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    score = Column(Float, nullable=False)
    completeness = Column(Float, nullable=False)
    outcome_coverage = Column(Float, nullable=False)
    assessment_quality = Column(Float, nullable=False)
    bloom_coverage = Column(Float, nullable=False)
    industry_relevance = Column(Float, nullable=False)
    breakdown = Column(JSON, nullable=True)  # Detailed comments & visual metrics
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="readiness_scores")

class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    document_type = Column(String, nullable=False) # RAG_SOURCE, SYLLABUS
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="uploaded_documents")
    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("uploaded_documents.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)  # Stored as a list of floats (supports pgvector mapping & SQLite fallback)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("UploadedDocument", back_populates="embeddings")

class PersonalizationProfile(Base):
    __tablename__ = "instructor_personalization"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    profile = Column(JSON, nullable=False)  # Tone, slide style preference, custom instructions
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="personalization")

class PptExport(Base):
    __tablename__ = "ppt_exports"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="exports")
