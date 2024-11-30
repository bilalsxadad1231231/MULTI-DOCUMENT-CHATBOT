from langchain.text_splitter import CharacterTextSplitter
from fastapi import HTTPException
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.document_loaders import TextLoader, PDFMinerLoader
from langchain.vectorstores import Chroma
import chromadb
import os


class DocumentProcessor:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        self.vec_database_path = "vec-database"
        
        # Ensure vector database directory exists
        os.makedirs(self.vec_database_path, exist_ok=True)
        
        # Initialize Chroma client
        self.chroma_client = chromadb.PersistentClient(path=self.vec_database_path)
    
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
        
        # Create or load Chroma collection
        collection_name = f"{username}_{chatbot_name}".replace(" ", "_").lower()
        
        try:
            # Try to get existing collection
            collection = self.chroma_client.get_collection(name=collection_name)
            print(f"Existing collection {collection_name} found. Adding new documents.")
        except Exception:
            # Create new collection if it doesn't exist
            collection = self.chroma_client.create_collection(name=collection_name)
            print(f"Created new collection {collection_name}")
        
        # Create Chroma vector store
        vectorstore = Chroma(
            client=self.chroma_client,
            collection_name=collection_name,
            embedding_function=self.embedding_model
        )
        
        # Add documents to the vector store without additional metadata
        vectorstore.add_documents(texts)
        
        return collection_name

    def retrieve_collection(self, username: str, chatbot_name: str):
        """
        Retrieve a Chroma retriever for a specific collection
        
        Args:
            username (str): Username of the chatbot owner
            chatbot_name (str): Name of the chatbot
        
        Returns:
            ChromaRetriever: A retriever for the specified collection
        """
        # Generate collection name
        collection_name = f"{username}_{chatbot_name}".replace(" ", "_").lower()
        
        try:
            # Create Chroma vector store
            vectorstore = Chroma(
                client=self.chroma_client,
                collection_name=collection_name,
                embedding_function=self.embedding_model
            )
            
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
                detail=f"Collection retrieval failed: {str(e)}"
            )
