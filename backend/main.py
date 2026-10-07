import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import process_query

app = FastAPI(
    title="Employee AI Database Agent",
    description="FastAPI service backed by LangGraph and Supabase",
    version="1.0.0"
)

# Enable CORS for frontend integration (both local Vite and deployed Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
def health_check():
    """Root endpoint for status check and deployment health verification."""
    return {"status": "ok", "service": "Employee DB AI Agent Backend"}

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """Processes natural language requests, delegating to LangGraph and Supabase."""
    cleaned_message = request.message.strip()
    if not cleaned_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    try:
        reply = process_query(cleaned_message)
        return ChatResponse(response=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0 is required for containerized environments and Render
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
