import streamlit as st
from chatbot.core.chatbot import AIMLChatbot

def initialize_chatbot_session(llm_provider, model_name, temperature, search_type):
    """
    Streamlit session state içinde chatbot'u ve ilgili ayarları başlatır.
    """
    st.session_state.chatbot = AIMLChatbot(
        llm_provider=llm_provider,
        model_name=model_name,
        temperature=temperature,
        search_type=search_type
    )
    st.session_state.llm_provider = llm_provider
    st.session_state.model_name = model_name
    st.session_state.temperature = temperature
    st.session_state.search_type = search_type

def chatbot_needs_reset(llm_provider, model_name, temperature, search_type):
    """
    Mevcut session ayarlarıyla yeni ayarlar uyuşmuyorsa True döner.
    """
    return (
        ("llm_provider" in st.session_state and st.session_state.llm_provider != llm_provider) or
        ("model_name" in st.session_state and st.session_state.model_name != model_name) or
        ("temperature" in st.session_state and st.session_state.temperature != temperature) or
        ("search_type" in st.session_state and st.session_state.search_type != search_type)
    )
