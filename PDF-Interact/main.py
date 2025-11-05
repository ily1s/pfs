from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chat_logic import process_pdf, generate_response
import os

# Configuration
PDF_STORAGE_PATH = "store/"
os.makedirs(PDF_STORAGE_PATH, exist_ok=True)

app = FastAPI(title="DocuMind AI - PDF Chat API")

# CORS middleware (allowing all for dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set specific origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint: Upload PDF and process it
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    file_path = os.path.join(PDF_STORAGE_PATH, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        process_pdf(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": f"{file.filename} processed successfully."}

# Request schema for chat
class ChatRequest(BaseModel):
    question: str
    history: list  # List of {"role": str, "content": str}

# Endpoint: Chat interaction
@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        answer = generate_response(req.question, req.history)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@app.get("/")
def read_root():
    return {"message": "DocuMind AI API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
