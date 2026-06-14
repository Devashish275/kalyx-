import os
import sys
from fpdf import FPDF

class SourceCodePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(True, 15)
        self.primary_color = (30, 41, 59)     # Slate-800
        self.secondary_color = (56, 189, 248) # Sky-400
        self.text_color_main = (15, 23, 42)    # Slate-900
        self.code_bg = (248, 250, 252)        # Slate-50
        self.border_color = (226, 232, 240)   # Slate-200
        
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 10, 'KALYX - Technical Source Code Repository', new_x="RIGHT", new_y="TOP", align='L')
            self.cell(0, 10, f'Page {self.page_no()}', new_x="LMARGIN", new_y="NEXT", align='R')
            self.set_draw_color(*self.border_color)
            self.line(15, 20, 195, 20)
            self.ln(3)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 10, 'Confidential - Submission Source Code', new_x="RIGHT", new_y="TOP", align='L')
            self.cell(0, 10, 'KALYX © 2026', new_x="RIGHT", new_y="TOP", align='R')

    def cover_page(self):
        self.add_page()
        # Cover background
        self.set_fill_color(*self.primary_color)
        self.rect(0, 0, 210, 297, 'F')
        
        # Cover accent bar
        self.set_fill_color(*self.secondary_color)
        self.rect(15, 80, 5, 120, 'F')
        
        # Titles
        self.set_xy(30, 95)
        self.set_font('Helvetica', 'B', 40)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, 'KALYX', new_x="LMARGIN", new_y="NEXT", align='L')
        
        self.set_x(30)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(*self.secondary_color)
        self.cell(0, 10, 'COMPLETE SOURCE CODE REPOSITORY', new_x="LMARGIN", new_y="NEXT", align='L')
        
        self.ln(10)
        self.set_x(30)
        self.set_font('Helvetica', '', 11)
        self.set_text_color(203, 213, 225)
        self.multi_cell(150, 5.5, 'Official technical submission document containing all source code modules for the FastAPI backend, Next.js frontend, and multi-agent LangGraph workflow engine.', 0, 'L')
        
        # Submission Details
        self.set_xy(30, 220)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, 'SUBMISSION FOR: Hackathon Evaluation Committee', new_x="LMARGIN", new_y="NEXT", align='L')
        self.set_x(30)
        self.cell(0, 6, 'LANGUAGES: TypeScript, Python, Tailwind CSS, HTML', new_x="LMARGIN", new_y="NEXT", align='L')
        self.set_x(30)
        self.cell(0, 6, 'TEAM: KALYX Core Engineers', new_x="LMARGIN", new_y="NEXT", align='L')
        self.set_x(30)
        self.cell(0, 6, 'DATE: June 2026', new_x="LMARGIN", new_y="NEXT", align='L')

    def add_file_section(self, file_path, code_text):
        self.add_page()
        # Section Header
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*self.primary_color)
        self.cell(0, 10, f"File: {file_path}", new_x="LMARGIN", new_y="NEXT", align='L')
        self.set_fill_color(*self.secondary_color)
        self.rect(15, 27, 40, 1.5, 'F')
        self.ln(5)
        
        # Output code text
        self.set_font('Courier', '', 7.5)
        self.set_text_color(30, 41, 59)
        self.set_fill_color(*self.code_bg)
        
        lines = code_text.split('\n')
        # We print line-by-line using multicell to allow automatic page breaking
        for idx, line in enumerate(lines, 1):
            line_str = f"{idx:4d} | {line}"
            # Render each line of code
            self.multi_cell(0, 3.8, line_str, border=0, align='L', fill=True, new_x='LMARGIN', new_y='NEXT')

def sanitize_text(text):
    # Safely convert unicode characters to ascii equivalents for standard PDF Courier font
    replacements = {
        '\u201c': '"', '\u201d': '"',
        '\u2018': "'", '\u2019': "'",
        '\u2013': '-', '\u2014': '-',
        '\u2022': '-',
        '\u2500': '-', '\u2502': '|',
        '\u251c': '|', '\u2514': '\\',
        '\u2510': '+', '\u250c': '+',
        '\u253c': '+', '\u252c': '+',
        '\u2534': '+', '\u2524': '+',
        '\u00a0': ' ', # non-breaking space
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    # Fallback to ascii conversion
    return text.encode('ascii', errors='replace').decode('ascii')

def main():
    print("Initializing Source Code PDF Compilation...")
    pdf = SourceCodePDF()
    pdf.cover_page()
    
    # Core project files to read
    project_files = [
        # Database & Base Configuration
        "backend/app/database.py",
        "backend/app/models.py",
        "backend/app/security.py",
        
        # Core Workflows & Logic
        "backend/app/agents/workflow.py",
        "backend/app/services/rag_service.py",
        
        # API Routers
        "backend/app/routers/auth.py",
        "backend/app/routers/courses.py",
        "backend/app/routers/studio.py",
        "backend/app/routers/export.py",
        
        # Server Entry
        "backend/app/main.py",
        
        # Tests
        "backend/test_auth_audit.py",
        
        # Frontend Main Page
        "frontend/src/app/page.tsx",
    ]
    
    workspace_root = "/Users/devashishpandey/code/KALYX9"
    
    for relative_path in project_files:
        full_path = os.path.join(workspace_root, relative_path)
        print(f"Reading file: {relative_path}...")
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                sanitized = sanitize_text(content)
                pdf.add_file_section(relative_path, sanitized)
                print(f"Successfully added: {relative_path}")
            except Exception as e:
                print(f"Error reading {relative_path}: {e}")
        else:
            print(f"File not found: {relative_path}")
            
    output_path = os.path.join(workspace_root, "KALYX_SOURCE_CODE.pdf")
    print(f"Writing PDF to {output_path}...")
    pdf.output(output_path)
    print("Source Code PDF generated successfully!")

if __name__ == '__main__':
    main()
