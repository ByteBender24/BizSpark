# Overview

This is an MSME (Micro, Small & Medium Enterprise) Business Management Platform built with Streamlit. The application provides role-based access control for Admins and Shop Owners, featuring inventory management capabilities, document-based knowledge retrieval using RAG (Retrieval-Augmented Generation), and AI-powered chat assistance. The platform enables businesses to manage their inventory through CRUD operations, upload and query documents for knowledge management, and interact with AI chatbots for business assistance.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit web application framework
- **Layout**: Wide layout with expandable sidebar for navigation
- **Authentication**: Token-based authentication with role-based access control
- **Session Management**: Streamlit session state for user authentication and role persistence

## Backend Architecture
- **Application Structure**: Modular design with separate utility modules for different functionalities
- **Core Modules**:
  - `auth_utils.py`: Authentication and authorization logic
  - `inventory_utils.py`: Inventory management operations
  - `rag_utils.py`: Document processing and knowledge retrieval
  - `chat_utils.py`: AI chat functionality
  - `database_init.py`: Database initialization and schema setup

## Data Storage Solutions
- **Primary Database**: SQLite for inventory management
  - Single table design with auto-incrementing primary keys
  - Indexed product names for optimized search performance
  - Timestamp tracking for creation and updates
- **Vector Storage**: FAISS (Facebook AI Similarity Search) for document embeddings
  - Separate vector stores for Admin and Shop Owner roles
  - Persistent storage using pickle for text chunks
  - Flat L2 distance indexing for similarity search

## Authentication and Authorization
- **Token-based Authentication**: Simple token validation system
- **Role-based Access Control**: Two distinct roles (Admin and Shop Owner)
- **Configuration**: Environment variables and Streamlit secrets for token management
- **Session Persistence**: Authentication state maintained in Streamlit session

## AI and Machine Learning Components
- **Embedding Model**: SentenceTransformers 'all-MiniLM-L6-v2' for text vectorization
- **Language Model**: Google Gemini 2.5 Flash for response generation
- **RAG Implementation**: Custom retrieval-augmented generation for document queries
- **Document Processing**: PDF text extraction using PyPDF2

## Data Processing Pipeline
- **Inventory Management**: CSV import/export functionality with schema validation
- **Document Processing**: PDF text extraction and chunk-based indexing
- **Vector Search**: Similarity-based document retrieval for contextual responses

# External Dependencies

## AI Services
- **Google Gemini API**: Primary language model for chat responses and business assistance
- **SentenceTransformers**: Hugging Face model for text embeddings and similarity search

## Data Processing Libraries
- **pandas**: Data manipulation and CSV operations for inventory management
- **PyPDF2**: PDF document parsing and text extraction
- **FAISS**: Vector similarity search and indexing
- **numpy**: Numerical operations for vector computations

## Database and Storage
- **SQLite**: Embedded database for inventory data persistence
- **pickle**: Python object serialization for vector store text storage

## Web Framework
- **Streamlit**: Complete web application framework with built-in session management and secrets handling

## Configuration Management
- **Environment Variables**: Token configuration and API key management
- **Streamlit Secrets**: Secure configuration storage for production deployment