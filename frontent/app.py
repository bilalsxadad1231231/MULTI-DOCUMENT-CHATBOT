import streamlit as st
import requests
import json
from datetime import datetime
from typing import Optional, Dict, List

# Configuration
API_URL = "http://34.203.75.2:8000"

# Initialize session state variables
def init_session_state():
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'chatbots' not in st.session_state:
        st.session_state.chatbots = []
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = {}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'main'
    if 'selected_chatbot' not in st.session_state:
        st.session_state.selected_chatbot = None

class APIClient:
    def get_headers() -> Dict:
        if st.session_state.access_token:
            return {"Authorization": f"Bearer {st.session_state.access_token}"}
        return {}

    @staticmethod
    def handle_response(response: requests.Response):
        if response.status_code == 401:
            st.session_state.access_token = None
            st.session_state.user_info = None
            st.error("Session expired. Please login again.")
            st.rerun()
        elif not 200 <= response.status_code < 300:
            error_detail = response.json().get('detail', 'An error occurred')
            st.error(f"Error: {error_detail}")
            return None
        return response.json()

    @classmethod
    def register(cls, username: str, email: str, password: str) -> bool:
        try:
            response = requests.post(
                f"{API_URL}/register",
                json={"username": username, "email": email, "password": password}
            )
            result = cls.handle_response(response)
            if result:
                st.session_state.access_token = result["access_token"]
                return True
            return False
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            return False

    @classmethod
    def login(cls, username: str, password: str) -> bool:
        try:
            response = requests.post(
                f"{API_URL}/token",
                data={"username": username, "password": password}
            )
            result = cls.handle_response(response)
            if result:
                st.session_state.access_token = result["access_token"]
                return True
            return False
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            return False

    @classmethod
    def create_chatbot(cls, name: str, description: str, persona_prompt: str, file) -> bool:
        try:
            files = {"document": file}
            data = {
                "name": name,
                "description": description,
                "persona_prompt": persona_prompt
            }
            response = requests.post(
                f"{API_URL}/chatbots",
                data=data,
                files=files,
                headers=cls.get_headers()
            )
            return cls.handle_response(response) is not None
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            return False

    @classmethod
    def get_chatbots(cls) -> List[Dict]:
        try:
            response = requests.get(
                f"{API_URL}/chatbots",
                headers=cls.get_headers()
            )
            result = cls.handle_response(response)
            return result if result else []
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            return []

    @classmethod
    def chat_with_bot(cls, chatbot_name: str, message: str) -> Optional[str]:
        try:
            response = requests.post(
                f"{API_URL}/chatbots/chat",
                json={
                    "chatbot_name": chatbot_name,
                    "message": message
                },
                headers=cls.get_headers()
            )
            
            response.raise_for_status()
            
            result = cls.handle_response(response)
            
            return result.get("response") if result else None
        
        except requests.RequestException as e:
            st.error(f"Error communicating with chatbot: {str(e)}")
            return None

def render_login_page():
    st.header("Login")
    with st.form(key="login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button("Login")

        if submit and username and password:
            if APIClient.login(username, password):
                st.success("Login successful!")
                st.rerun()

def render_register_page():
    st.header("Register")
    with st.form(key="register_form"):
        username = st.text_input("Username", key="register_username")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        submit = st.form_submit_button("Register")

        if submit and username and email and password:
            if APIClient.register(username, email, password):
                st.success("Registration successful! You can now login.")
                st.rerun()

def render_create_chatbot_page():
    st.header("Create New Chatbot")
    with st.form(key="chatbot_form"):
        name = st.text_input("Chatbot Name")
        description = st.text_area("Description")
        persona_prompt = st.text_area("Persona Prompt")
        file = st.file_uploader("Upload Training Document", type=["txt", "pdf"])
        submit = st.form_submit_button("Create Chatbot")

        if submit:
            if not all([name, description, persona_prompt, file]):
                st.error("All fields are required!")
            else:
                if APIClient.create_chatbot(name, description, persona_prompt, file):
                    st.success("Chatbot created successfully!")
                    st.session_state.chatbots = APIClient.get_chatbots()
                    st.rerun()

def render_chat_interface(chatbot):
    st.header(f"Chat with {chatbot['name']}")
    
    # Add a back button
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = 'main'
        st.session_state.selected_chatbot = None
        st.rerun()
    
    # Display chatbot info
    with st.expander("Chatbot Details", expanded=False):
        st.write(f"**Description**: {chatbot['description']}")
        st.write(f"**Created**: {datetime.fromisoformat(chatbot['created_at']).strftime('%Y-%m-%d %H:%M')}")
        st.write(f"**Persona**: {chatbot['persona_prompt']}")
    
    # Initialize chat history for this chatbot
    if f"messages_{chatbot['id']}" not in st.session_state:
        st.session_state[f"messages_{chatbot['id']}"] = []
    
    # Chat container for scrollable history
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        for message in st.session_state[f"messages_{chatbot['id']}"]:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input(f"Message {chatbot['name']}"):
        # Add user message to chat history
        st.session_state[f"messages_{chatbot['id']}"].append(
            {"role": "user", "content": prompt}
        )
        
        # Get chatbot response
        response = APIClient.chat_with_bot(chatbot['name'], prompt)
        if response:
            st.session_state[f"messages_{chatbot['id']}"].append(
                {"role": "assistant", "content": response}
            )
        st.rerun()

def render_chatbot_list():
    st.header("My Chatbots")
    chatbots = APIClient.get_chatbots()
    
    if not chatbots:
        st.info("No chatbots found. Create one to get started!")
        return

    # Create a grid layout for chatbot cards
    cols = st.columns(3)  # Adjust number of columns as needed
    
    for idx, chatbot in enumerate(chatbots):
        with cols[idx % 3]:
            # Create a card-like container for each chatbot
            with st.container():
                st.subheader(f"📱 {chatbot['name']}")
                st.write(f"**Description**: {chatbot['description'][:100]}...")
                st.write(f"**Created**: {datetime.fromisoformat(chatbot['created_at']).strftime('%Y-%m-%d')}")
                
                # Chat button
                if st.button("Open Chat", key=f"chat_btn_{chatbot['id']}"):
                    st.session_state.selected_chatbot = chatbot
                    st.session_state.current_page = 'chat'
                    st.rerun()
                
                st.divider()  # Visual separator between cards

def main():
    # Initialize session state
    init_session_state()
    
    # Sidebar
    st.sidebar.title("Navigation")
    
    if not st.session_state.access_token:
        page = st.sidebar.radio("Menu", ["Login", "Register"], key="nav_public")
        if page == "Login":
            render_login_page()
        else:
            render_register_page()
    else:
        # Show logout button
        if st.sidebar.button("Logout"):
            st.session_state.access_token = None
            st.session_state.user_info = None
            st.session_state.current_page = 'main'
            st.session_state.selected_chatbot = None
            st.rerun()
        
        # Navigation based on current page
        if st.session_state.current_page == 'main':
            page = st.sidebar.radio("Menu", ["My Chatbots", "Create Chatbot"], key="nav_private")
            if page == "My Chatbots":
                render_chatbot_list()
            else:
                render_create_chatbot_page()
        else:
            # Render chat interface if a chatbot is selected
            if st.session_state.selected_chatbot:
                render_chat_interface(st.session_state.selected_chatbot)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Chatbot Platform",
        page_icon="🤖",
        layout="wide"
    )
    main()