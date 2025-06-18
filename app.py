import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# ---- Load Config from YAML ----
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# ---- Initialize Authenticator ----
authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# ---- Login UI ----
name, authentication_status, username = authenticator.login("Login", location="main")

if authentication_status is False:
    st.error("Username/password is incorrect")
elif authentication_status is None:
    st.warning("Please enter your username and password")
elif authentication_status:
    authenticator.logout("Logout", location="sidebar")
    st.sidebar.success(f"Welcome {name} 👋")
    
    st.title("🔐 Protected App")
    st.write("You're now logged in and can access this content.")
