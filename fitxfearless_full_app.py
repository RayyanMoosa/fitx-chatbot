import streamlit as st
import re
import os
import sys
from openai import OpenAI
import streamlit.components.v1 as components  # for voice input/output

# Voice input/output HTML+JS snippet (for meal planner input mic)
VOICE_HTML = """
<script>
var recognition = new(window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = 'en-US';
recognition.interimResults = false;
recognition.maxAlternatives = 1;

function startRecognition() {
    recognition.start();
}

recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    const inputBox = window.parent.document.querySelector('input#meal_input');
    if(inputBox) {
        inputBox.value = transcript;
        inputBox.dispatchEvent(new Event('input', { bubbles: true }));
    }
}
</script>
<button onclick="startRecognition()">🎤 Speak</button>
"""

# Chat voice input HTML+JS snippet for chat input mic
CHAT_VOICE_HTML = """
<script>
var recognition = new(window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = 'en-US';
recognition.interimResults = false;
recognition.maxAlternatives = 1;

function startRecognition() {
    recognition.start();
}

recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    const inputBox = window.parent.document.querySelector('input#chat_input');
    if(inputBox) {
        inputBox.value = transcript;
        inputBox.dispatchEvent(new Event('input', { bubbles: true }));
    }
}
</script>
<button onclick="startRecognition()">🎤 Speak</button>
"""

# Lex's personality system prompt (from fitness_chatbot.py)
SYSTEM_PROMPT = """
You are Lex, a friendly, energetic, and motivational fitness coach.
You always speak in an upbeat, supportive tone. You use emojis sometimes to sound fun and engaging.
You're casual and feel like a gym buddy. If the user feels down or unmotivated, cheer them up.

Avoid sounding robotic or formal. Keep your replies short, helpful, and fun. Be proactive and helpful.
"""

# Initialize OpenAI client using environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="💪 FitxFearless AI Coach", page_icon="💪")

st.title("💪 FitxFearless AI Coach")
st.markdown("""
Welcome! I'm **Lex**, your assistant coach.
Let’s get you started on your fitness journey. Ready? 👇
""")

# Helper functions and setup

def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

def generate_summary(answers):
    prompt = f"""
You are a friendly fitness coach assistant.
Here are the user’s answers:
Goal: {answers['goal']}
Struggle: {answers['struggle']}
Timeline: {answers['timeline']}

Write a warm, encouraging summary of their fitness journey and next steps.
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
    return response.choices[0].message.content

def rerun_app():
    sys.exit()

# Initialize session state variables

if "step" not in st.session_state:
    st.session_state.step = 0

if "memory" not in st.session_state:
    st.session_state.memory = {}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""

# Multi-step flow

if st.session_state.step == 0:
    # Lead Capture Form
    with st.form("lead_form"):
        name = st.text_input("What's your name?", value=st.session_state.memory.get("name", ""))
        email = st.text_input("Your email?", value=st.session_state.memory.get("email", ""))
        goal_options = ["🏋️‍♂️ Build muscle", "🔥 Lose fat", "🏃‍♀️ Improve endurance", "💪 Get in shape overall"]
        goal = st.selectbox(
            "What is your primary fitness goal?", goal_options,
            index=goal_options.index(st.session_state.memory["goal"]) if st.session_state.memory.get("goal") in goal_options else 0
        )
        submitted = st.form_submit_button("Start Coaching")
        if submitted:
            if name and email and is_valid_email(email):
                st.session_state.memory["name"] = name
                st.session_state.memory["email"] = email
                st.session_state.memory["goal"] = goal
                st.session_state.step = 1
                rerun_app()
            else:
                st.error("Please enter a valid name and email.")

elif st.session_state.step == 1:
    # Struggle selection
    st.write(f"Welcome back, {st.session_state.memory['name']}! Ready to crush your goal: {st.session_state.memory['goal']}?")
    struggle_options = ["⏳ Not enough time", "🥗 Struggle with diet", "💡 Lack of motivation", "🤷 Not sure what works for me"]
    struggle = st.radio(
        "What do you feel is holding you back right now?", struggle_options,
        index=struggle_options.index(st.session_state.memory["struggle"]) if st.session_state.memory.get("struggle") in struggle_options else 0
    )
    if st.button("Next"):
        st.session_state.memory["struggle"] = struggle
        st.session_state.step = 2
        rerun_app()

elif st.session_state.step == 2:
    # Timeline selection
    timeline_options = ["✅ ASAP", "🗓️ Within a month", "📅 In 2–3 months"]
    timeline = st.radio(
        "When would you ideally want to start seeing results?", timeline_options,
        index=timeline_options.index(st.session_state.memory["timeline"]) if st.session_state.memory.get("timeline") in timeline_options else 0
    )
    if st.button("Next"):
        st.session_state.memory["timeline"] = timeline
        st.session_state.step = 3
        rerun_app()

elif st.session_state.step == 3:
    # Show personalized summary
    with st.spinner("Generating your personalized fitness summary..."):
        summary = generate_summary({
            "goal": st.session_state.memory["goal"],
            "struggle": st.session_state.memory["struggle"],
            "timeline": st.session_state.memory["timeline"]
        })
    st.markdown("### Your Personalized Fitness Summary:")
    st.info(summary)
    
    if st.button("🔊 Play Summary Audio"):
        js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance();
        msg.text = {repr(summary)};
        window.speechSynthesis.speak(msg);
        </script>
        """
        components.html(js_code, height=0)

    email_input = st.text_input("Confirm your email to send your custom strategy + success stories", value=st.session_state.memory.get("email", ""))
    if st.button("Send & Continue"):
        if is_valid_email(email_input):
            st.session_state.memory["email"] = email_input
            st.session_state.step = 4
            rerun_app()
        else:
            st.error("Please enter a valid email.")

