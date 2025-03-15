import streamlit as st
import groq
import os
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Any

# Set page configuration
st.set_page_config(page_title="Lead Generation AI", page_icon="💼", layout="wide")

# Initialize Groq API key
if 'GROQ_API_KEY' not in st.session_state:
    st.session_state.GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

# Lead data storage
if 'leads' not in st.session_state:
    st.session_state.leads = []

# Chat history storage
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Initialize Groq client
def initialize_groq_client():
    """Initialize Groq client with API key"""
    api_key = st.session_state.GROQ_API_KEY.strip()
    if api_key:
        try:
            return groq.Groq(api_key=api_key)
        except Exception as e:
            st.error(f"Error initializing Groq client: {e}")
    return None

# Fetch response from Groq API
def get_groq_response(client, messages: List[Dict[str, str]]) -> str:
    """Get response from Groq API"""
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",  # Groq's high-performance model
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error fetching response from Groq: {e}")
        return "I'm sorry, I'm having trouble connecting right now. Please try again later."

# Lead qualification functions
def extract_lead_data(response: str) -> Dict[str, Any]:
    """Extract lead data from AI response"""
    try:
        json_start = response.find("```json")
        json_end = response.find("```", json_start + 6)
        if json_start != -1 and json_end != -1:
            json_str = response[json_start + 7:json_end].strip()
            return json.loads(json_str)
    except Exception as e:
        st.error(f"Error extracting lead data: {e}")
    return {}

def update_lead_info(lead_data: Dict[str, Any]):
    """Update lead information in session state"""
    if not lead_data:
        return
    lead_data['timestamp'] = datetime.now().isoformat()
    if lead_data.get('email'):
        for i, lead in enumerate(st.session_state.leads):
            if lead.get('email') == lead_data.get('email'):
                st.session_state.leads[i].update(lead_data)
                return
    st.session_state.leads.append(lead_data)

def save_leads_to_csv():
    """Save leads to CSV file"""
    if st.session_state.leads:
        df = pd.DataFrame(st.session_state.leads)
        df.to_csv('leads.csv', index=False)
        return True
    return False

# Streamlit UI
st.title("Lead Generation AI Assistant 💼")

# Sidebar for API key and lead analytics
with st.sidebar:
    st.header("Configuration")
    api_key_input = st.text_input("Enter Groq API Key", st.session_state.GROQ_API_KEY, type="password")
    if st.button("Save API Key"):
        st.session_state.GROQ_API_KEY = api_key_input
        st.success("API Key saved!")
    st.markdown("---")
    st.header("Lead Analytics")
    hot_leads = sum(1 for lead in st.session_state.leads if lead.get('lead_quality') == 'hot')
    warm_leads = sum(1 for lead in st.session_state.leads if lead.get('lead_quality') == 'warm')
    cold_leads = sum(1 for lead in st.session_state.leads if lead.get('lead_quality') == 'cold')
    col1, col2, col3 = st.columns(3)
    col1.metric("Hot Leads", hot_leads)
    col2.metric("Warm Leads", warm_leads)
    col3.metric("Cold Leads", cold_leads)
    if st.button("Export Leads"):
        if save_leads_to_csv():
            st.success("Leads exported to leads.csv")
            st.download_button(
                label="Download CSV",
                data=pd.DataFrame(st.session_state.leads).to_csv(index=False),
                file_name="leads.csv",
                mime="text/csv"
            )
        else:
            st.warning("No leads to export")

# Initialize chat interface
if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": "Hello! How can I assist you today?"})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        if message["role"] == "assistant":
            json_start = content.find("```json")
            if json_start != -1:
                content = content[:json_start]
        st.markdown(content)

if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    client = initialize_groq_client()
    if client:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_groq_response(client, st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": response})
                lead_data = extract_lead_data(response)
                update_lead_info(lead_data)
                display_response = response.split("```json")[0]
                st.markdown(display_response)
    else:
        st.error("Please enter a valid Groq API key in the sidebar.")
