import os
import tempfile
import pickle
import streamlit as st
from chat_utils import generate_response
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
import io

# Text storage paths (simplified without embeddings for now)
ADMIN_TEXTS_PATH = "admin_texts.pkl"
SHOP_TEXTS_PATH = "shop_texts.pkl"

def initialize_vector_store():
    """Initialize text storage files if they don't exist."""
    # Initialize admin text storage
    if not os.path.exists(ADMIN_TEXTS_PATH):
        with open(ADMIN_TEXTS_PATH, 'wb') as f:
            pickle.dump([], f)
    
    # Initialize shop text storage
    if not os.path.exists(SHOP_TEXTS_PATH):
        with open(SHOP_TEXTS_PATH, 'wb') as f:
            pickle.dump([], f)

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file."""
    try:
        if PyPDF2 is None:
            raise Exception("PyPDF2 not available. Please upload text files instead.")
        
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def chunk_text(text, chunk_size=1000, overlap=100):
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
    
    return chunks

def upload_and_process_document(uploaded_file, doc_type):
    """
    Process uploaded document and add to text storage.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        doc_type: 'admin' or 'shop'
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract text based on file type
        if uploaded_file.type == "application/pdf":
            if PyPDF2 is None:
                st.error("PDF support is not available. Please upload text files instead.")
                return False
            text = extract_text_from_pdf(uploaded_file)
        else:  # text file
            text = str(uploaded_file.read(), "utf-8")
        
        if not text.strip():
            st.error("No text content found in the uploaded file.")
            return False
        
        # Chunk the text
        chunks = chunk_text(text)
        
        if not chunks:
            st.error("Could not create text chunks from the document.")
            return False
        
        # Load existing texts and add new ones
        texts_path = ADMIN_TEXTS_PATH if doc_type == "admin" else SHOP_TEXTS_PATH
        
        with open(texts_path, 'rb') as f:
            existing_texts = pickle.load(f)
        
        # Add new texts to list
        existing_texts.extend(chunks)
        
        # Save updated texts
        with open(texts_path, 'wb') as f:
            pickle.dump(existing_texts, f)
        
        return True
    
    except Exception as e:
        st.error(f"Error processing document: {str(e)}")
        return False

def query_knowledge_base(query, doc_type, top_k=3):
    """
    Query the knowledge base and return relevant response using simple text matching.
    
    Args:
        query: User's question
        doc_type: 'admin' or 'shop'
        top_k: Number of chunks to include in context (simplified)
    
    Returns:
        Generated response
    """
    try:
        # Get texts path based on doc_type
        texts_path = ADMIN_TEXTS_PATH if doc_type == "admin" else SHOP_TEXTS_PATH
        
        # Load texts
        if not os.path.exists(texts_path):
            return "No knowledge base found. Please upload documents first."
        
        with open(texts_path, 'rb') as f:
            texts = pickle.load(f)
        
        if not texts:
            return "Knowledge base is empty. Please upload documents first."
        
        # Simple keyword-based matching - find chunks that contain query terms
        query_words = query.lower().split()
        relevant_chunks = []
        
        for text in texts:
            text_lower = text.lower()
            # Count how many query words appear in this text chunk
            matches = sum(1 for word in query_words if word in text_lower)
            if matches > 0:
                relevant_chunks.append((text, matches))
        
        # Sort by relevance (number of matching words) and take top chunks
        relevant_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = [chunk[0] for chunk in relevant_chunks[:top_k]]
        
        # If no relevant chunks found, use all text (truncated)
        if not top_chunks:
            # Take first few chunks if no keyword matches
            context = "\n\n".join(texts[:2])
        else:
            context = "\n\n".join(top_chunks)
        
        if not context.strip():
            return "I don't have information about that in the knowledge base."
        
        # Generate response using Gemini
        if doc_type == "admin":
            system_instruction = "You are an MSME compliance and guidance expert. Use the provided context to answer questions about MSME laws, schemes, and compliance requirements. If the context doesn't contain relevant information, say so clearly."
        else:
            system_instruction = "You are a customer service assistant for a shop. Use the provided context to answer questions about products, services, and shop policies. If the context doesn't contain relevant information, say so clearly."
        
        response = generate_response(query, context, system_instruction)
        return response
    
    except Exception as e:
        return f"Error querying knowledge base: {str(e)}"
