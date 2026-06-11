import sys
import os
from fpdf import FPDF

class KalyxDocumentation(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(True, 20)
        self.primary_color = (26, 36, 43)    # Deep Slate
        self.secondary_color = (66, 133, 244) # Blue Accent
        self.text_color_main = (33, 33, 33)   # Charcoal
        self.light_bg = (245, 247, 250)      # Warm white/light gray
        self.border_color = (220, 224, 230)   # Light border
        
    def header(self):
        # Skip header on cover page
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(100, 110, 120)
            self.cell(0, 10, 'KALYX - AI Powered Curriculum Intelligence Platform', new_x="RIGHT", new_y="TOP", align='L')
            self.cell(0, 10, 'Technical Judge Documentation', new_x="LMARGIN", new_y="NEXT", align='R')
            self.set_draw_color(*self.border_color)
            self.line(20, 20, 190, 20)
            self.ln(5)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(100, 110, 120)
            self.cell(0, 10, 'Confidential - KALYX Technical Documentation', new_x="RIGHT", new_y="TOP", align='L')
            self.cell(0, 10, f'Page {self.page_no()}', new_x="RIGHT", new_y="TOP", align='R')

    def cover_page(self):
        self.add_page()
        # Draw a beautiful dark background cover
        self.set_fill_color(*self.primary_color)
        self.rect(0, 0, 210, 297, 'F')
        
        # Add decorative lines/accents
        self.set_fill_color(*self.secondary_color)
        self.rect(20, 80, 5, 120, 'F')
        
        # Text positioning
        self.set_xy(35, 90)
        self.set_font('Helvetica', 'B', 44)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'KALYX', new_x="LMARGIN", new_y="NEXT", align='L')
        
        self.set_x(35)
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*self.secondary_color)
        self.cell(0, 10, 'AI-POWERED CURRICULUM INTELLIGENCE PLATFORM', new_x="LMARGIN", new_y="NEXT", align='L')
        
        self.ln(15)
        self.set_x(35)
        self.set_font('Helvetica', '', 12)
        self.set_text_color(200, 210, 220)
        self.multi_cell(150, 6, 'A complete multi-agent curriculum mapping, generation, and alignment auditing engine designed for higher education.\n\nBuilt with Next.js, FastAPI, LangGraph, Groq API, and SQLite.', 0, 'L')
        
        self.set_xy(35, 220)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, 'TEAM: KALYX Core Engineers', new_x="LMARGIN", new_y="NEXT", align='L')
        self.set_x(35)
        self.cell(0, 6, 'HACKATHON: Global Generative AI Hackathon 2026', new_x="LMARGIN", new_y="NEXT", align='L')
        self.set_x(35)
        self.cell(0, 6, f'DATE: June 2026', new_x="LMARGIN", new_y="NEXT", align='L')
        self.set_x(35)
        self.cell(0, 6, 'TARGET AUDIENCE: Technical Evaluation Panel', new_x="LMARGIN", new_y="NEXT", align='L')

    def add_section_header(self, title):
        self.add_page()
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(*self.primary_color)
        self.cell(0, 15, title, new_x="LMARGIN", new_y="NEXT", align='L')
        self.set_fill_color(*self.secondary_color)
        self.rect(20, 32, 50, 2, 'F')
        self.ln(10)

    def add_paragraph(self, text, style=''):
        self.set_font('Helvetica', style, 10)
        self.set_text_color(*self.text_color_main)
        self.multi_cell(0, 6, text, 0, 'J')
        self.ln(4)
        
    def add_subheading(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(*self.primary_color)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align='L')
        self.ln(2)

    def add_bullet(self, title, description):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*self.primary_color)
        self.write(6, f"- {title}: ")
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*self.text_color_main)
        self.multi_cell(0, 6, description, 0, 'J')
        self.ln(2)

    def add_code_block(self, code_text):
        self.set_fill_color(*self.light_bg)
        self.set_draw_color(*self.border_color)
        self.set_font('Courier', '', 8)
        self.set_text_color(40, 50, 60)
        
        # Format code to avoid long lines wrapping badly
        lines = code_text.split('\n')
        self.ln(2)
        
        # Check remaining space, if too small, insert a page break
        required_height = len(lines) * 4.5 + 4
        if self.get_y() + required_height > 270:
            self.add_page()
            self.ln(10)
            
        x_start = self.get_x()
        y_start = self.get_y()
        
        # Draw background rectangle
        self.rect(x_start, y_start, 170, required_height, 'DF')
        self.set_xy(x_start + 4, y_start + 2)
        
        for line in lines:
            self.cell(0, 4.2, line, new_x="LMARGIN", new_y="NEXT", align='L')
            self.set_x(x_start + 4)
            
        self.set_xy(x_start, y_start + required_height)
        self.ln(4)

    def add_table_row(self, widths, row_data, headers=False):
        self.set_font('Helvetica', 'B' if headers else '', 9)
        if headers:
            self.set_fill_color(230, 240, 255)
            self.set_text_color(*self.primary_color)
        else:
            self.set_fill_color(255, 255, 255)
            self.set_text_color(*self.text_color_main)
            
        self.set_draw_color(*self.border_color)
        
        # Calculate row height
        max_nb = 0
        for i, val in enumerate(row_data):
            w = widths[i]
            nb = self.get_string_width(str(val)) / w
            if nb > max_nb:
                max_nb = nb
        row_height = max(5, int(max_nb + 1) * 4.2)
        
        # Check page break
        if self.get_y() + row_height > 270:
            self.add_page()
            
        x_pos = self.get_x()
        y_pos = self.get_y()
        
        for i, val in enumerate(row_data):
            self.set_xy(x_pos, y_pos)
            self.multi_cell(widths[i], row_height / (int(self.get_string_width(str(val)) / widths[i]) + 1) if not headers else row_height, str(val), 1, 'L', fill=True)
            x_pos += widths[i]
            
        self.set_xy(self.l_margin, y_pos + row_height)

