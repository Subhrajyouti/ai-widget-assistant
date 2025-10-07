from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage

# Load API key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()

# Allow frontend access (localhost, or your domain later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request schema
class ChatRequest(BaseModel):
    question: str
    context: dict

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Init Gemini LLM
        model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",   
            google_api_key=GEMINI_API_KEY,
        )

        # Build prompt
        system_prompt = """You are a helpful assistant for a flight booking website.
You MUST ONLY answer using the context provided.
If the answer is missing, reply: "I cannot find that information on this page."
Always include a short supporting expert from the context. Give only the answer. Not anything else.Always include a short supporting excerpt from the context"""

        user_prompt = f"""
User question: {request.question}

Page context:
{str(request.context)[:12000]}  # limit to avoid oversized input
"""

        response = await model.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        return {"answer": response.content}
    except Exception as e:
        return {"error": str(e)}
