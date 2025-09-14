from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import (
  ChatPromptTemplate,
  HumanMessagePromptTemplate,
  SystemMessagePromptTemplate,
  MessagesPlaceholder)

from langchain.memory import ConversationBufferMemory
# from langchain.chains import LLMChain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from dotenv import load_dotenv

load_dotenv()


# ----- backend -----
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os

google_api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro",api_key=google_api_key)

prompts = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("""You are a friendly Indian tourism expert for a Smart India Hackathon (SIH) project.  
    Your role: guide travelers about India’s rich heritage, culture, food, and adventure.  

    🎯 Rules:
    - Always give authentic and useful information (real places, culture, festivals, foods, etc).  
    - Personalize suggestions based on user’s interests (heritage, nature, beaches, spirituality, trekking, festivals).  
    - Keep answers *very short and concise*: 2–4 lines per point, maximum 3–4 bullet points.  
    - Add relevant emojis to make the chat lively 🇮🇳✨  
    - End every answer with *one short follow-up question* to continue the conversation.  
    - If user asks something unrelated to tourism, politely bring the conversation back to Indian travel & culture.  
  """),
    MessagesPlaceholder("chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

chain = prompts | llm

store = {}

def get_session_id(session_id:str):
  if session_id not in store:
    store[session_id] = ChatMessageHistory()
  return store[session_id]


runnable_message_history = RunnableWithMessageHistory(
  chain,
  get_session_id,
  input_messages_key="input",
  history_messages_key="chat_history"
)



# ----- BACKEND ---
app = FastAPI(title='Tourism Chatbot API')

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True, 
  allow_methods=["*"],
  allow_headers=["*"],
)


# ----- Pydantic ----
class ChatRequest(BaseModel):
  message : str
  session_id : Optional[str] = "user_123"

class ChatResponse(BaseModel):
  reply : str
  session_id : str




@app.post("/chat",response_model=ChatResponse)
async def chat_endpoint(payload:ChatRequest):
  session_id = payload.session_id or str(uuid.uuid4())
  user_input = payload.message

  response = runnable_message_history.invoke(
    {"input":user_input},
    config={"configurable":{"session_id":session_id}}
  )
  
  return ChatResponse(reply=response.content, session_id=session_id)
