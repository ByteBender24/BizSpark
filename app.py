import streamlit as st
import pandas as pd
import os
from auth_utils import authenticate_user, get_user_role
from rag_utils import (
    upload_and_process_document, 
    query_knowledge_base, 
    initialize_vector_store
)
from inventory_utils import (
    get_inventory_data, 
    update_inventory_data, 
    import_inventory_csv, 
    export_inventory_csv,
    query_inventory_chatbot
)
from chat_utils import generate_response
from database_init import initialize_database

# Initialize database and vector store on startup
@st.cache_resource
def initialize_app():
    initialize_database()
    initialize_vector_store()
    return True

# Page configuration
st.set_page_config(
    page_title="MSME Business Management Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Initialize app
    initialize_app()
    
    # Authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_token = None
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_app()

def show_login_page():
    st.title("🏢 MSME Business Management Platform")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Login")
        token = st.text_input("Enter your access token:", type="password")
        
        if st.button("Login", type="primary"):
            user_role = authenticate_user(token)
            if user_role:
                st.session_state.authenticated = True
                st.session_state.user_role = user_role
                st.session_state.user_token = token
                st.rerun()
            else:
                st.error("Invalid token. Please try again.")
        
        st.markdown("---")
        st.info("**Roles:**\n- Admin: Manage MSME compliance docs\n- Shop Owner: Manage inventory and shop knowledge base")

def show_main_app():
    # Sidebar navigation
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.user_role}!")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.user_token = None
            st.rerun()
        
        st.markdown("---")
        
        # Navigation based on role
        if st.session_state.user_role == "Admin":
            page = st.selectbox(
                "Navigate to:",
                ["Admin Knowledge Base", "Admin Chatbot"]
            )
        else:  # Shop Owner
            page = st.selectbox(
                "Navigate to:",
                ["Inventory Management", "Shop Knowledge Base", "Customer Chatbot", "Inventory Chatbot", "MSME Guidance"]
            )
    
    # Main content based on selected page
    if page == "Admin Knowledge Base":
        show_admin_knowledge_base()
    elif page == "Admin Chatbot":
        show_admin_chatbot()
    elif page == "Inventory Management":
        show_inventory_management()
    elif page == "Shop Knowledge Base":
        show_shop_knowledge_base()
    elif page == "Customer Chatbot":
        show_customer_chatbot()
    elif page == "Inventory Chatbot":
        show_inventory_chatbot()
    elif page == "MSME Guidance":
        show_msme_guidance()

def show_admin_knowledge_base():
    st.title("📚 Admin Knowledge Base Management")
    st.markdown("Upload MSME-related documents (laws, compliance, schemes)")
    
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=['txt', 'pdf'],
        help="Upload text files or PDFs containing MSME guidance"
    )
    
    if uploaded_file is not None:
        if st.button("Process Document", type="primary"):
            with st.spinner("Processing document..."):
                try:
                    result = upload_and_process_document(uploaded_file, "admin")
                    if result:
                        st.success("Document processed and added to knowledge base!")
                    else:
                        st.error("Failed to process document.")
                except Exception as e:
                    st.error(f"Error processing document: {str(e)}")

def show_admin_chatbot():
    st.title("🤖 Admin Knowledge Chatbot")
    st.markdown("Test the MSME guidance knowledge base")
    
    if "admin_chat_history" not in st.session_state:
        st.session_state.admin_chat_history = []
    
    # Display chat history
    for message in st.session_state.admin_chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about MSME laws, compliance, or schemes..."):
        # Add user message to history
        st.session_state.admin_chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = query_knowledge_base(prompt, "admin")
                    st.write(response)
                    st.session_state.admin_chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.write(error_msg)
                    st.session_state.admin_chat_history.append({"role": "assistant", "content": error_msg})

