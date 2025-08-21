import os
from google import genai
from google.genai import types
import streamlit as st

# Initialize Gemini client
@st.cache_resource
def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "default_key"))
    return genai.Client(api_key=api_key)

def generate_response(prompt, context="", system_instruction=""):
    """
    Generate response using Google Gemini API.
    
    Args:
        prompt: User's question/input
        context: Additional context for the response
        system_instruction: System instruction for the model
    
    Returns:
        Generated response text
    """
    try:
        client = get_gemini_client()
        
        # Construct the full prompt with context
        if context:
            full_prompt = f"Context: {context}\n\nQuestion: {prompt}"
        else:
            full_prompt = prompt
        
        # Generate response
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(role="user", parts=[types.Part(text=full_prompt)])
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction if system_instruction else 
                "You are a helpful assistant for MSME businesses. Provide accurate, concise, and actionable responses."
            )
        )
        
        return response.text if response.text else "I'm sorry, I couldn't generate a response."
    
    except Exception as e:
        return f"Error generating response: {str(e)}"

def analyze_csv_schema(csv_content):
    """
    Use Gemini to analyze and suggest improvements for CSV schema.
    
    Args:
        csv_content: String content of the CSV
    
    Returns:
        Analysis and suggestions
    """
    try:
        client = get_gemini_client()
        
        prompt = f"""
        Analyze this CSV data for an MSME inventory system and provide:
        1. Schema validation
        2. Data quality issues
        3. Suggestions for improvement
        4. Missing columns that might be useful
        
        CSV Content:
        {csv_content[:1000]}...  # First 1000 chars
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are a data analysis expert specializing in MSME inventory management systems."
            )
        )
        
        return response.text if response.text else "Could not analyze CSV schema."
    
    except Exception as e:
        return f"Error analyzing CSV: {str(e)}"

def generate_inventory_response(query, inventory_data):
    """
    Generate response for inventory-related queries.
    
    Args:
        query: User's inventory question
        inventory_data: Current inventory data as string
    
    Returns:
        Response about inventory
    """
    try:
        client = get_gemini_client()
        
        prompt = f"""
        Based on this inventory data, answer the user's question:
        
        Inventory Data:
        {inventory_data}
        
        User Question: {query}
        
        If the user is asking to add/remove/update items, provide clear confirmation of what action should be taken.
        If asking about stock levels, provide specific numbers and product details.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are an inventory management assistant for MSME businesses. Provide precise, actionable responses about inventory operations."
            )
        )
        
        return response.text if response.text else "Could not process inventory query."
    
    except Exception as e:
        return f"Error processing inventory query: {str(e)}"