elif st.session_state.step == 4:
    # Meal Planner + Voice Input + Prompt for next step
    st.success(f"Thanks for sharing your info, {st.session_state.memory['name']}! 🎉")

    st.markdown("""
    ### Meal Planner
    Tell me your dietary preferences or restrictions (e.g., vegetarian, keto, allergies) and I’ll create a simple meal plan for you.
    """)

    components.html(VOICE_HTML, height=60)

    meal_input = st.text_input("Your dietary preferences or restrictions (try speaking!)", key="meal_input")
    
    if st.button("Generate Meal Plan") and meal_input.strip():
        prompt = f"Create a simple 3-day meal plan for someone with these dietary preferences/restrictions: {meal_input}"
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful fitness meal planner."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        meal_plan = response.choices[0].message.content
        st.markdown("### Your 3-Day Meal Plan:")
        st.info(meal_plan)
        
        if st.button("🔊 Play Meal Plan Audio"):
            js_code = f"""
            <script>
            var msg = new SpeechSynthesisUtterance();
            msg.text = {repr(meal_plan)};
            window.speechSynthesis.speak(msg);
            </script>
            """
            components.html(js_code, height=0)

    st.markdown("---")
    st.markdown("""
    ✅ You're almost ready!  
    📅 **[Book Your Free Strategy Call](https://calendly.com/YOUR_LINK)**  
    """)

    if st.button("💬 Continue chatting with Lex"):
        st.session_state.step = 5
        rerun_app()

    if st.button("Start Over"):
        st.session_state.step = 0
        st.session_state.memory = {}
        rerun_app()

elif st.session_state.step >= 5:
    # Freeform conversational chatbot interface (main chat with Lex)

    st.markdown("---")
    st.header("💬 Chat with Lex, your AI Fitness Coach")

    # Display chat history with formatting
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        elif msg["role"] == "assistant":
            st.markdown(f"**Lex:** {msg['content']}")

    def submit_chat():
        user_message = st.session_state.chat_input.strip()
        if not user_message:
            return

        st.session_state.chat_history.append({"role": "user", "content": user_message})
        st.session_state.chat_input = ""

        with st.spinner("Lex is typing..."):
            response = client.chat.completions.create(
                model="gpt-4",
                messages=st.session_state.chat_history,
                temperature=0.7,
                max_tokens=300,
            )
        assistant_msg = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_msg})

    # Text input with Enter submission
    st.text_input(
        "Type your message here...",
        key="chat_input",
        on_change=submit_chat,
        placeholder="Type and press Enter or click Send",
    )

    # Optional Send button
    if st.button("Send"):
        submit_chat()

    # Mic button for voice input in chat
    components.html(CHAT_VOICE_HTML, height=60)

    if st.button("Reset Chat"):
        st.session_state.chat_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        st.session_state.chat_input = ""
        rerun_app()
