import os
import json
import math
from typing import List, Dict, Any
from pypdf import PdfReader
from sqlalchemy.orm import Session
from app.models import UploadedDocument, Embedding

# Helper to get embeddings from Google Gemini
def get_embedding(text: str) -> List[float]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "" or api_key.startswith("your_"):
        # Local mock embedding generator (reproducible based on text hashes for demo stability)
        import hashlib
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        # Create a deterministic mock vector of 768 dimensions
        mock_vector = []
        for i in range(768):
            val = (int(h[i % 32], 16) / 15.0) * math.sin(i + 1)
            mock_vector.append(val)
        # Normalize vector
        norm = math.sqrt(sum(x*x for x in mock_vector))
        return [x/norm for x in mock_vector] if norm > 0 else [0.0]*768
        
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.embed_content(
            model="models/gemini-embedding-2",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"[RAG] Error generating Gemini embedding: {e}")
        # Dynamic fallback
        return [0.0] * 3072

# Parse PDF text
def extract_text_from_pdf(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text
    except Exception as e:
        print(f"[RAG] PDF Extraction failed: {e}")
        return ""

# Split text into overlapping chunks
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    chunks = []
    words = text.split()
    # Estimate characters using words (approx 5 chars per word)
    text_len = len(text)
    if text_len <= chunk_size:
        return [text] if text.strip() else []
        
    start = 0
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
        
    return chunks

# Store document and generate RAG index
def process_and_index_document(db: Session, course_id: int, file_name: str, file_path: str, document_type: str = "RAG_SOURCE") -> UploadedDocument:
    # 1. Create uploaded document record
    doc = UploadedDocument(
        course_id=course_id,
        file_name=file_name,
        file_path=file_path,
        document_type=document_type
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # 2. Extract text
    text = ""
    if file_name.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file_name.lower().endswith((".txt", ".md")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            text = ""
    else:
        text = f"Simulated content for document: {file_name}"
        
    # 3. Chunk text
    chunks = chunk_text(text)
    
    # 4. Generate embeddings and save
    for idx, chunk in enumerate(chunks):
        vector = get_embedding(chunk)
        embedding_record = Embedding(
            document_id=doc.id,
            chunk_text=chunk,
            embedding=vector  # Stored as JSON list of floats
        )
        db.add(embedding_record)
        
    db.commit()
    return doc

# Calculate cosine similarity
def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if len(v1) != len(v2) or not v1 or not v2:
        return 0.0
    dot = sum(a*b for a, b in zip(v1, v2))
    sum1 = sum(a*a for a in v1)
    sum2 = sum(b*b for b in v2)
    denom = math.sqrt(sum1) * math.sqrt(sum2)
    return dot / denom if denom > 0 else 0.0

# Retrieve relevant chunks for course
def retrieve_relevant_chunks(db: Session, course_id: int, query: str, limit: int = 4) -> List[Dict[str, Any]]:
    # Generate query embedding
    query_vector = get_embedding(query)
    
    # Get all documents belonging to this course
    docs = db.query(UploadedDocument).filter(UploadedDocument.course_id == course_id).all()
    if not docs:
        return []
        
    doc_ids = [d.id for d in docs]
    
    # Fetch all chunks
    all_embeddings = db.query(Embedding).filter(Embedding.document_id.in_(doc_ids)).all()
    
    # Run in-memory cosine similarity (dual fallback Postgres mapping & SQLite matching)
    results = []
    for item in all_embeddings:
        # DB embeddings might be loaded as JSON-deserialized list or JSON string depending on sqlite driver
        vector = item.embedding
        if isinstance(vector, str):
            try:
                vector = json.loads(vector)
            except Exception:
                continue
                
        similarity = cosine_similarity(query_vector, vector)
        results.append({
            "chunk_text": item.chunk_text,
            "similarity": similarity,
            "document_id": item.document_id
        })
        
    # Sort by similarity descending
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:limit]
