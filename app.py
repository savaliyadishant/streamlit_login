import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import json
import pandas as pd
import time

from components.sidebar import render_sidebar
from components.chat_input import render_chat_input
from components.config_ui import render_config_screen
from core.prompt_builder import build_prompt
from core.llm_generator import generate_sql, generate_natural_response
from core.query_executor import execute_query
from core.sql_validator import validate_sql

# Set page configuration
st.set_page_config(page_title="Gen AI SQL Agent", layout="wide")

# Load user credentials
with open("config/config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# Authenticator setup
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Login form
name, authentication_status, username = authenticator.login("Login", "main")

# If login successful
if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"✅ Logged in as: {name} ({username})")
    # Map username to role
    role = "admin" if username == "admin" else "analyst"
    st.sidebar.info(f"🔐 Your role: {role}")
    # Load role permissions
    with open("config/roles.json") as f:
        ROLE_PERMISSIONS = json.load(f)

    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    screen = st.sidebar.radio("Go to:", ["GenAI Assistant", "Configuration"])

    if screen == "GenAI Assistant":
        st.markdown("## 🤖 Gen AI Assistant")
        user_query, submitted = render_chat_input()
        selected_db = render_sidebar()

        if user_query and submitted:
            prompt = build_prompt(user_query, role, selected_db)
            st.code(prompt, language="sql")

            sql_query = generate_sql(prompt, role)
            st.code(sql_query, language="sql")

            allow_dml = ROLE_PERMISSIONS[role].get("allow_dml", False)
            validation = validate_sql(sql_query, allow_dml=allow_dml)

            if not validation["valid"]:
                st.error(f"❌ Invalid SQL Query: {validation['error']}")
                st.stop()

            result = execute_query(sql_query, selected_db, user_query, role)

            if result["error"]:
                st.error(f"❌ Query Execution Failed: {result['error']}")
            else:
                rows = result.get("rows")
                columns = result.get("columns")

                if rows is not None and columns is not None:
                    df_result = pd.DataFrame(rows, columns=columns)
                    if not df_result.empty:
                        st.subheader("🗣️ Natural Language Answer (Word-by-word)")
                        natural_response = generate_natural_response(user_query, df_result)

                        placeholder = st.empty()
                        typed_text = ""

                        # Show word-by-word with a short delay
                        for word in natural_response.split():
                            typed_text += word + " "
                            placeholder.markdown(typed_text + "▌")  # Simulate typing cursor  # Adjust speed if needed
                            time.sleep(0.1)
                        # Finalize without cursor
                        placeholder.markdown(typed_text.strip())

                    else:
                        st.warning("⚠️ Query executed successfully but returned no data.")
                else:
                    st.success("✅ Query executed successfully. (No data returned)")

    elif screen == "Configuration":
        render_config_screen()

# If login failed
elif authentication_status is False:
    st.error("❌ Incorrect username or password")

# If waiting for login
elif authentication_status is None:
    st.warning("🔐 Please enter your username and password to continue.")
