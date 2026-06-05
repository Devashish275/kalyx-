import os
import csv
import io
import json
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models import User, Course, GeneratedSlide, InstructorNote, Assessment, PptExport
from app.services.exporter import generate_pptx_deck, generate_pdf_package

router = APIRouter(prefix="/export", tags=["Exports"])

def get_interactive_quiz_template(course_title: str, course_desc: str, questions_json: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Quiz: {course_title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Outfit', sans-serif;
            background: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%);
            min-height: 100vh;
            color: #f8fafc;
        }}
        .glass-panel {{
            background: rgba(15, 23, 42, 0.65);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}
        .pulse-light {{
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
            animation: pulse 3s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ box-shadow: 0 0 15px rgba(56, 189, 248, 0.2); }}
            50% {{ box-shadow: 0 0 25px rgba(56, 189, 248, 0.4); }}
        }}
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: rgba(15, 23, 42, 0.2);
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
    </style>
</head>
<body class="flex flex-col items-center justify-center p-4 md:p-8 min-h-screen">

    <!-- MAIN APP CONTAINER -->
    <div class="w-full max-w-3xl flex flex-col gap-6">
        
        <!-- HEADER LOGO / TITLE -->
        <div class="flex items-center justify-between px-2">
            <div class="flex items-center gap-2">
                <span class="p-1.5 rounded-lg bg-gradient-to-tr from-sky-500 to-indigo-500 text-white font-black text-sm tracking-widest shadow-md">K</span>
                <span class="text-sm font-black text-white tracking-widest">KALYX <span class="text-sky-400 font-medium">ASSESSMENT</span></span>
            </div>
            <div class="text-[10px] text-slate-500 tracking-wider uppercase font-mono bg-slate-900 px-2.5 py-1 rounded-full border border-slate-800">
                Self-Hosted Test
            </div>
        </div>

        <!-- 1. WELCOME SCREEN -->
        <div id="welcome-screen" class="glass-panel p-8 md:p-12 rounded-3xl flex flex-col items-center text-center gap-6 animate-fade-in">
            <div class="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shadow-lg">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.62 48.62 0 0112 20.9c2.79 0 5.422-.94 7.524-2.535.214-1.61.3-3.24.292-4.878m-15.556-3.34h15.556m-15.556 0a48.188 48.188 0 011.87-7.758A48.62 48.62 0 0112 3c1.765 0 3.443.345 4.978.975a48.188 48.188 0 011.87 7.758m-15.556-.001a42.947 42.947 0 015.008-.387m10.548.387a42.947 42.947 0 00-5.008-.387m0 0a89.29 89.29 0 00-5.008.387m5.008-.387h.01"></path>
                </svg>
            </div>
            
            <div>
                <h1 class="text-2xl md:text-3xl font-black text-white tracking-tight leading-tight">{course_title}</h1>
                <p class="text-slate-400 text-xs md:text-sm mt-3 max-w-lg leading-relaxed">{course_desc}</p>
            </div>

            <div class="grid grid-cols-2 gap-4 w-full max-w-md my-4">
                <div class="bg-slate-950/55 border border-slate-900 p-4 rounded-2xl flex flex-col items-center">
                    <span class="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Total Questions</span>
                    <span id="welcome-q-count" class="text-xl font-black text-white mt-1">0</span>
                </div>
                <div class="bg-slate-950/55 border border-slate-900 p-4 rounded-2xl flex flex-col items-center">
                    <span class="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Estimated Time</span>
                    <span id="welcome-time" class="text-xl font-black text-white mt-1">10 min</span>
                </div>
            </div>

            <button onclick="startQuiz()" class="w-full max-w-sm py-4 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white rounded-2xl text-sm font-bold shadow-lg shadow-indigo-500/10 hover:shadow-indigo-500/20 active:scale-[0.98] transition-all pulse-light">
                Begin Challenge
            </button>
        </div>

        <!-- 2. QUIZ SCREEN (HIDDEN BY DEFAULT) -->
        <div id="quiz-screen" class="hidden glass-panel p-6 md:p-8 rounded-3xl flex flex-col gap-6">
            
            <!-- Progress & Stats Bar -->
            <div class="flex justify-between items-center text-xs text-slate-400">
                <span class="font-mono" id="quiz-progress-text">Question 1 of 10</span>
                <span class="px-2.5 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-black tracking-widest text-[9px]" id="bloom-badge">
                    REMEMBERING
                </span>
            </div>

            <!-- Progress Bar -->
            <div class="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                <div id="quiz-progress-bar" class="bg-gradient-to-r from-sky-400 to-indigo-500 h-full rounded-full transition-all duration-300" style="width: 10%;"></div>
            </div>

            <!-- Question Text -->
            <h2 id="question-text" class="text-base md:text-lg font-black text-white leading-relaxed tracking-tight min-h-[50px]">
                Loading question...
            </h2>

            <!-- Options Grid -->
            <div id="options-container" class="grid grid-cols-1 gap-3 my-2">
                <!-- Javascript will inject options here -->
            </div>

            <!-- Navigation Buttons -->
            <div class="flex justify-between items-center pt-4 border-t border-white/5">
                <button onclick="prevQuestion()" id="prev-btn" class="px-5 py-2.5 bg-slate-950 border border-slate-900 hover:border-slate-800 text-xs font-bold text-slate-400 hover:text-white rounded-xl active:scale-95 transition-all">
                    Back
                </button>
                
                <button onclick="nextOrSubmit()" id="next-btn" class="px-6 py-2.5 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-xs font-bold text-white rounded-xl active:scale-95 transition-all shadow-md">
                    Next Question
                </button>
            </div>
        </div>

        <!-- 3. RESULTS SCREEN (HIDDEN BY DEFAULT) -->
        <div id="result-screen" class="hidden flex flex-col gap-6">
            
            <!-- Result Stats Card -->
            <div class="glass-panel p-8 rounded-3xl flex flex-col md:flex-row items-center justify-around gap-8 text-center md:text-left">
                
                <!-- Circular Chart -->
                <div class="relative flex items-center justify-center">
                    <svg class="w-36 h-36 transform -rotate-90">
                        <circle cx="72" cy="72" r="60" stroke="rgba(255,255,255,0.03)" stroke-width="12" fill="transparent" />
                        <circle id="progress-circle" cx="72" cy="72" r="60" stroke="url(#result-gradient)" stroke-dasharray="376.8" stroke-dashoffset="376.8" stroke-width="12" stroke-linecap="round" fill="transparent" class="transition-all duration-1000 ease-out" />
                        <defs>
                            <linearGradient id="result-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#38bdf8" />
                                <stop offset="100%" stop-color="#6366f1" />
                            </linearGradient>
                        </defs>
                    </svg>
                    <span id="percentage-text" class="absolute text-3xl font-black text-white">0%</span>
                </div>

                <div class="flex flex-col gap-2 max-w-sm">
                    <span class="text-[10px] text-slate-500 font-bold block uppercase tracking-wider">Assessment Outcome</span>
                    <h2 id="rating-title" class="text-2xl font-black text-white">Elite Mastery!</h2>
                    <p id="rating-desc" class="text-xs text-slate-400 leading-relaxed mt-1">Excellent job! You have fully understood the primary building blocks of this curriculum.</p>
                    <div class="mt-4 flex items-center gap-6">
                        <div>
                            <span class="text-[10px] text-slate-500 font-bold block uppercase tracking-wider">SCORE</span>
                            <span id="score-fraction" class="text-lg font-black text-white mt-0.5">0 / 0</span>
                        </div>
                        <button onclick="location.reload()" class="px-4 py-2 bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/20 text-xs font-bold text-indigo-400 rounded-xl transition-all">
                            Retake Challenge
                        </button>
                    </div>
                </div>
            </div>

            <!-- Review Section Title -->
            <div class="px-1 flex justify-between items-center">
                <h3 class="text-sm font-black text-white uppercase tracking-wider">Answer Review Board</h3>
                <span class="text-xs text-slate-500 font-medium">Auto-Graded locally</span>
            </div>

            <!-- Review Cards List -->
            <div id="review-list" class="flex flex-col gap-4">
                <!-- Javascript will inject review cards -->
            </div>
            
        </div>

    </div>

    <!-- CORE INTERACTIVE JS -->
    <script>
        const questions = {questions_json};
        let currentIdx = 0;
        const userAnswers = {{}}; // key: index, value: option index

        // Setup Welcome details
        document.getElementById('welcome-q-count').innerText = questions.length;
        document.getElementById('welcome-time').innerText = Math.max(5, Math.round(questions.length * 0.75)) + " min";

        function startQuiz() {{
            document.getElementById('welcome-screen').classList.add('hidden');
            document.getElementById('quiz-screen').classList.remove('hidden');
            renderQuestion();
        }}

        function renderQuestion() {{
            if (!questions.length) return;
            const q = questions[currentIdx];
            
            // Text values
            document.getElementById('quiz-progress-text').innerText = `Question ${{currentIdx + 1}} of ${{questions.length}}`;
            document.getElementById('question-text').innerText = q.question_text;
            
            // Bloom badge
            const badge = document.getElementById('bloom-badge');
            badge.innerText = q.bloom_level ? q.bloom_level.toUpperCase() : "GENERAL";
            
            // Progress bar width
            const percent = ((currentIdx + 1) / questions.length) * 100;
            document.getElementById('quiz-progress-bar').style.width = percent + "%";
            
            // Load Options
            const container = document.getElementById('options-container');
            container.innerHTML = '';
            
            if (q.options && q.options.length) {{
                q.options.forEach((opt, idx) => {{
                    const isSelected = userAnswers[currentIdx] === idx;
                    const card = document.createElement('div');
                    
                    const charCode = String.fromCharCode(65 + idx); // A, B, C, D
                    
                    card.onclick = () => selectOption(idx);
                    
                    // Style depends on select status
                    let style = "bg-slate-950/65 border-slate-900 text-slate-300 hover:border-slate-800 hover:text-white";
                    if (isSelected) {{
                        style = "bg-sky-500/10 border-sky-500 text-sky-200 shadow-md shadow-sky-500/5";
                    }}
                    
                    card.className = `flex items-center gap-4 px-5 py-4 border rounded-2xl cursor-pointer select-none transition-all duration-200 ${{style}}`;
                    card.innerHTML = `
                        <span class="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center text-xs font-black ${{isSelected ? "bg-sky-500 text-slate-950" : "bg-slate-900 text-slate-500"}}">
                            ${{charCode}}
                        </span>
                        <span class="text-xs leading-relaxed font-semibold">${{opt}}</span>
                    `;
                    container.appendChild(card);
                }});
            }}
            
            // Nav states
            document.getElementById('prev-btn').disabled = currentIdx === 0;
            document.getElementById('prev-btn').style.opacity = currentIdx === 0 ? '0.4' : '1';
            
            const nextBtn = document.getElementById('next-btn');
            if (currentIdx === questions.length - 1) {{
                nextBtn.innerText = "Submit Assessment";
                nextBtn.className = "px-6 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-xs font-bold text-white rounded-xl active:scale-95 transition-all shadow-md shadow-emerald-500/10 cursor-pointer";
            }} else {{
                nextBtn.innerText = "Next Question";
                nextBtn.className = "px-6 py-2.5 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-xs font-bold text-white rounded-xl active:scale-95 transition-all shadow-md shadow-indigo-500/10 cursor-pointer";
            }}
        }}

        function selectOption(optIdx) {{
            userAnswers[currentIdx] = optIdx;
            renderQuestion();
        }}

        function prevQuestion() {{
            if (currentIdx > 0) {{
                currentIdx--;
                renderQuestion();
            }}
        }}

        function nextOrSubmit() {{
            if (currentIdx === questions.length - 1) {{
                // Submit!
                submitQuiz();
            }} else {{
                currentIdx++;
                renderQuestion();
            }}
        }}

        // Allow keyboard triggers
        window.addEventListener('keydown', (e) => {{
            if (document.getElementById('quiz-screen').classList.contains('hidden')) return;
            
            const key = e.key.toLowerCase();
            if (key === 'a' || key === '1') selectOption(0);
            if (key === 'b' || key === '2') selectOption(1);
            if (key === 'c' || key === '3') selectOption(2);
            if (key === 'd' || key === '4') selectOption(3);
            
            if (key === 'enter') nextOrSubmit();
            if (key === 'arrowleft' && currentIdx > 0) prevQuestion();
        }});

        function submitQuiz() {{
            document.getElementById('quiz-screen').classList.add('hidden');
            document.getElementById('result-screen').classList.remove('hidden');
            calculateResults();
        }}

        function calculateResults() {{
            let score = 0;
            questions.forEach((q, idx) => {{
                const correctVal = q.correct_answer ? q.correct_answer.trim().toLowerCase() : "";
                const selectedOptIdx = userAnswers[idx];
                
                if (selectedOptIdx !== undefined && q.options[selectedOptIdx]) {{
                    const selectedVal = q.options[selectedOptIdx].trim().toLowerCase();
                    if (selectedVal === correctVal || correctVal.includes(selectedVal) || selectedVal.includes(correctVal)) {{
                        score++;
                    }}
                }}
            }});

            const percent = Math.round((score / questions.length) * 100);
            document.getElementById('percentage-text').innerText = percent + "%";
            document.getElementById('score-fraction').innerText = score + " / " + questions.length;
            
            // Draw SVG circle progress
            const circle = document.getElementById('progress-circle');
            const radius = 60;
            const circumference = 2 * Math.PI * radius;
            circle.style.strokeDasharray = circumference;
            const offset = circumference - (percent / 100) * circumference;
            circle.style.strokeDashoffset = offset;
            
            // Rating titles
            let rating = "Keep Studying!";
            let ratingDesc = "Review the course materials and try again to improve your grasp on the topics.";
            let ratingColor = "text-rose-400";
            if (percent >= 90) {{
                rating = "Elite Mastery!";
                ratingDesc = "Outstanding performance! You have fully mastered the core concepts of this course.";
                ratingColor = "text-emerald-400";
            }} else if (percent >= 70) {{
                rating = "Competent Scholar!";
                ratingDesc = "Great job! You have a solid understanding of most topics covered.";
                ratingColor = "text-sky-400";
            }} else if (percent >= 50) {{
                rating = "Developing Thinker!";
                ratingDesc = "Good effort, but there is still room for improvement in some areas.";
                ratingColor = "text-amber-400";
            }}
            
            const ratingEl = document.getElementById('rating-title');
            ratingEl.innerText = rating;
            ratingEl.className = "text-2xl font-black mt-4 " + ratingColor;
            document.getElementById('rating-desc').innerText = ratingDesc;
            
            // Build Review Board
            const reviewList = document.getElementById('review-list');
            reviewList.innerHTML = '';
            questions.forEach((q, idx) => {{
                const selectedOptIdx = userAnswers[idx];
                const correctVal = q.correct_answer ? q.correct_answer.trim().toLowerCase() : "";
                let isCorrect = false;
                let selectedText = "No answer selected";
                
                if (selectedOptIdx !== undefined && q.options[selectedOptIdx]) {{
                    selectedText = q.options[selectedOptIdx];
                    const selectedVal = selectedText.trim().toLowerCase();
                    if (selectedVal === correctVal || correctVal.includes(selectedVal) || selectedVal.includes(correctVal)) {{
                        isCorrect = true;
                    }}
                }}
                
                const card = document.createElement('div');
                card.className = "glass-panel p-6 rounded-2xl border " + (isCorrect ? "border-emerald-500/20 bg-emerald-950/5" : "border-rose-500/20 bg-rose-950/5") + " flex flex-col gap-3";
                
                let optionsHtml = '';
                q.options.forEach((opt, oIdx) => {{
                    let optStyle = "bg-slate-950/60 border border-slate-900/60 text-slate-400";
                    if (oIdx === selectedOptIdx) {{
                        optStyle = isCorrect ? "bg-emerald-500/10 border-emerald-500 text-emerald-300 font-bold" : "bg-rose-500/10 border-rose-500 text-rose-300 font-bold";
                    }} else {{
                        // Check if this option represents the correct answer
                        const optVal = opt.trim().toLowerCase();
                        if (correctVal && (optVal === correctVal || correctVal.includes(optVal) || optVal.includes(correctVal))) {{
                            optStyle = "bg-emerald-500/5 border-emerald-500/30 text-emerald-400/90";
                        }}
                    }}
                    optionsHtml += `<div class="px-4 py-2.5 rounded-xl text-xs ${{optStyle}}">${{opt}}</div>`;
                }});
                
                card.innerHTML = `
                    <div class="flex justify-between items-center text-[10px]">
                      <span class="px-2.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 font-mono font-bold">
                        QUESTION ${{idx + 1}}
                      </span>
                      <span class="px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-extrabold uppercase">
                        ${{q.bloom_level || "GENERAL"}}
                      </span>
                    </div>
                    <h4 class="text-sm font-bold text-white leading-relaxed mt-1">${{q.question_text}}</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-2 my-2">
                      ${{optionsHtml}}
                    </div>
                    <div class="flex items-center gap-2 mt-1">
                      <span class="text-xs font-bold ${{isCorrect ? "text-emerald-400" : "text-rose-400"}} flex items-center gap-1">
                        ${{isCorrect ? 
                          `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> Correct` : 
                          `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> Incorrect`
                        }}
                      </span>
                      <span class="text-xs text-slate-500">|</span>
                      <span class="text-xs text-slate-350 font-medium">Selected: ${{selectedText}}</span>
                      <span class="text-xs text-slate-500">|</span>
                      <span class="text-xs text-slate-350 font-medium">Solution: <strong class="text-emerald-400 font-bold">${{q.correct_answer}}</strong></span>
                    </div>
                `;
                reviewList.appendChild(card);
            }});
        }}
    </script>
