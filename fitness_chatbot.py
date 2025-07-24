import streamlit as st
from openai import OpenAI
import os

# Set your OpenAI API key securely
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -------------------------------
# 🧠 Lex's personality system prompt
SYSTEM_PROMPT = """
You are Lex, a friendly, energetic, and motivational fitness coach.
You always speak in an upbeat, supportive tone. You use emojis sometimes to sound fun and engaging.
You're casual and feel like a gym buddy. If the user feels down or unmotivated, cheer them up.

Avoid sounding robotic or formal. Keep your replies short, helpful, and fun. Be proactive and helpful.
"""

# -------------------------------
# 🎯 Streamlit App Layout
st.set_page_config(page_title="FitxFearless AI Coach", page_icon="💪")

st.title("💪 FitxFearless AI Coach")
st.markdown("Welcome! I'm **Lex**, your assistant coach. Let’s get you started on your fitness journey. Ready?")

# -------------------------------
# 💬 Conversation Session
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Hey! I'm Lex, your AI fitness buddy 💪 What's your goal today? Let's make it happen!"}
    ]

# Show conversation
for msg in st.session_state.messages[1:]:
    st.chat_message(msg["role"]).markdown(msg["content"])

# User input
if prompt := st.chat_input("Type your message here…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages,
        )
        msg = response.choices[0].message.content
        st.markdown(msg)

    st.session_state.messages.append({"role": "assistant", "content": msg})
