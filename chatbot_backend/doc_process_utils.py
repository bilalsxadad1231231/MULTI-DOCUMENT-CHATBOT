from langchain.text_splitter import CharacterTextSplitter
from fastapi import HTTPException
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, PDFMinerLoader
from langchain_community.vectorstores import FAISS  # Use FAISS instead of Chroma
import os
from huggingface_hub import login

login(token="you huggin face access token")

class DocumentProcessor:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        self.vec_database_path = "vec-database"
        
        # Ensure vector database directory exists
        os.makedirs(self.vec_database_path, exist_ok=True)
    
    def load_document(self, file_path: str):
        if file_path.endswith('.txt'):
            loader = TextLoader(file_path)
        elif file_path.endswith('.pdf'):
            loader = PDFMinerLoader(file_path)
        else:
            raise ValueError("Unsupported file format")
        return loader.load()
    
    def process_document(self, file_path: str, username: str, chatbot_name: str):
        # Load and split documents
        documents = self.load_document(file_path)
        texts = self.text_splitter.split_documents(documents)
        
        # Create or load FAISS vector store
        collection_name = f"{username}_{chatbot_name}".replace(" ", "_").lower()
        faiss_index_path = os.path.join(self.vec_database_path, f"{collection_name}.faiss")
        
        if os.path.exists(faiss_index_path):
            # Load existing FAISS index
            vectorstore = FAISS.load_local(
                folder_path=self.vec_database_path,
                embeddings=self.embedding_model,
                index_name=collection_name
            )
            print(f"Existing FAISS index {collection_name} found. Adding new documents.")
        else:
            # Create new FAISS index
            vectorstore = FAISS.from_documents(
                documents=texts,
                embedding=self.embedding_model
            )
            print(f"Created new FAISS index {collection_name}")
        
        # Add new documents to the vector store
        vectorstore.add_documents(texts)
        
        # Save the updated FAISS index to disk
        vectorstore.save_local(
            folder_path=self.vec_database_path,
            index_name=collection_name
        )
        
        return collection_name

    def retrieve_collection(self, username: str, chatbot_name: str):
        """
        Retrieve a FAISS retriever for a specific collection
        
        Args:
            username (str): Username of the chatbot owner
            chatbot_name (str): Name of the chatbot
        
        Returns:
            FAISSRetriever: A retriever for the specified collection
        """
        # Generate collection name
        print("inside fiass 1")
        collection_name = f"{username}_{chatbot_name}".replace(" ", "_").lower()
        faiss_index_path = os.path.join(self.vec_database_path, f"{collection_name}.faiss")
        print("inside fiass 2")
        
        try:
            # Load FAISS index
            vectorstore = FAISS.load_local(
                folder_path=self.vec_database_path,
                embeddings=self.embedding_model,
                index_name=collection_name,
                allow_dangerous_deserialization=True
            )
            
            print("inside fiass 3")
            
            
            # Create and return a retriever
            return vectorstore.as_retriever(
                search_type="mmr",  # Maximum Marginal Relevance retrieval
                search_kwargs={
                    "k": 5,  # Number of documents to retrieve
                    "fetch_k": 10  # Number of documents to consider before filtering
                }
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=404, 
                detail=f"FAISS index retrieval failed: {str(e)}"
            )
            
        
