from typing import TypedDict, List, Dict, Any, Optional

class SharedState(TypedDict):
    course_id: Optional[int]
    syllabus_text: str
    curriculum_map: Dict[str, Any]  # modules, topics, subtopics
    learning_outcomes: List[Dict[str, Any]]  # lists of outcomes with bloom levels
    curriculum_plan: Dict[str, Any]  # sequences, roadmap
    slide_deck: List[Dict[str, Any]]  # generated slide screens
    instructor_notes: List[Dict[str, Any]]  # generated slide notes
    assessment_bank: List[Dict[str, Any]]  # MCQs, Short Answers, viva questions
    bloom_report: Dict[str, Any]  # percentage of Bloom taxonomy coverage
    readiness_score: Dict[str, Any]  # 100-point curriculum score breakdown
    industry_gap_report: Dict[str, Any]  # modernization analysis
    personalization_profile: Dict[str, Any]  # style/tone instructions
    logs: List[str]  # Real-time state logging for agent steps
    current_agent: str  # active agent reporting name
    pipeline_telemetry: List[Dict[str, Any]]  # Real agent execution start/end/duration metrics