</body>
</html>
"""

@router.get("/courses/{course_id}/pptx")
def export_course_pptx(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    slides = db.query(GeneratedSlide).filter(GeneratedSlide.course_id == course_id).order_by(GeneratedSlide.slide_index).all()
    notes = db.query(InstructorNote).filter(InstructorNote.course_id == course_id).order_by(InstructorNote.slide_index).all()
    
    if not slides:
        raise HTTPException(status_code=400, detail="No slides generated yet for this course. Please analyze a syllabus first.")
        
    slides_data = [
        {
            "slide_index": s.slide_index,
            "title": s.title,
            "content": s.content,
            "suggested_visuals": s.suggested_visuals
        } for s in slides
    ]
    
    notes_data = [
        {
            "slide_index": n.slide_index,
            "talking_points": n.talking_points,
            "teaching_tips": n.teaching_tips,
            "examples": n.examples
        } for n in notes
    ]
    
    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)
    file_name = f"Kalyx_Course_{course_id}.pptx"
    file_path = os.path.join(export_dir, file_name)
    
    try:
        generate_pptx_deck(slides_data, notes_data, file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PPTX deck: {e}")
        
    ppt_log = PptExport(
        course_id=course_id,
        file_name=file_name,
        file_path=file_path
    )
    db.add(ppt_log)
    db.commit()
    
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

@router.get("/courses/{course_id}/pdf")
def export_course_pdf(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    slides = db.query(GeneratedSlide).filter(GeneratedSlide.course_id == course_id).order_by(GeneratedSlide.slide_index).all()
    notes = db.query(InstructorNote).filter(InstructorNote.course_id == course_id).order_by(InstructorNote.slide_index).all()
    assessments = db.query(Assessment).filter(Assessment.course_id == course_id).all()
    
    if not slides:
        raise HTTPException(status_code=400, detail="No slides generated yet for this course. Please analyze a syllabus first.")
        
    slides_data = [
        {
            "slide_index": s.slide_index,
            "title": s.title,
            "content": s.content,
            "suggested_visuals": s.suggested_visuals
        } for s in slides
    ]
    
    notes_data = [
        {
            "slide_index": n.slide_index,
            "talking_points": n.talking_points,
            "teaching_tips": n.teaching_tips,
            "examples": n.examples
        } for n in notes
    ]
    
    assessments_data = [
        {
            "question_text": a.question_text,
            "question_type": a.question_type,
            "options": a.options,
            "correct_answer": a.correct_answer,
            "bloom_level": a.bloom_level
        } for a in assessments
    ]
    
    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)
    file_name = f"Kalyx_Course_{course_id}.pdf"
    file_path = os.path.join(export_dir, file_name)
    
    try:
        generate_pdf_package(course.title, course.description, slides_data, notes_data, assessments_data, file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF package: {e}")
        
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/pdf"
    )

@router.get("/courses/{course_id}/kahoot")
def export_course_kahoot(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    assessments = db.query(Assessment).filter(Assessment.course_id == course_id).all()
    # Filter MCQ questions (those marked as MCQ or having non-empty options)
    mcqs = [a for a in assessments if a.question_type.upper() == "MCQ" or (a.options and len(a.options) > 0)]
    
    if not mcqs:
        raise HTTPException(status_code=400, detail="No MCQ assessments found for this course.")
        
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Kahoot bulk import spreadsheet format headers:
    # Question,Answer Option 1,Answer Option 2,Answer Option 3,Answer Option 4,Time Limit (seconds),Correct Answer(s)
    writer.writerow([
        "Question", 
        "Answer Option 1", 
        "Answer Option 2", 
        "Answer Option 3", 
        "Answer Option 4", 
        "Time Limit (seconds)", 
        "Correct Answer(s)"
    ])
    
    for a in mcqs:
        question_text = a.question_text
        options = a.options or []
        correct_answer = a.correct_answer or ""
        
        # Max lengths: Question 120 chars, Option 75 chars (warning limit, but we preserve as much text as possible)
        # Ensure we have up to 4 options
        opt1 = options[0] if len(options) > 0 else ""
        opt2 = options[1] if len(options) > 1 else ""
        opt3 = options[2] if len(options) > 2 else ""
        opt4 = options[3] if len(options) > 3 else ""
        
        # Find 1-based index/indices of correct answer
        correct_indices = []
        if correct_answer:
            cleaned_options = [str(opt).strip().lower() for opt in options]
            clean_correct = str(correct_answer).strip().lower()
            
            # Exact Match
            matched = False
            for idx, cleaned_opt in enumerate(cleaned_options):
                if cleaned_opt == clean_correct:
                    correct_indices.append(str(idx + 1))
                    matched = True
                    break
            
            # Substring Match
            if not matched:
                for idx, cleaned_opt in enumerate(cleaned_options):
                    if cleaned_opt in clean_correct or clean_correct in cleaned_opt:
                        correct_indices.append(str(idx + 1))
                        matched = True
                        break
            
            # Digit Match
            if not matched:
                digits = [c for c in clean_correct if c.isdigit()]
                for d in digits:
                    val = int(d)
                    if 1 <= val <= len(options):
                        correct_indices.append(str(val))
                        matched = True
        
        # Fallback to index 1 if not matched
        if not correct_indices:
            correct_indices = ["1"]
            
        correct_str = ",".join(correct_indices)
        time_limit = 30
        
        writer.writerow([
            question_text,
            opt1,
            opt2,
            opt3,
            opt4,
            time_limit,
            correct_str
        ])
        
    csv_data = output.getvalue()
    output.close()
    
    headers = {
        "Content-Disposition": f"attachment; filename=Kahoot_Import_Course_{course_id}.csv"
    }
    return Response(content=csv_data, media_type="text/csv", headers=headers)

@router.get("/courses/{course_id}/interactive-quiz")
def export_course_interactive_quiz(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    assessments = db.query(Assessment).filter(Assessment.course_id == course_id).all()
    mcqs = [a for a in assessments if a.question_type.upper() == "MCQ" or (a.options and len(a.options) > 0)]
    
    if not mcqs:
        raise HTTPException(status_code=400, detail="No MCQ assessments found for this course.")
        
    questions_data = []
    for a in mcqs:
        questions_data.append({
            "id": a.id,
            "question_text": a.question_text,
            "bloom_level": a.bloom_level,
            "options": a.options or [],
            "correct_answer": a.correct_answer or ""
        })
        
    questions_json = json.dumps(questions_data)
    course_title_esc = course.title.replace('"', '\\"')
    course_desc_esc = course.description.replace('"', '\\"').replace('\n', ' ') if course.description else ""
    
    html_content = get_interactive_quiz_template(course_title_esc, course_desc_esc, questions_json)
    
    headers = {
        "Content-Disposition": f"attachment; filename=Interactive_Quiz_Course_{course_id}.html"
    }
    return Response(content=html_content, media_type="text/html", headers=headers)

