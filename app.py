# app.py - Streamlit frontend for the Research Assistant Network

import streamlit as st
from research_network import ResearchAssistantNetwork  # Import the backend

# Initialize the research network (session state to persist across interactions)
if 'research_network' not in st.session_state:
    st.session_state.research_network = ResearchAssistantNetwork()

# Page config for a chat-like feel
st.set_page_config(
    page_title="Research Assistant Chat",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better chat styling
st.markdown("""
    <style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        max-width: 80%;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: auto;
        text-align: right;
    }
    .assistant-message {
        background-color: #f1f1f1;
        color: black;
        margin-right: auto;
    }
    .markdown h1, .markdown h2, .markdown h3 {
        color: #007bff;
    }
    .stChatMessage {
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Chat history in session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Title
st.title("🔍 Research Assistant Chat")
st.markdown("Ask me to research any topic, and I'll gather info from web sources, Wikipedia, and more!")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like me to research?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Researching... This may take a moment as I scrape the web and cross-reference sources."):
            # Use quick_research for faster response; switch to conduct_research for deeper async analysis if needed
            response = st.session_state.research_network.quick_research(prompt)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar for options (optional)
with st.sidebar:
    st.header("Research Options")
    use_async = st.checkbox("Use deep async research (slower but more comprehensive)", value=False)
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.info("Powered by web scraping, Wikipedia, and AI summarization.")