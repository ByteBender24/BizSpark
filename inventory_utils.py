import pandas as pd
import sqlite3
import io
import streamlit as st
from chat_utils import generate_inventory_response, analyze_csv_schema

# Database connection
DATABASE_PATH = "inventory.db"

def get_db_connection():
    """Get SQLite database connection."""
    return sqlite3.connect(DATABASE_PATH)

def get_inventory_data():
    """
    Retrieve inventory data from database.
    
    Returns:
        pandas.DataFrame: Inventory data
    """
    try:
        conn = get_db_connection()
        df = pd.read_sql_query(
            "SELECT id, product_name, quantity, unit_price, category, description FROM inventory ORDER BY product_name", 
            conn
        )
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error retrieving inventory data: {str(e)}")
        return pd.DataFrame()

def update_inventory_data(df):
    """
    Update inventory data in database.
    
    Args:
        df: pandas.DataFrame with inventory data
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM inventory")
        
        # Insert new data
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO inventory (product_name, quantity, unit_price, category, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row.get('product_name', ''),
                row.get('quantity', 0),
                row.get('unit_price', 0.0),
                row.get('category', ''),
                row.get('description', '')
            ))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        st.error(f"Error updating inventory: {str(e)}")
        return False

def import_inventory_csv(uploaded_file):
    """
    Import inventory data from CSV file.
    
    Args:
        uploaded_file: Streamlit uploaded file object
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)
        
        # Show CSV analysis
        csv_content = uploaded_file.getvalue().decode('utf-8')
        analysis = analyze_csv_schema(csv_content)
        
        with st.expander("📊 CSV Analysis & Suggestions"):
            st.write(analysis)
        
        # Standardize column names
        column_mapping = {
            'product': 'product_name',
            'name': 'product_name',
            'item': 'product_name',
            'qty': 'quantity',
            'stock': 'quantity',
            'price': 'unit_price',
            'cost': 'unit_price',
            'type': 'category',
            'desc': 'description',
            'details': 'description'
        }
        
        # Rename columns to standard format
        df.columns = df.columns.str.lower().str.strip()
        df.rename(columns=column_mapping, inplace=True)
        
        # Ensure required columns exist
        required_columns = ['product_name', 'quantity', 'unit_price', 'category', 'description']
        for col in required_columns:
            if col not in df.columns:
                if col in ['quantity', 'unit_price']:
                    df[col] = 0
                else:
                    df[col] = ''
        
        # Clean and validate data
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        df['quantity'] = df['quantity'].fillna(0)
        df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
        df['unit_price'] = df['unit_price'].fillna(0.0)
        df['product_name'] = df['product_name'].astype(str).fillna('')
        df['category'] = df['category'].astype(str).fillna('')
        df['description'] = df['description'].astype(str).fillna('')
        
        # Remove empty product names
        df = df[df['product_name'].str.strip() != '']
        
        if df.empty:
            st.error("No valid inventory data found in CSV.")
            return False
        
        # Update database
        return update_inventory_data(df[required_columns])
    
    except Exception as e:
        st.error(f"Error importing CSV: {str(e)}")
        return False

def export_inventory_csv():
    """
    Export inventory data as CSV.
    
    Returns:
        str: CSV data as string
    """
    try:
        df = get_inventory_data()
        if df.empty:
            return None
        
        # Remove ID column for export
        export_df = df.drop('id', axis=1, errors='ignore')
        
        # Convert to CSV
        output = io.StringIO()
        export_df.to_csv(output, index=False)
        return output.getvalue()
    
    except Exception as e:
        st.error(f"Error exporting inventory: {str(e)}")
        return None

def query_inventory_chatbot(query):
    """
    Handle inventory chatbot queries.
    
    Args:
        query: User's inventory-related question
    
    Returns:
        str: Response to the query
    """
    try:
        # Get current inventory data
        df = get_inventory_data()
        
        if df.empty:
            return "Your inventory is currently empty. You can add items using the inventory management interface or by uploading a CSV file."
        
        # Convert dataframe to string format for context
        inventory_summary = df.to_string(index=False)
        
        # Check if this is a modification request
        modification_keywords = ['add', 'remove', 'delete', 'update', 'increase', 'decrease', 'set']
        is_modification = any(keyword in query.lower() for keyword in modification_keywords)
        
        if is_modification:
            response = generate_inventory_response(query, inventory_summary)
            response += "\n\n⚠️ **Note:** To actually make changes to your inventory, please use the Inventory Management interface or upload a new CSV file. I can only provide information and suggestions."
            return response
        else:
            # Information query
            return generate_inventory_response(query, inventory_summary)
    
    except Exception as e:
        return f"Error processing inventory query: {str(e)}"

def search_product(product_name):
    """
    Search for a specific product in inventory.
    
    Args:
        product_name: Name of the product to search for
    
    Returns:
        dict: Product information or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT product_name, quantity, unit_price, category, description
            FROM inventory
            WHERE product_name LIKE ?
        """, (f"%{product_name}%",))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'product_name': result[0],
                'quantity': result[1],
                'unit_price': result[2],
                'category': result[3],
                'description': result[4]
            }
        else:
            return None
    
    except Exception as e:
        st.error(f"Error searching product: {str(e)}")
        return None
