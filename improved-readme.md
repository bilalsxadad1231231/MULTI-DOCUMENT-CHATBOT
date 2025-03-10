# Multi-Document Chatbot

![Chat App Interface](/assets/chat app image.jpg)

![CI/CD Pipeline Completion](/assets/ci cd.jpg)

## Overview

Multi-Document Chatbot is an AI-powered application that enables users to interact with multiple documents simultaneously through natural language conversation. This innovative solution leverages the **Groq LLM** for fast, accurate response generation and **FAISS** (Facebook AI Similarity Search) as its vector database for efficient document indexing and retrieval.

## Key Features

- **Multi-document interaction**: Chat with multiple documents simultaneously
- **High-performance AI**: Powered by **Groq LLM** for lightning-fast response generation
- **Efficient retrieval**: Uses **FAISS** vector database for semantic search
- **Streamlit frontend**: Modern, interactive user interface
- **Containerized architecture**: Fully dockerized backend and frontend
- **Automated deployment**: CI/CD pipeline using GitHub Actions
- **Cloud-ready**: Optimized for AWS ECR deployment

## Technical Architecture

### Components

| Component | Technology | Description |
|-----------|------------|-------------|
| Frontend | Streamlit | Interactive web interface for document upload and chat interaction |
| Backend | FastAPI | RESTful API service in `backend.py` that processes requests |
| Vector Database | FAISS | Efficient similarity search for document chunks |
| LLM Provider | Groq | State-of-the-art language model for response generation |

### System Flow

1. Documents are uploaded, processed, and indexed in FAISS
2. User queries are vectorized and matched against document contents
3. Relevant document sections are retrieved and sent to Groq LLM
4. LLM generates contextual responses based on retrieved information
5. Responses are delivered to the user through the Streamlit chat interface

## Deployment

### Dockerization

Both the Streamlit frontend and FastAPI backend services are containerized using Docker for consistent environments across development and production.

### AWS ECR Deployment

The application is deployed to Amazon Elastic Container Registry (ECR) for reliable, scalable hosting:

1. Docker images are built and tagged
2. Images are pushed to private AWS ECR repositories
3. GitHub Actions automates the entire build and deployment workflow with separate pipelines for frontend and backend

## Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.8 or higher
- AWS CLI configured with appropriate permissions for ECR
- Groq API credentials

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/bilalsxadad1231231/MULTI-DOCUMENT-CHATBOT.git
   cd MULTI-DOCUMENT-CHATBOT
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Groq API key and other configurations
   ```

3. Build and run the backend:
   ```bash
   cd chatbot_backend
   docker build -t chatbot-backend .
   docker run -p 8000:8000 -v $(pwd)/data:/app/data --env-file ../.env chatbot-backend
   ```

4. Run the Streamlit frontend:
   ```bash
   cd chatbot_frontend
   docker build -t chatbot-frontend .
   docker run -p 8501:8501 --env-file ../.env chatbot-frontend
   ```

5. Access the application at `http://localhost:8501`

### Production Deployment

For production deployment, use the provided GitHub Actions workflows:

1. Configure AWS credentials in GitHub repository secrets
2. Push changes to the main branch to trigger automatic deployment
3. Monitor deployment progress in the Actions tab of your repository

## CI/CD Pipeline

The automated CI/CD pipeline consists of two separate workflows:

- **Backend Pipeline** (`.github/workflows/backend_image.yml`):
  - Builds and tests the FastAPI backend
  - Pushes the backend image to AWS ECR

- **Frontend Pipeline** (`.github/workflows/fronend-image.yml`):
  - Builds and tests the Streamlit frontend
  - Pushes the frontend image to AWS ECR

Triggers:
- Push to main branch
- Pull request against main branch (test build only)
- Manual workflow dispatch

## Project Structure

```
MULTI-DOCUMENT-CHATBOT/
├── .github/workflows/
│   ├── backend_image.yml
│   └── fronend-image.yml
├── assets/
│   ├── chat app image.jpg
│   ├── ci cd.jpg
│   └── test.txt
├── chatbot_backend/
│   ├── Dockerfile
│   ├── backend.py
│   ├── chat_client.py
│   ├── database_utils.py
│   ├── doc_process_utils.py
│   ├── memory_utils.py
│   ├── pydantic_class.py
│   ├── requirements.txt
│   └── validation_utils.py
├── chatbot_frontend/
│   ├── Dockerfile
│   ├── frontend.py (Streamlit app)
│   └── requirements.txt
├── LICENSE
├── LICENSE.txt
└── README.MD
```

## Usage Guide

1. **Start the application**: Ensure both backend and frontend containers are running
2. **Upload documents**: Supported formats include PDF, DOCX, TXT, and CSV
3. **Initiate chat**: Ask questions about your documents in natural language
4. **Review responses**: The system will cite sources from the relevant documents
5. **Export conversations**: Save your chat history for future reference

## Backend Services

The backend consists of several utility modules:
- `backend.py` - Main FastAPI application
- `chat_client.py` - Interface with Groq LLM
- `database_utils.py` - FAISS database operations
- `doc_process_utils.py` - Document parsing and preprocessing
- `memory_utils.py` - Conversation history management
- `pydantic_class.py` - Data models
- `validation_utils.py` - Input validation

## Frontend Features

The Streamlit frontend provides:
- Document upload interface
- Interactive chat window
- Document visualization
- Response history tracking
- User settings management

## Troubleshooting

- **Connection issues**: Ensure proper network configuration and API key setup
- **Indexing errors**: Check document format compatibility
- **Slow responses**: Adjust chunk size parameters for optimal performance

## License

This project is licensed under the MIT License - see the LICENSE files for details.

## Acknowledgements

- Groq team for providing the LLM API
- FAISS library developers at Facebook Research
- Streamlit and FastAPI framework contributors
