from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import huggingface_hub
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_community.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from passlib.context import CryptContext
from datetime import datetime, timedelta
import shutil
import uuid
import json
from pydantic_class import *
from database_utils import *
from validation_utils import *
from doc_process_utils import *
from memory_utils import *

# Constants
UPLOAD_DIR = "uploaded_documents"

# Create upload directory
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Database configuration

# FastAPI app instance
app = FastAPI(title="Chatbot API")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme

# Initialize database on startup
init_db()

        
# Document processing utilities
doc_processor = DocumentProcessor()

@app.post("/register", response_model=Token)
async def register(user: UserCreate):
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE username = ?", (user.username,)).fetchone():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        password_hash = pwd_context.hash(user.password)
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?) RETURNING id",
            (user.username, user.email, password_hash)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        
        access_token = create_access_token({"sub": user.username, "user_id": user_id})
        return Token(access_token=access_token, token_type="bearer")

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (form_data.username,)
        ).fetchone()
        
        if not user or not pwd_context.verify(form_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token({"sub": user["username"], "user_id": user["id"]})
        return Token(access_token=access_token, token_type="bearer")


@app.post("/chatbots", response_model=ChatbotResponse)
async def create_chatbot(
    name: str = Form(...),
    description: str = Form(...),
    persona_prompt: str = Form(...),
    document: UploadFile = File(...),
    token_data: dict = Depends(verify_token)
):
    user_id = token_data["user_id"]
    username = token_data["sub"]
    
    # Save uploaded file
    file_extension = document.filename.split('.')[-1]
    file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{uuid.uuid4()}.{file_extension}")
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(document.file, buffer)
        
        # Process document
        # doc_processor = DocumentProcessor()
        collection_name = doc_processor.process_document(
            file_path, 
            username, 
            name
        )
        
        with get_db() as conn:
            # Create chatbot
            cursor = conn.execute("""
                INSERT INTO chatbots (
                    user_id, 
                    name, 
                    description, 
                    persona_prompt
                )
                VALUES (?, ?, ?, ?) RETURNING id, created_at
            """, (user_id, name, description, persona_prompt))
            chatbot_id, created_at = cursor.fetchone()
            
            conn.commit()
            
            return ChatbotResponse(
                id=chatbot_id,
                name=name,
                description=description,
                persona_prompt=persona_prompt,
                created_at=created_at
            )
    except Exception as e:
        # Handle any errors during file processing or database insertion
        raise HTTPException(status_code=500, detail=f"Error creating chatbot: {str(e)}")
    finally:
        # Cleanup uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)


@app.get("/chatbots", response_model=List[ChatbotResponse])
async def get_chatbots(token_data: dict = Depends(verify_token)):
    with get_db() as conn:
        chatbots = conn.execute("""
            SELECT id, name, description, persona_prompt, created_at
            FROM chatbots
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (token_data["user_id"],)).fetchall()
        
        return [
            ChatbotResponse(
                id=chatbot["id"],
                name=chatbot["name"],
                description=chatbot["description"],
                persona_prompt=chatbot["persona_prompt"],
                created_at=chatbot["created_at"]
            )
            for chatbot in chatbots
        ]
    


# Global memory manager instance
chatbot_memory_manager = ChatbotMemoryManager()



@app.post("/chatbots/chat")
async def chat_with_chatbot(
    request: ChatRequest,
    token_data: dict = Depends(verify_token)
):
    # Convert chatbot_id to string for memory management
    chatbot_str_id = str(request.chatbot_name)
    username = token_data["sub"]

    try:
        # Retrieve chatbot details

        with get_db() as conn:
            chatbot = conn.execute("""
                SELECT name, description, persona_prompt
                FROM chatbots 
                WHERE name = ? AND user_id = (SELECT id FROM users WHERE username = ?)
            """, (chatbot_str_id, username)).fetchone()
        

        if not chatbot:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        
        # Initialize document processor and retriever
        # doc_processor = DocumentProcessor()
        retriever = doc_processor.retrieve_collection(username, chatbot['name'])
        
        # Initialize Hugging Face models
        # Note: Replace with your actual Hugging Face API key
        embedding_model = HuggingFaceInferenceAPIEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2", 
            api_key="Your hugging face access token"
        )
        
        llm = HuggingFaceHub(
            repo_id="Qwen/Qwen2.5-Coder-32B-Instruct",
            huggingfacehub_api_token = "Your hugging face access token",
            model_kwargs={"temperature": 0.7, "max_length": 1000}
        )
        
        # Retrieve existing memory or create new
        memory = chatbot_memory_manager.get_chatbot_memory(username, chatbot_str_id)
        
        
        # Custom prompt template to incorporate persona and context
# Custom prompt template to incorporate chatbot name, description, persona, and context
        prompt_template = PromptTemplate(
            input_variables=["chat_history", "question", "context"],
            template="""You are {chatbot_name}, {chatbot_description}

My Persona: {persona_prompt}

Context Documents: {context}

Chat History: {chat_history}

User Question: {question}

Respond as {chatbot_name}, providing a helpful, contextually relevant response that reflects my unique personality and knowledge:""",
    partial_variables={
        "chatbot_name": chatbot['name'],
        "chatbot_description": chatbot['description'],
        "persona_prompt": chatbot['persona_prompt']
    }
)
        # Create Conversational Retrieval Chain
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            verbose=True,
            return_source_documents=False,
            combine_docs_chain_kwargs={
                "prompt": prompt_template
            }
        )
        result = conversation_chain.invoke({"question": request.message})
        response = result['answer']
        response = response.split("persona-consistent response:")[-1].strip()
        chatbot_memory_manager.get_user_memory_manager(username).save_memory(chatbot_str_id)
        
        return {
            "response": response
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")