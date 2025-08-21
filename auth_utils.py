import streamlit as st
import os

def authenticate_user(token):
    """
    Authenticate user based on token and return user role.
    Returns 'Admin' or 'Shop Owner' if valid, None if invalid.
    """
    # Get tokens from secrets/environment
    admin_token = st.secrets.get("ADMIN_TOKEN", os.getenv("ADMIN_TOKEN", "admin_token_123"))
    
    # Shop tokens can be multiple - stored as comma-separated string
    shop_tokens_str = st.secrets.get("SHOP_TOKENS", os.getenv("SHOP_TOKENS", "shop_token_1,shop_token_2,shop_token_3"))
    shop_tokens = [token.strip() for token in shop_tokens_str.split(",")]
    
    if token == admin_token:
        return "Admin"
    elif token in shop_tokens:
        return "Shop Owner"
    else:
        return None

def get_user_role():
    """Get current user role from session state."""
    return st.session_state.get("user_role", None)

def is_admin():
    """Check if current user is admin."""
    return get_user_role() == "Admin"

def is_shop_owner():
    """Check if current user is shop owner."""
    return get_user_role() == "Shop Owner"
