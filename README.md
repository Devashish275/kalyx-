# ✨ KALYX: Curriculum Intelligence Platform

KALYX is an , enterprise-grade multi-agent curriculum intelligence platform designed for modern educators, academic directors, and training organizations. By orchestrating a pipeline of **4 consolidated LangGraph agents** powered by **Google Gemini**, KALYX transforms a raw syllabus document (PDF/TXT) into a comprehensive, production-ready classroom package in minutes.

The platform automatically builds structured lesson outlines, slide content, instructor lecture scripts, question banks, cognitive audits, and modern industry gap analysis, exporting everything directly to premium PPTX slide decks, PDFs, Kahoot packages, and interactive quizzes.

---

## 📸 Platform Snapshots

### 1. Premium Educator Dashboard
![Kalyx Premium Educator Dashboard](assets/kalyx_dashboard_mockup.png)

### 2. Interactive AI Studio & Canvas Editor
![Kalyx Course Workspace & Studio](assets/course_dashboard.png)

### 3. Curriculum Readiness Breakdown (Explain Score)
![Curriculum Readiness Breakdown](assets/readiness_score.png)

### 4. Bloom's Taxonomy Cognitive Audit
![Bloom Taxonomy Quality Audit](assets/blooms_taxonomy_audit.png)

### 5. Multi-Tier Assessment & Quiz Bank
![Assessment Generator & Quiz Bank](assets/assessment_bank.png)

### 6. Silicon Valley Industry Gap Analyzer
![Modern Industry Gap Analyzer](assets/industry_gap_analyzer.png)

---

## 🚀 Key Features

### 1. Intelligent Multi-Agent Workflow (4-Agent Loop)
KALYX features a structured multi-agent state graph pipeline powered by **LangGraph** and **Google Gemini**:
1. **Curriculum Intelligence Agent**: Deconstructs raw syllabi, formulates measurable learning outcomes (LOs), and maps structured weekly lesson plans.
2. **Content Generation Agent**: Generates complete, detailed lecture slides and comprehensive instructor lecture scripts (including talking points, teaching tips, and real-world examples).
3. **Assessment Intelligence Agent**: Designs diagnostic MCQ assessment banks and performs a cognitive audit across all six tiers of Bloom's Revised Taxonomy.
4. **Curriculum Evaluation Agent**: Evaluates curriculum quality on a 100-point readiness scale and compiles active industry tech gap analyses.

### 2. Self-Healing Cognitive Loop
If the **Assessment Intelligence Agent** audits the average Bloom cognitive coverage below a **75% threshold**, the LangGraph orchestrator triggers a conditional edge that loops back to the *Curriculum Intelligence* stage. This enriches the syllabus content and updates outcomes dynamically before finalizing the package.

### 3. Learning Outcome Traceability
Educators can click on any extracted learning outcome inside the traceability dashboard to view exactly how it is covered across the generated course. The platform maps outcomes directly to:
* Relevant generated slides
* Instructor lecture scripts and talking points
* Target assessment questions
* Overall coverage completeness percentages

### 4. Interactive Studio Workspace
The workspace provides an interactive slide canvas, markdown speaker notes editor, and customizable quiz bank. Instructors can refine text, adjust teaching tips, customize slide layouts, and update visual suggestions on the fly with automatic database synchronization.

### 5. Premium Slide Exports (PPTX & PDF)
* **PowerPoint Deck**: Generates startup-grade dark-navy theme presentation slides (`#0a0f1e` dark theme, `#0ea5e9` cyan accents) with programmatically fetched relevant stock photos from LoremFlickr, terminal formatting for code snippets, and bound speaker notes.
* **FPDF2 PDF Package**: Generates classroom implementation booklets including custom cover pages, metadata profiles, section dividers, side-by-side illustrated slide panels, and quiz answer keys.

---

## 🛠️ Technical Architecture

```mermaid
graph TD
    %% Frontend Block
    subgraph Frontend [Next.js 15 SPA]
        FE_Landing[Landing Page]
        FE_Studio[Interactive AI Studio]
        FE_Trace[Traceability Dashboard]
        FE_Timeline[Execution Pipeline Panel]
    end

    %% Backend Block
    subgraph Backend [FastAPI Server]
        BE_Auth[JWT Auth Router]
        BE_Course[Course Manager Router]
        BE_Studio[Studio Mutator Router]
        BE_Export[Export Generator Router]
        BE_RAG[RAG Vector Index Builder]
    end

    %% Storage Block
    subgraph Storage [SQLite Database]
        DB_User[(users)]
        DB_Course[(courses & syllabi)]
        DB_Slides[(generated_slides)]
        DB_Notes[(instructor_notes)]
        DB_Embeds[(embeddings vector index)]
    end

    %% Orchestration Block
    subgraph Orchestration [LangGraph Orchestrator]
        AG_Graph[4-Agent State Graph]
        AG_Gemini[Gemini Flash]
    end

    %% Interconnections
    FE_Landing -->|API Requests| BE_Auth
    FE_Studio -->|API Requests| BE_Course
    FE_Studio -->|Mutations| BE_Studio
    FE_Trace -->|Fetch Data| BE_Course
    FE_Timeline -->|Log Traces| BE_Course
    
    BE_Auth --> DB_User
    BE_Course --> DB_Course
    BE_Studio --> DB_Slides
    BE_Studio --> DB_Notes
    BE_RAG --> DB_Embeds
    
    BE_Course -->|Orchestrate| AG_Graph
    AG_Graph -->|LLM Queries| AG_Gemini
```

---

## ⚡ Setup & Installation

### Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables. Create a `.env` file inside the `backend` folder:
   ```env
   DATABASE_URL=sqlite:///./kalyx.db
   JWT_SECRET_KEY=your-jwt-secret-key-change-this
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

5. Run the backend development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup (Next.js)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the frontend development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:3000` to access the KALYX platform.

---

## 🔒 Production Hardening & Security

* **Rate Limiting**: Sliding-window, dependency-free rate limiters protect sensitive routes:
  * `/api/auth/login` (10 req/min/IP)
  * `/api/auth/signup` (5 req/min/IP)
  * `/api/courses/` (20 req/min/user)
  * Syllabus uploads & analyze (5 req/min/user)
* **Payload Validation**: Strict checks on input files, course titles, description lengths, and PDF formats. Returns clean, structured JSON 422/429 validation outputs.
* **Local Fallbacks**: Local embedding vector indexing and mock agent fallbacks guarantee that the application compiles successfully even during offline sessions or Gemini API outages.

---

## 📄 License
This project is proprietary and confidential. Created as part of the KALYX Curriculum Intelligence Platform.
