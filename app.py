# app.py
import os
import streamlit as st
import pandas as pd
import google.generativeai as genai

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="MSME AI Assistant", layout="wide")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Ensure docs folder exists
DOCS_DIR = "docs"
os.makedirs(DOCS_DIR, exist_ok=True)

# Initialize session state
if "inventory" not in st.session_state:
    st.session_state["inventory"] = pd.DataFrame(
        columns=["Product Name", "Quantity", "Price", "Category"]
    )

# Gemini helper
def ask_gemini(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text if response else "⚠️ No response from Gemini."

# Helper: Read all docs from folder
def load_docs():
    texts = []
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".txt"):
            with open(os.path.join(DOCS_DIR, filename), "r", encoding="utf-8") as f:
                texts.append(f.read())
    return "\n\n".join(texts) if texts else "No shop info uploaded yet."


# ----------------------------
# SIDEBAR NAVIGATION
# ----------------------------
st.sidebar.title("📌 MSME AI Platform")
page = st.sidebar.radio(
    "Choose Section",
    ["🏪 Customer Chatbot", "🛠️ Owner Dashboard", "📂 Docs Manager", "📊 Insights"],
)


# ----------------------------
# CUSTOMER CHATBOT
# ----------------------------
if page == "🏪 Customer Chatbot":
    st.title("🏪 Customer Chatbot")
    st.write("Ask me about this shop’s products and services!")

    if "cust_chat" not in st.session_state:
        st.session_state["cust_chat"] = []

    for msg in st.session_state["cust_chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["text"])

    query = st.chat_input("Type your question here...")
    if query:
        st.session_state["cust_chat"].append({"role": "user", "text": query})

        context = load_docs()
        prompt = f"""You are a helpful assistant for a shop.
Shop Information:
{context}

Customer Question:
{query}

Answer in a simple and clear way.
"""
        answer = ask_gemini(prompt)

        st.session_state["cust_chat"].append({"role": "assistant", "text": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)


# ----------------------------
# OWNER DASHBOARD
# ----------------------------
elif page == "🛠️ Owner Dashboard":
    st.title("🛠️ Owner Dashboard")

    tabs = st.tabs(["💬 Chat with Documents", "📦 Inventory Manager"])

    # --- Owner chat with documents ---
    with tabs[0]:
        st.subheader("💬 Chat with your uploaded documents")

        if "owner_chat" not in st.session_state:
            st.session_state["owner_chat"] = []

        for msg in st.session_state["owner_chat"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["text"])

        query = st.chat_input("Ask about your documents...")
        if query:
            st.session_state["owner_chat"].append({"role": "user", "text": query})

            context = load_docs()
            prompt = f"""You are an assistant helping the shop owner.
Here are their uploaded documents:
{context}

Owner Question:
{query}

Give clear and useful answers.
"""
            answer = ask_gemini(prompt)

            st.session_state["owner_chat"].append({"role": "assistant", "text": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)

    # --- Inventory Manager ---
    # ----------------------------
    # INVENTORY MANAGER
    # ----------------------------
    INV_FILE = os.path.join(DOCS_DIR, "inventory.csv")

    # Load inventory from CSV at startup
    if os.path.exists(INV_FILE) and "inventory" not in st.session_state:
        st.session_state["inventory"] = pd.read_csv(INV_FILE)
    elif "inventory" not in st.session_state:
        st.session_state["inventory"] = pd.DataFrame(
            columns=["Product Name", "Quantity", "Price", "Category"]
        )

    with tabs[1]:
        st.subheader("📦 Inventory Manager")

        uploaded_csv = st.file_uploader("Upload inventory CSV", type=["csv"])
        if uploaded_csv:
            st.session_state["inventory"] = pd.read_csv(uploaded_csv)
            st.session_state["inventory"].to_csv(INV_FILE, index=False)  # Save immediately
            st.success("✅ Inventory loaded and saved!")

        # Editable table
        st.session_state["inventory"] = st.data_editor(
            st.session_state["inventory"],
            num_rows="dynamic",
            use_container_width=True,
        )

        # Save button → persist changes
        if st.button("💾 Save Changes"):
            st.session_state["inventory"].to_csv(INV_FILE, index=False)
            st.success("✅ Inventory saved to storage!")

        st.download_button(
            "⬇️ Download Inventory CSV",
            data=st.session_state["inventory"].to_csv(index=False),
            file_name="inventory.csv",
            mime="text/csv",
        )

        st.write("### 💬 Ask about or update your inventory")
        if "inv_chat" not in st.session_state:
            st.session_state["inv_chat"] = []

        for msg in st.session_state["inv_chat"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["text"])

        query = st.chat_input("E.g., 'Add 10 Laptops at $800 in Electronics'")
        if query:
            st.session_state["inv_chat"].append({"role": "user", "text": query})

            inventory_text = st.session_state["inventory"].to_string(index=False)
            prompt = f"""You are an assistant for inventory management.

    Here is the current inventory table:
    {inventory_text}

    Owner Request:
    {query}

    If updates are requested (add, remove, update quantity/price/category),
    output clear **step-by-step instructions** of what to change in the table.
    """
            answer = ask_gemini(prompt)

            # Append assistant response
            st.session_state["inv_chat"].append({"role": "assistant", "text": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)

            # --- Parse changes (very simple example) ---
            if "add" in query.lower():
                # crude parsing example: "Add 10 Laptops at $800 in Electronics"
                try:
                    words = query.split()
                    qty = int([w for w in words if w.isdigit()][0])
                    name = next(w for w in words if w.istitle())
                    price = float([w.strip("$") for w in words if "$" in w][0])
                    cat = words[-1]

                    new_row = pd.DataFrame(
                        [[name, qty, price, cat]],
                        columns=["Product Name", "Quantity", "Price", "Category"],
                    )
                    st.session_state["inventory"] = pd.concat(
                        [st.session_state["inventory"], new_row],
                        ignore_index=True
                    )
                    st.session_state["inventory"].to_csv(INV_FILE, index=False)
                    st.success(f"✅ Added {qty} {name}(s) to inventory.")
                except:
                    st.warning("⚠️ Could not parse request into table changes. Please edit manually.")

            elif "remove" in query.lower():
                # crude remove: e.g., "Remove Laptop"
                try:
                    words = query.split()
                    item = next(w for w in words if w.istitle())
                    st.session_state["inventory"] = st.session_state["inventory"][
                        st.session_state["inventory"]["Product Name"] != item
                    ]
                    st.session_state["inventory"].to_csv(INV_FILE, index=False)
                    st.success(f"✅ Removed {item} from inventory.")
                except:
                    st.warning("⚠️ Could not parse request into table changes. Please edit manually.")

            elif "update" in query.lower():
                # crude update: e.g., "Update Laptop quantity to 50"
                try:
                    words = query.split()
                    item = next(w for w in words if w.istitle())
                    if "quantity" in query.lower():
                        qty = int([w for w in words if w.isdigit()][0])
                        st.session_state["inventory"].loc[
                            st.session_state["inventory"]["Product Name"] == item,
                            "Quantity"
                        ] = qty
                        st.success(f"✅ Updated {item} quantity to {qty}.")
                    st.session_state["inventory"].to_csv(INV_FILE, index=False)
                except:
                    st.warning("⚠️ Could not parse update. Please edit manually.")



# ----------------------------
# DOCS MANAGER
# ----------------------------
elif page == "📂 Docs Manager":
    st.title("📂 Manage Documents")

    st.subheader("📤 Upload .txt documents")
    uploaded_files = st.file_uploader(
        "Upload your .txt files", type=["txt"], accept_multiple_files=True
    )
    if uploaded_files:
        for file in uploaded_files:
            filepath = os.path.join(DOCS_DIR, file.name)
            with open(filepath, "wb") as f:
                f.write(file.getbuffer())
        st.success("✅ Files uploaded successfully!")

    st.subheader("📋 Existing Documents")
    files = os.listdir(DOCS_DIR)
    txt_files = [f for f in files if f.endswith(".txt")]

    if txt_files:
        for f in txt_files:
            col1, col2 = st.columns([4, 1])
            col1.write(f)
            if col2.button("❌ Delete", key=f"del_{f}"):
                os.remove(os.path.join(DOCS_DIR, f))
                st.experimental_rerun()
    else:
        st.info("No documents found. Upload some to get started.")


# ----------------------------
# INSIGHTS
# ----------------------------
elif page == "📊 Insights":
    st.title("📊 Inventory Insights")
    inv = st.session_state["inventory"]

    if inv.empty:
        st.warning("⚠️ No inventory uploaded yet.")
    else:
        low_stock = inv[inv["Quantity"].astype(float) < 10]
        out_stock = inv[inv["Quantity"].astype(float) == 0]

        st.subheader("⚠️ Low Stock (<10)")
        st.dataframe(low_stock, use_container_width=True)

        st.subheader("❌ Out of Stock")
        st.dataframe(out_stock, use_container_width=True)

        st.subheader("📈 Inventory Overview")
        st.bar_chart(inv.set_index("Product Name")["Quantity"])