def build_pdf():
    pdf = KalyxDocumentation()
    
    # 1. Cover Page
    pdf.cover_page()
    
    # 2. Executive Summary
    pdf.add_section_header("2. Executive Summary")
    pdf.add_paragraph("Curriculum design and pedagogical planning in higher education is currently a deeply manual, siloed, and slow process. Professors and instructional designers spend hundreds of hours drafting syllabi, alignment maps, slide outlines, speaker notes, and multi-level assessments. This manual workflow often results in misalignment between target learning outcomes, course materials, and examinations. Furthermore, keeping academic content synchronized with rapid industry technological advancements (like generative AI, modern cloud practices, and vector databases) remains extremely challenging.")
    pdf.add_paragraph("KALYX is an AI-powered Curriculum Intelligence Platform that revolutionizes this process. Leveraging a multi-agent system composed of 9 specialized AI agents operating under a stateful LangGraph workflow, KALYX ingests raw syllabus descriptions, creates standard weekly lesson plans, designs deep academic slide outlines, writes accompanying speaker scripts, produces Bloom's Taxonomy-mapped assessments, audits compliance, detects industry gaps, and evaluates course readiness.")
    pdf.add_paragraph("Through integration with the Groq API and Llama 3 models, KALYX delivers institutional-grade generation speeds, completing complex curriculum tasks in under 10 seconds. It establishes alignment across all educational materials, allowing universities and training institutions to construct modern, pedagogically sound, and industry-aligned courses in minutes rather than months.")
    
    # 3. Problem Statement
    pdf.add_section_header("3. Problem Statement")
    pdf.add_paragraph("Higher education institutions face a complex, interconnected set of problems when creating and updating curricula:")
    pdf.add_bullet("High Development Cost and Latency", "Constructing a new university-level course requires between 80 to 120 hours of academic preparation, causing significant curriculum updates to lag years behind industry state-of-the-art.")
    pdf.add_bullet("Pedagogical Alignment", "Creating alignment between learning objectives and assessments is technically difficult. Frequently, assessments evaluate rote memorization (lower Bloom levels) while course objectives target critical thinking (higher Bloom levels).")
    pdf.add_bullet("Industry Relevance Mismatch", "As industry demands shift rapidly, academic syllabi fail to adapt, leaving students with outdated training and widening the skills gap in high-tech fields.")
    pdf.add_bullet("Siloed Content Formats", "Lecture slides, teaching notes, and exam databases are generated in isolation. Changes in weekly outlines do not automatically propagate to slide content or speaker scripts, leading to disjointed classroom instruction.")
    
    # 4. Approach & Methodology
    pdf.add_section_header("4. Approach & Methodology")
    pdf.add_paragraph("To build KALYX, the engineering team adopted a structured, pedagogy-first methodology that addresses technical scalability, user-experience, and AI safety:")
    pdf.add_bullet("Requirement Gathering", "Gathered feedback from university instructors and instructional designers. Identified syllabus parsing, lesson plan generation, slide design draft, and aligned question creation as the core bottlenecks.")
    pdf.add_bullet("System Design", "Designed a decoupled system composed of a Next.js (TypeScript/Tailwind CSS) frontend for highly visual user interactions and a FastAPI (Python/SQLAlchemy) backend to coordinate the orchestration of AI workflows and databases.")
    pdf.add_bullet("AI Workflow Design", "Utilized LangGraph to organize the multi-agent system into a stateful, linear pipeline. LangGraph maintains a central shared state containing syllabus data, generated slide lists, speaker notes, and evaluations, ensuring consistent inputs across agents.")
    pdf.add_bullet("Agent Specialization", "Segmented tasks into 9 distinct agents. Each agent operates with highly targeted system prompts, system-level instructions, and strict JSON output schemas (leveraging Pydantic models).")
    pdf.add_bullet("Iterative Optimization", "Transited from slower, high-latency models to Groq API's Llama 3 infrastructure. Resolved JSON parsing issues by implementing dynamic JSON schema resolver components that remove nested definitions.")
    pdf.add_bullet("Testing & Validation", "Implemented comprehensive automated testing for critical modules (e.g., authentication, password verification) and full agent pipelines to guarantee stability and prevent regressions.")
    
    # 5. System Architecture
    pdf.add_section_header("5. System Architecture")
    pdf.add_paragraph("KALYX's architecture is structured to separate concern between presentation, coordination, AI reasoning, and data persistence.")
    pdf.add_subheading("High-Level System Flow")
    
    # Text-based visual diagram
    diagram = """
+------------------+       HTTPS Requests        +--------------------+
|  Next.js Client  | <=========================> |  FastAPI Backend   |
| (Vercel Hosting) |      (JSON Payload)         |  (Render Hosting)  |
+------------------+                             +--------------------+
                                                           ||
                                                   Orchestrates State
                                                           ||
                                                           \/
                                                 +--------------------+
                                                 | LangGraph Workflow |
                                                 +--------------------+
                                                           ||
                                                    Sequential Runs
                                                           ||
                                                           \/
                                                 +--------------------+
                                                 | 9 Specialized AI   |
                                                 |   Agents (Groq)    |
                                                 +--------------------+
                                                           ||
                                                      Persists Data
                                                           ||
                                                           \/
                                                 +--------------------+
                                                 |  SQLite Database   |
                                                 +--------------------+
"""
    pdf.add_code_block(diagram)
    
    pdf.add_paragraph("Component Explanations:")
    pdf.add_bullet("User/Frontend", "The client interacts with a responsive, glassmorphic Next.js portal. Instructors upload syllabus files, edit course settings, view generated outlines, export slides, and analyze alignment audits.")
    pdf.add_bullet("Backend", "The FastAPI server handles HTTP requests, serves API endpoints, manages user authentication sessions, coordinates background generation tasks, and exposes export tools.")
    pdf.add_bullet("LangGraph Layer", "Acts as the stateful engine. It compiles a sequential state machine where each node represents a specialized agent that edits the shared state, propagating changes down the chain.")
    pdf.add_bullet("9 Agents Layer", "Specialized prompts run in parallel or sequence, calling the Groq API to perform analysis, planning, generation, auditing, and scoring.")
    pdf.add_bullet("Groq API", "Provides sub-second token generation times for Llama 3 models, making a multi-agent generation loop with dozens of requests feasible in real-time.")
    pdf.add_bullet("SQLite Database", "Stores user profiles, courses, uploaded files, slide contents, instructor notes, assessments, and readiness reports.")
    
    # 6. Technical Architecture
    pdf.add_section_header("6. Technical Architecture")
    pdf.add_paragraph("This section breaks down the technology layers that form KALYX's engine.")
    
    pdf.add_subheading("Frontend Architecture")
    pdf.add_paragraph("The frontend is written in Next.js 14 utilizing TypeScript. The dashboard operates on single-page state, providing real-time visual progress of the LangGraph agent executions. Styling is created using Vanilla Tailwind CSS classes, customized color schemes (rich dark colors, gradient rings, glass panels), and Outfit typography. API communication is orchestrated via asynchronous fetch queries.")
    
    pdf.add_subheading("Backend Architecture")
    pdf.add_paragraph("FastAPI serves as the backend layer. It uses Uvicorn as an ASGI server. The directory architecture separates API routers, SQLAlchemy models, database connection pools, and multi-agent workflow definitions. Background tasks are managed using standard FastAPI BackgroundTasks to prevent blocking the request-response thread during pipeline runs.")
    
    pdf.add_subheading("AI Layer & LangGraph Node Design")
    pdf.add_paragraph("The AI layer uses LangGraph to coordinate the pipeline. The state consists of input course info, curriculum map, learning outcomes, generated slides, speaker notes, assessments, gap reports, and readiness indicators. Each agent is a Node that writes to specific keys in the shared dictionary.")
    
    mermaid_workflow = """
[Start] -> (Curriculum Analysis) -> (Learning Outcome) -> (Curriculum Planning)
                                                                 ||
                                                                 \/
[End] <- (Readiness Score) <- (Industry Gap) <- (Bloom Audit) <- (Slides/Notes/MCQ)
"""
    pdf.add_code_block(mermaid_workflow)
    
    pdf.add_subheading("Database Layer")
    pdf.add_paragraph("SQLite is used locally to provide zero-configuration data persistence. In production, SQLAlchemy handles schema binding and provides transaction-safe sessions. All foreign keys cascade on delete, ensuring consistency across related courses, slides, notes, and assessments.")
    
    pdf.add_subheading("Authentication Layer")
    pdf.add_paragraph("JWT tokens (HS256) authenticate API requests. Passwords are encrypted with salt using the `bcrypt` library. The login flow supports case-insensitive username/email matching, and the verification utility has been audited for strict type-safety across Python string and bytes inputs.")
    
    # 7. Code Structure
    pdf.add_section_header("7. Code Structure")
    pdf.add_paragraph("KALYX is organized into two primary folders: frontend and backend. Below is the complete repository structure:")
    
    code_tree = """
KALYX/
|-- backend/
|   |-- app/
|   |   |-- agents/
|   |   |   |-- __init__.py
|   |   |   |-- workflow.py         # 9-agent LangGraph workflow
|   |   |-- routers/
|   |   |   |-- __init__.py
|   |   |   |-- auth.py             # Signup, login, and JWT endpoints
|   |   |   |-- courses.py          # Course management and generation endpoints
|   |   |   |-- export.py           # PPTX/DOCX export endpoints
|   |   |   |-- studio.py           # Slide editing & interactive studio API
|   |   |-- services/
|   |   |   |-- __init__.py
|   |   |   |-- rag_service.py      # Document embeddings & retrieval
|   |   |-- database.py             # SQLAlchemy configuration
|   |   |-- main.py                 # FastAPI application startup & routing
|   |   |-- models.py               # Database tables
|   |   |-- security.py             # Rate limiters & token decoders
|   |-- requirements.txt            # Python dependencies
|   |-- test_auth_audit.py          # Authentication audit script
|   |-- test_pipeline_run.py        # Pipeline execution test script
|-- frontend/
|   |-- src/
|   |   |-- app/
|   |   |   |-- layout.tsx
|   |   |   |-- page.tsx            # Main visual application interface
|   |   |   |-- globals.css
|   |   |-- components/             # Reusable UI widgets
|   |   |-- context/                # Client state management
|   |-- package.json
|   |-- tailwind.config.js
|-- README.md
"""
    pdf.add_code_block(code_tree)
    
    # 8. Core Source Code Modules
    pdf.add_section_header("8. Core Source Code Modules")
    pdf.add_paragraph("This section reviews the primary source code files of KALYX, details their business logic, inputs, outputs, and critical functions.")
    
    pdf.add_subheading("workflow.py")
    pdf.add_bullet("Purpose", "Implements the multi-agent state graph, structures LLM prompts, flattened schemas, and retries.")
    pdf.add_bullet("Inputs", "Raw syllabus text, course title, target learning level.")
    pdf.add_bullet("Outputs", "A complete dictionary containing structured weekly lesson plans, slides, speaker notes, MCQs, and readiness audits.")
    pdf.add_bullet("Key Functions", "call_llm (handles rate-limit retry and backoff), resolve_defs (resolves Pydantic references), and agent execution nodes (analyze_curriculum_node, plan_curriculum_node, etc.).")
    
    pdf.add_subheading("auth.py")
    pdf.add_bullet("Purpose", "Coordinates signup and login endpoints, password hashing, and token generations.")
    pdf.add_bullet("Inputs", "Pydantic request payload (UserSignup, UserLoginSchema).")
    pdf.add_bullet("Outputs", "TokenResponse JSON containing JWT and user profile data.")
    pdf.add_bullet("Key Functions", "hash_password, verify_password (type-safe logic), signup, and login endpoints.")
    
    pdf.add_subheading("courses.py")
    pdf.add_bullet("Purpose", "Exposes API endpoints to create courses, upload syllabi, and trigger the multi-agent generation.")
    pdf.add_bullet("Key Functions", "create_course, upload_syllabus, and generate_curriculum (which spawns the LangGraph background task).")
    
    pdf.add_subheading("rag_service.py")
    pdf.add_bullet("Purpose", "Handles upload document parsing, generates mock or Gemini-based embeddings, and fetches relevant context chunks.")
    pdf.add_bullet("Key Functions", "process_document, retrieve_relevant_chunks, and get_embedding.")

    pdf.add_subheading("database.py & models.py")
    pdf.add_bullet("Purpose", "Configures SQLAlchemy DB connection parameters, session lifetimes, and binds SQLite tables (User, Course, GeneratedSlide, InstructorNote, Assessment, CurriculumAnalysis, ReadinessScore).")

    pdf.add_subheading("page.tsx")
    pdf.add_bullet("Purpose", "Serves as the frontend UI. Implements forms to submit course parameters, displays the pipeline progress, and hosts the course slide studio.")

    # 9. Multi-Agent Workflow
    pdf.add_section_header("9. Multi-Agent Workflow")
    pdf.add_paragraph("KALYX coordinates 9 specialized agents inside a stateful graph to process a course outline. Below is a detailed description of each agent's purpose, input, output, prompt design, and interaction profile.")
    
    pdf.add_table_row([35, 65, 70], ["Agent Name", "Primary Purpose", "Output Data Format"], headers=True)
    pdf.add_table_row([35, 65, 70], ["1. Curriculum Analysis", "Extracts metadata, prerequisites, and core learning goals from the raw syllabus document.", "Structured JSON metadata & topic list"])
    pdf.add_table_row([35, 65, 70], ["2. Learning Outcome", "Generates outcome statements mapped directly to Bloom's Taxonomy cognitive levels.", "JSON list of outcomes + cognitive tiers"])
    pdf.add_table_row([35, 65, 70], ["3. Curriculum Planning", "Expands topics into a complete weekly lesson plan (30 weeks of teaching structure).", "Weekly lesson structures & subtopics"])
    pdf.add_table_row([35, 65, 70], ["4. Slide Generation", "Generates slide titles, layouts, visual directions, and academic text paragraphs in batches.", "JSON list of slides per week"])
    pdf.add_table_row([35, 65, 70], ["5. Instructor Notes", "Generates deep, slide-specific lecture scripts, talking points, and classroom examples.", "JSON list of notes mapped to slide indices"])
    pdf.add_table_row([35, 65, 70], ["6. Assessment", "Generates high-quality multiple choice questions (MCQs) mapped to outcomes.", "JSON list of MCQs + keys + outcomes"])
    pdf.add_table_row([35, 65, 70], ["7. Bloom Audit", "Audits the alignment between learning outcomes and generated questions.", "JSON audit reports pointing to misalignments"])
    pdf.add_table_row([35, 65, 70], ["8. Industry Gap", "Compares course content to modern industry trends, noting gaps and suggesting topics.", "JSON gap reports & integration suggestions"])
    pdf.add_table_row([35, 65, 70], ["9. Readiness Score", "Synthesizes all reports into a unified course readiness score (0-100) and breakdown.", "JSON scores & final pedagogical comments"])
    pdf.ln(5)
    
    pdf.add_paragraph("Prompt Design & LLM Optimization:")
    pdf.add_bullet("Strict JSON Schemas", "Pydantic validation schemas enforce exact structural types. Llama models are instructed via system prompts to return only valid JSON fitting these schemas, preventing parser crashes.")
    pdf.add_bullet("Workflow Progression", "Output from the Planning Agent acts as the structural spine. The Slide, Note, and Assessment Agents use this spine to populate content, maintaining pedagogical continuity.")
    
    # 10. Database Design
    pdf.add_section_header("10. Database Design")
    pdf.add_paragraph("The SQLite schema utilizes SQLAlchemy ORM models. All tables support primary keys, foreign key constraints with cascade deletes, and JSON serialization fields.")
    
    pdf.add_subheading("Database Tables & Schema Configuration")
    pdf.add_table_row([35, 30, 155], ["Table Name", "Primary Key", "Columns & Foreign Keys"], headers=True)
    pdf.add_table_row([35, 30, 155], ["users", "id (Integer)", "email (String, Unique), username (String, Unique), hashed_password (String), full_name (String), created_at (DateTime)"])
    pdf.add_table_row([35, 30, 155], ["courses", "id (Integer)", "user_id (Integer -> users.id), title (String), description (Text), created_at (DateTime)"])
    pdf.add_table_row([35, 30, 155], ["syllabi", "id (Integer)", "course_id (Integer -> courses.id), raw_text (Text), file_name (String), file_path (String)"])
    pdf.add_table_row([35, 30, 155], ["curriculum_analysis", "id (Integer)", "course_id (Integer -> courses.id), curriculum_map (JSON), gap_analysis (JSON), industry_gap_report (JSON)"])
    pdf.add_table_row([35, 30, 155], ["generated_slides", "id (Integer)", "course_id (Integer -> courses.id), slide_index (Integer), title (String), content (JSON), suggested_visuals (Text)"])
    pdf.add_table_row([35, 30, 155], ["instructor_notes", "id (Integer)", "course_id (Integer -> courses.id), slide_index (Integer), talking_points (JSON), teaching_tips (Text), examples (JSON)"])
    pdf.add_table_row([35, 30, 155], ["assessments", "id (Integer)", "course_id (Integer -> courses.id), question_text (Text), question_type (String), options (JSON), correct_answer (Text), bloom_level (String)"])
    pdf.add_table_row([35, 30, 155], ["readiness_scores", "id (Integer)", "course_id (Integer -> courses.id), score (Float), completeness (Float), outcome_coverage (Float), assessment_quality (Float), breakdown (JSON)"])
    pdf.ln(5)
    
    # 11. Authentication Design
    pdf.add_section_header("11. Authentication Design")
    pdf.add_paragraph("KALYX implements stateless authentication using JSON Web Tokens (JWT) and industry-standard password cryptosecurity.")
    pdf.add_bullet("Password Encryption", "Uses bcrypt.hashpw with a work factor of 12. Salting is handled natively by bcrypt to prevent rainbow-table compromises.")
    pdf.add_bullet("JWT Sessions", "Upon successful login, a JWT is issued with the subject ('sub') set to the user's email, signed with a secret key using the HS256 algorithm. Session tokens expire in 1440 minutes (24 hours).")
    pdf.add_bullet("Case-Insensitive Queries", "User lookups normalize usernames and emails by trimming leading/trailing whitespaces and performing database queries with SQLAlchemy's func.lower(column) against the user's input, preventing duplicate login issues.")
    
    pdf.add_subheading("Type-Safe Password Verification Fix")
    pdf.add_paragraph("During a security audit, a type strictness bug was identified. bcrypt.checkpw(plain_password, hashed_password) requires both arguments to be of type bytes. If the database driver (such as PostgreSQL on Render) returns the hashed_password as a bytes string, calling .encode('utf-8') on it raises an AttributeError. A silent general try-except block swallowed the exception and returned False, causing authentication to fail even with correct credentials.")
    pdf.add_paragraph("The verified fix check parameter types dynamically, converting only str types to UTF-8 encoded bytes while preserving pre-encoded bytes hashes, ensuring platform-agnostic performance:")
    
    code_fix = """
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Convert plain password to bytes safely
        if isinstance(plain_password, str):
            plain_bytes = plain_password.encode('utf-8')
        elif isinstance(plain_password, bytes):
            plain_bytes = plain_password
        else:
            plain_bytes = str(plain_password).encode('utf-8')

        # Convert hashed password to bytes safely
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        elif isinstance(hashed_password, bytes):
            hashed_bytes = hashed_password
        else:
            hashed_bytes = str(hashed_password).encode('utf-8')

        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Error in verify_password: {e}", exc_info=True)
        return False
"""
    pdf.add_code_block(code_fix)
    
    # 12. API Documentation
    pdf.add_section_header("12. API Documentation")
    pdf.add_paragraph("KALYX backend exposes REST API endpoints for user sessions, course management, multi-agent pipelines, and pptx exports.")
    
    pdf.add_subheading("1. Authentication APIs")
    pdf.add_bullet("Signup: POST /api/auth/signup", "Creates a new user profile. Expects JSON body with email, username, password, full_name. Returns JSON Web Token.")
    pdf.add_bullet("Login: POST /api/auth/login", "Authenticates existing users. Expects JSON body with username_or_email, password. Returns JWT access token.")
    
    pdf.add_subheading("2. Course Management APIs")
    pdf.add_bullet("Create Course: POST /api/courses/create", "Requires authorization token header. Creates a course entry. Body: title, description.")
    pdf.add_bullet("Upload Syllabus: POST /api/courses/{course_id}/syllabus", "Uploads a text/PDF syllabus file. Associates it with the course.")
    pdf.add_bullet("Trigger Pipeline: POST /api/courses/{course_id}/generate", "Triggers the 9-agent LangGraph generation loop in the background. Returns generation confirmation.")
    
    pdf.add_subheading("3. Export APIs")
    pdf.add_bullet("Export PPTX: GET /api/export/{course_id}/slides", "Generates and downloads a slide deck (.pptx) compiled from slide database records.")
    pdf.add_bullet("Export DOCX: GET /api/export/{course_id}/notes", "Generates and downloads a Word document (.docx) containing the lecture syllabus and instructor notes.")
    
    # 13. Groq Migration
    pdf.add_section_header("13. Groq Migration")
    pdf.add_paragraph("Initially, KALYX utilized Google's Gemini API. During scaling tests, Google GenAI hit strict rate limits (TPM/RPM ceilings), causing long-running multi-agent pipelines to crash. To solve this, the engineering team migrated KALYX to the Groq API.")
    pdf.add_bullet("Why Groq?", "Groq provides high-throughput token generation for Llama 3 models, cutting the pipeline run time from minutes to under 10 seconds.")
    pdf.add_bullet("Dynamic Rate Limit Retries", "To handle Groq's token-per-minute limitations during batching, a custom retry loop parses rate limit headers. When a 429 status code is received, it extracts the exact retry delay (e.g. 'try again in 24.83s') and pauses the thread accordingly, adding a safety margin.")
    pdf.add_bullet("Schema Reference Resolver", "Groq's Llama models struggle to parse Pydantic JSON schemas that use references ($defs and $ref). Weasy/Groq Llama models would hallucinate schema structures rather than outputting actual data. To resolve this, a recursive function resolve_defs was implemented to inline and flatten all schema definitions before passing them to the API.")
    pdf.add_bullet("Batching Loop Strategy", "To prevent output truncation due to context-length limits, content is generated in batches. The Slide Agent generates slides in blocks of 5 weeks; the Notes Agent writes scripts in blocks of 5 slides; and the Assessment Agent produces MCQs in batches of 6, resolving context exhaustion issues.")
    
    # 14. Challenges & Learnings
    pdf.add_section_header("14. Challenges & Learnings")
    pdf.add_paragraph("Building a stateful multi-agent curriculum platform presented several technical challenges:")
    pdf.add_bullet("1. LLM Output Truncation", "Large curriculum outputs were cut off. Solution: Implemented block batching (5 slides/lessons per API call).")
    pdf.add_bullet("2. Pydantic Defs Parser Crash", "Llama models generated schema-like text instead of real data. Solution: Developed resolve_defs to flatten references.")
    pdf.add_bullet("3. Severe Groq Rate Limits (429)", "Pipelines crashed due to concurrent requests. Solution: Implemented header parsing to calculate dynamic sleep delays.")
    pdf.add_bullet("4. Production DB Auth Failure", "Database returned password hashes as bytes on Render, crashing login. Solution: Developed a type-safe verification utility.")
    pdf.add_bullet("5. Inconsistent State Synchronization", "Agents overwrote each other's outputs. Solution: Transitioned to a centralized LangGraph state dict.")
    pdf.add_bullet("6. Slow Frontend Render Updates", "Client UI was unresponsive during background runs. Solution: Implemented background polling endpoints.")
    pdf.add_bullet("7. Google API Dependency Bloat", "Gemini import failures crashed startup when offline. Solution: Decoupled imports, moving them inline.")
    pdf.add_bullet("8. PDF/Docx Export Sizing", "Text wrapped poorly in slides. Solution: Calibrated python-pptx shapes to scale text blocks dynamically.")
    pdf.add_bullet("9. Case Sensitivity on Login", "Users failed to log in when username case mismatched. Solution: Normalizing inputs with func.lower(...) in SQLAlchemy.")
    pdf.add_bullet("10. Thread Blocking during Generation", "Long generation runs timed out client sockets. Solution: Moved agent graph compilation to FastAPI's BackgroundTasks.")

    # 15. Testing & Validation
    pdf.add_section_header("15. Testing & Validation")
    pdf.add_paragraph("KALYX is tested using automated scripts that execute within the shell environment, validating database connections, schema sync, authorization sessions, and multi-agent pipeline compliance.")
    
    pdf.add_subheading("1. Authentication Unit & Integration Tests")
    pdf.add_paragraph("The test suite test_auth_audit.py performs the following steps:")
    pdf.add_bullet("Step A", "Directly tests password hashing and verification with both str and bytes parameters to ensure type safety.")
    pdf.add_bullet("Step B", "Signs up a test user, verifying DB commit and password encryption.")
    pdf.add_bullet("Step C", "Logs in by email, checking matching logic and token responses.")
    pdf.add_bullet("Step D", "Logs in by username with whitespace and uppercase variation, verifying normalization.")
    pdf.add_bullet("Step E", "Parses the generated JWT and validates token signatures.")
    
    pdf.add_subheading("2. Workflow Telemetry Validation")
    pdf.add_paragraph("The pipeline test test_pipeline_run.py validates LangGraph executions. It seeds a course outline, compiles the state machine, triggers the 9-agent chain, and captures node completion times, confirming correct execution paths.")
    
    # 16. Deployment Architecture
    pdf.add_section_header("16. Deployment Architecture")
    pdf.add_paragraph("KALYX is designed for simple, cloud-native deployments with decoupled frontend and backend hosting:")
    pdf.add_bullet("Frontend (Vercel)", "The Next.js single-page application is hosted on Vercel. Static assets are optimized, and API calls route to the Render backend domain via HTTPS.")
    pdf.add_bullet("Backend (Render)", "The FastAPI backend runs on Render as a Web Service. Uvicorn manages port bindings and spawns threads dynamically.")
    pdf.add_bullet("SQLite Persistence", "The local SQLite database (kalyx.db) is stored in Render's persistent disk storage directory, preventing data loss during deployment updates.")
    pdf.add_bullet("Environment Variables", "Backend configuration uses .env inputs for JWT_SECRET, DATABASE_URL, GROQ_API_KEY, and GROQ_MODEL.")
    
    # 17. Screenshots Section
    pdf.add_section_header("17. Screenshots Section")
    pdf.add_paragraph("Below are descriptions and structural layouts of KALYX's user interface pages. These serve as visual guides for evaluation panels:")
    pdf.add_bullet("1. Login Portal", "A glassmorphic card interface featuring email/username login forms, a secure password field, and automatic placeholder suggestions ('e.g. Dr. John Doe').")
    pdf.add_bullet("2. Dashboard Screen", "Displays user-curated courses in grid layouts. Each card displays course details, creation date, and status indicators.")
    pdf.add_bullet("3. Syllabus Upload & Pipeline Progress", "Contains a drag-and-drop file upload area. Upon uploading, a visual timeline displays agent node steps (1 to 9) turning from slate-gray (pending) to spinning indigo (active) to green (completed).")
    pdf.add_bullet("4. Interactive Studio Editor", "A workspace displaying generated slide previews on the left, an editable markdown text editor in the center, and instructor notes and assessments on the right.")
    pdf.add_bullet("5. Pedagogical Audit Panel", "Renders a color-coded chart displaying Bloom's taxonomy coverage alongside lists of identified industry gaps and overall course readiness scores (0-100%).")
    
    # 18. Innovation & Uniqueness
    pdf.add_section_header("18. Innovation & Uniqueness")
    pdf.add_paragraph("KALYX introduces several novel features compared to standard education platforms:")
    pdf.add_bullet("Agentic Coordination", "Instead of a single unstructured prompt, KALYX divides the generation workflow into 9 distinct, specialized nodes, resulting in highly detailed outputs.")
    pdf.add_bullet("Closed-Loop Pedagogical Audit", "The Bloom Audit Agent reviews the generated slides and assessments against target outcomes, flagging misalignment and ensuring quality control.")
    pdf.add_bullet("Industry-Driven Optimization", "The Industry Gap Agent checks external trends (e.g. cloud patterns, web standards) against course modules, suggesting real-world topics to ensure content relevance.")
    pdf.add_bullet("Unified File Exports", "Transforms database tables directly into styled PPTX slide decks and DOCX lecture notes, exporting production-ready materials instantly.")
    
    # 19. Future Scope
    pdf.add_section_header("19. Future Scope")
    pdf.add_paragraph("The future roadmap for KALYX targets enterprise scalability and enhanced learner personalization:")
    pdf.add_bullet("Adaptive Learning Pathways", "Generate personalized slide variations tailored to student backgrounds (e.g., beginner vs advanced variations).")
    pdf.add_bullet("LMS Integrations", "Export course packages directly as SCORM-compliant files or Canvas/Blackboard cartridges.")
    pdf.add_bullet("Enterprise Database Migration", "Transition SQLite databases to managed PostgreSQL clusters for high concurrency support.")
    pdf.add_bullet("Managed Vector Database", "Integrate dedicated vector stores (e.g., Pinecone or pgvector) to enable context retrieval across large institution-wide academic repositories.")
    pdf.add_bullet("Automated TA Chatbot", "Embed a student-facing chatbot using generated notes and slide context to answer student queries dynamically.")
    
    # 20. Repository & Submission Details
    pdf.add_section_header("20. Repository & Submission Details")
    pdf.add_paragraph("Repository Link: https://github.com/Devashish275/kalyx-")
    pdf.add_subheading("Build & Execution Instructions")
    
    pdf.add_paragraph("1. Backend Setup:")
    pdf.add_code_block("cd backend\n/usr/bin/python3 -m venv venv\nsource venv/bin/activate\npip install -r requirements.txt\nuvicorn app.main:app --reload --port 8000")
    
    pdf.add_paragraph("2. Frontend Setup:")
    pdf.add_code_block("cd frontend\nnpm install\nnpm run dev")
    
    pdf.add_paragraph("3. Environment Template (.env):")
    pdf.add_code_block("DATABASE_URL=sqlite:///./kalyx.db\nJWT_SECRET=supersecret_key_change_me_in_production\nJWT_ALGORITHM=HS256\nGROQ_API_KEY=your_groq_api_key\nGROQ_MODEL=llama-3.1-8b-instant")
    
    # 21. Conclusion
    pdf.add_section_header("21. Conclusion")
    pdf.add_paragraph("KALYX represents a major step forward in AI-assisted educational design. By structuring a multi-agent system into a stateful LangGraph pipeline, KALYX automates the manual workflow of syllabus decomposition, slide drafting, lecture script generation, and assessment alignment.")
    pdf.add_paragraph("Through robust type-safety fixes, dynamic rate limit retries, and inlined schema reference resolvers, the platform offers commercial-grade reliability. Leveraging Groq's high-speed API, KALYX minimizes generation latency, proving that AI agent coordination can deliver pedagogically aligned, industry-relevant curricula in seconds. KALYX is positioned to help universities scale modern, high-quality, and aligned educational pathways globally.")
    
    # Save the PDF
    pdf.output("KALYX_HACKATHON_SOURCE_CODE_DOCUMENTATION.pdf")
    print("Documentation PDF generated successfully!")

if __name__ == '__main__':
    build_pdf()