def show_inventory_management():
    st.title("📦 Inventory Management")
    
    # CSV Upload/Download section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Import Inventory")
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        
        if uploaded_file is not None:
            if st.button("Import CSV", type="primary"):
                with st.spinner("Importing data..."):
                    try:
                        result = import_inventory_csv(uploaded_file)
                        if result:
                            st.success("Inventory imported successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to import inventory.")
                    except Exception as e:
                        st.error(f"Import error: {str(e)}")
    
    with col2:
        st.subheader("Export Inventory")
        if st.button("Download Current Inventory", type="secondary"):
            try:
                csv_data = export_inventory_csv()
                if csv_data:
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name="inventory.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No inventory data to export.")
            except Exception as e:
                st.error(f"Export error: {str(e)}")
    
    st.markdown("---")
    
    # Inventory Editor
    st.subheader("📊 Inventory Editor")
    
    try:
        df = get_inventory_data()
        
        if df.empty:
            st.info("No inventory data found. Upload a CSV file or add items manually.")
            # Create empty dataframe with standard columns
            df = pd.DataFrame(columns=['product_name', 'quantity', 'unit_price', 'category', 'description'])
        
        # Editable dataframe
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "product_name": st.column_config.TextColumn("Product Name", required=True),
                "quantity": st.column_config.NumberColumn("Quantity", min_value=0),
                "unit_price": st.column_config.NumberColumn("Unit Price", min_value=0.0, format="$%.2f"),
                "category": st.column_config.TextColumn("Category"),
                "description": st.column_config.TextColumn("Description")
            }
        )
        
        if st.button("Save Changes", type="primary"):
            with st.spinner("Saving changes..."):
                try:
                    result = update_inventory_data(edited_df)
                    if result:
                        st.success("Inventory updated successfully!")
                    else:
                        st.error("Failed to update inventory.")
                except Exception as e:
                    st.error(f"Update error: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading inventory: {str(e)}")

def show_shop_knowledge_base():
    st.title("🏪 Shop Knowledge Base Management")
    st.markdown("Upload shop-specific documents (product info, FAQs, policies)")
    
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=['txt', 'pdf'],
        help="Upload documents about your shop, products, or services"
    )
    
    if uploaded_file is not None:
        if st.button("Process Document", type="primary"):
            with st.spinner("Processing document..."):
                try:
                    result = upload_and_process_document(uploaded_file, "shop")
                    if result:
                        st.success("Document processed and added to shop knowledge base!")
                    else:
                        st.error("Failed to process document.")
                except Exception as e:
                    st.error(f"Error processing document: {str(e)}")

def show_customer_chatbot():
    st.title("💬 Customer Support Chatbot")
    st.markdown("**Public-facing chatbot** - Answers customer questions based on your shop knowledge base")
    
    if "customer_chat_history" not in st.session_state:
        st.session_state.customer_chat_history = []
    
    # Display chat history
    for message in st.session_state.customer_chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about products, services, or shop information..."):
        # Add user message to history
        st.session_state.customer_chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = query_knowledge_base(prompt, "shop")
                    if not response or "I don't have information" in response:
                        response = "I'm sorry, I don't have specific information about that. Please contact the shop directly for more details."
                    st.write(response)
                    st.session_state.customer_chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = "I'm sorry, I'm having trouble accessing information right now. Please try again later."
                    st.write(error_msg)
                    st.session_state.customer_chat_history.append({"role": "assistant", "content": error_msg})

def show_inventory_chatbot():
    st.title("📦 Inventory Assistant")
    st.markdown("Ask questions about your inventory or request updates")
    
    if "inventory_chat_history" not in st.session_state:
        st.session_state.inventory_chat_history = []
    
    # Display chat history
    for message in st.session_state.inventory_chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about inventory or request updates (e.g., 'What's my stock of Product X?' or 'Add 10 items to Product Y')"):
        # Add user message to history
        st.session_state.inventory_chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display response
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                try:
                    response = query_inventory_chatbot(prompt)
                    st.write(response)
                    st.session_state.inventory_chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.write(error_msg)
                    st.session_state.inventory_chat_history.append({"role": "assistant", "content": error_msg})

def show_msme_guidance():
    st.title("🏛️ MSME Guidance & Compliance")
    st.markdown("Get guidance on MSME laws, schemes, and compliance requirements")
    
    if "msme_chat_history" not in st.session_state:
        st.session_state.msme_chat_history = []
    
    # Display chat history
    for message in st.session_state.msme_chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about MSME laws, compliance requirements, government schemes..."):
        # Add user message to history
        st.session_state.msme_chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display response
        with st.chat_message("assistant"):
            with st.spinner("Searching MSME knowledge base..."):
                try:
                    response = query_knowledge_base(prompt, "admin")
                    if not response or "I don't have information" in response:
                        response = "I don't have specific information about that in the MSME knowledge base. Please consult with an MSME advisor or check official government resources."
                    st.write(response)
                    st.session_state.msme_chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error accessing the MSME knowledge base: {str(e)}"
                    st.write(error_msg)
                    st.session_state.msme_chat_history.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()
