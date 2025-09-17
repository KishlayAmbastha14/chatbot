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
import json
import os
import tempfile
from google.oauth2 import service_account


# GOOGLE_APPLICATION_CREDENTIALS_JSON
# def setup_google_credentials():
#     creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
#     if not creds_json:
#         raise RuntimeError("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON not set!")

#     # Cross-platform temp file location
#     temp_dir = tempfile.gettempdir()  
#     temp_path = os.path.join(temp_dir, "adc.json")

#     with open(temp_path, "w") as f:
#         f.write(creds_json)

#     # Tell Google SDK to use this file
#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path

# setup_google_credentials()
# google_api_key = os.getenv("GOOGLE_API_KEY")


import base64
from google.oauth2 import service_account


# Decode the JSON from Base64
service_account_info = json.loads(base64.b64decode(os.environ["GOOGLE_APPLICATION_CREDENTIALS_BASE64"]))
credentials = service_account.Credentials.from_service_account_info(service_account_info)

# Pass credentials to the model
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", credentials=credentials)


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
