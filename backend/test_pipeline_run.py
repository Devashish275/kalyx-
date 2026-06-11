import requests
import sys
import json
import time

BASE_URL = "http://localhost:8000/api"

def run_test():
    print("1. Logging in as seeded user...")
    login_payload = {
        "username_or_email": "professor.jones@stanford.edu",
        "password": "hackathon_demo_pass"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        r.raise_for_status()
        token_data = r.json()
        token = token_data["access_token"]
        print(f"Logged in successfully. Token: {token[:15]}...")
    except Exception as e:
        print(f"Login failed: {e}")
        if 'r' in locals() and r is not None:
            print(r.text)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    print("\n2. Creating a new test course...")
    course_payload = {
        "title": "Advanced Machine Learning (Testing Groq)",
        "description": "Validation run for Groq API migration with 25-30 slides and dense content."
    }
    try:
        r = requests.post(f"{BASE_URL}/courses/", json=course_payload, headers=headers)
        r.raise_for_status()
        course_data = r.json()
        course_id = course_data["id"]
        print(f"Course created. ID: {course_id}")
    except Exception as e:
        print(f"Course creation failed: {e}")
        if 'r' in locals() and r is not None:
            print(r.text)
        sys.exit(1)

    print("\n3. Uploading syllabus and triggering 9-agent pipeline...")
    syllabus_path = "../Machine_Learning_Syllabus.txt"
    try:
        with open(syllabus_path, "rb") as f:
            files = {
                "file": ("Machine_Learning_Syllabus.txt", f, "text/plain")
            }
            start_time = time.time()
            r = requests.post(f"{BASE_URL}/courses/{course_id}/analyze", files=files, headers=headers, timeout=600)
            r.raise_for_status()
            duration = time.time() - start_time
            print(f"Pipeline finished execution in {duration:.2f}s.")
            res_data = r.json()
            print("Response status:", res_data.get("status"))
            print("Response message:", res_data.get("message"))
            print("\nPipeline Logs:")
            for log in res_data.get("logs", []):
                print(f"  {log}")
    except Exception as e:
        print(f"Pipeline execution failed: {e}")
        if 'r' in locals() and r is not None:
            print(r.text)
        sys.exit(1)

    print("\n4. Verifying generated data density and compliance...")
    try:
        r = requests.get(f"{BASE_URL}/courses/{course_id}", headers=headers)
        r.raise_for_status()
        course_details = r.json()
        
        # Check slides
        slides = course_details.get("slides", [])
        print(f"Generated Slide Count: {len(slides)}")
        
        # Verify slide count (Must be 25 to 30)
        if len(slides) < 25 or len(slides) > 30:
            print(f"WARNING: Slide count is {len(slides)}, expected 25 to 30.")
        else:
            print("SUCCESS: Slide count is in 25-30 range.")

        # Check content density on slides
        if slides:
            sample_slide = slides[0]
            print(f"Sample Slide Title: '{sample_slide.get('title')}'")
            print("Sample Slide Content points:")
            all_long_paragraphs = True
            for point in sample_slide.get("content", []):
                print(f"  - Length: {len(point)} chars | Sentences count approx: {len(point.split('.'))} | Content: {point}")
                # We expect long paragraphs (3-4 sentences), checking if they are reasonably long (e.g. > 100 characters)
                if len(point) < 80:
                    all_long_paragraphs = False
            if all_long_paragraphs:
                print("SUCCESS: Slide content bullets appear to be detailed paragraphs.")
            else:
                print("WARNING: Some slide content bullets are short.")

        # Check speaker notes
        notes = course_details.get("notes", [])
        print(f"Instructor Notes Count: {len(notes)}")
        if notes:
            sample_note = notes[0]
            tps = sample_note.get("talking_points", [])
            exs = sample_note.get("examples", [])
            print(f"Sample Note (Slide {sample_note.get('slide_index')}):")
            print(f"  - Talking points count: {len(tps)} (Expected >= 8-10)")
            print(f"  - Examples count: {len(exs)} (Expected >= 5-6)")
            if len(tps) >= 8:
                print("SUCCESS: Instructor notes talking points count matches expectations.")
            else:
                print(f"WARNING: Talking points count is {len(tps)} (expected >= 8)")
            if len(exs) >= 5:
                print("SUCCESS: Instructor notes examples count matches expectations.")
            else:
                print(f"WARNING: Examples count is {len(exs)} (expected >= 5)")

        # Check assessments
        assessments = course_details.get("assessments", [])
        print(f"Total Assessments (MCQs): {len(assessments)}")
        if len(assessments) >= 25:
            print("SUCCESS: Assessment MCQ count matches expectations (>= 25).")
        else:
            print(f"WARNING: Assessment MCQ count is {len(assessments)} (expected >= 25).")

    except Exception as e:
        print(f"Traceability check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
