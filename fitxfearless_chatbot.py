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

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="FitxFearless AI Coach", page_icon="💪")
st.title("💪 FitxFearless AI Coach")
st.markdown("""
Welcome! I'm **Lex**, your assistant coach.
Let’s get you started on your fitness journey. Ready? 👇
""")

# Initialize memory in session state
if "memory" not in st.session_state:
    st.session_state.memory = {}

# Email validation function
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

# Function to generate personalized summary using OpenAI GPT
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
        model="gpt-4",  # or "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
    return response.choices[0].message.content

# Helper function to rerun app (replaces st.experimental_rerun)
def rerun_app():
    sys.exit()

# Step flow control
if "step" not in st.session_state:
    st.session_state.step = 0  # start from 0 to capture lead first

# Step 0: Lead Capture Form
if st.session_state.step == 0:
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
                rerun_app()  # rerun app to proceed
            else:
                st.error("Please enter a valid name and email.")

# Step 1: Struggle selection
elif st.session_state.step == 1:
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

# Step 2: Timeline selection
elif st.session_state.step == 2:
    timeline_options = ["✅ ASAP", "🗓️ Within a month", "📅 In 2–3 months"]
    timeline = st.radio(
        "When would you ideally want to start seeing results?", timeline_options,
        index=timeline_options.index(st.session_state.memory["timeline"]) if st.session_state.memory.get("timeline") in timeline_options else 0
    )
    if st.button("Next"):
        st.session_state.memory["timeline"] = timeline
        st.session_state.step = 3
        rerun_app()

# Step 3: Show personalized summary from OpenAI and ask for email to send strategy
elif st.session_state.step == 3:
    with st.spinner("Generating your personalized fitness summary..."):
        summary = generate_summary({
            "goal": st.session_state.memory["goal"],
            "struggle": st.session_state.memory["struggle"],
            "timeline": st.session_state.memory["timeline"]
        })
    st.markdown("### Your Personalized Fitness Summary:")
    st.info(summary)
    
    # Voice play button for summary
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

# Step 4: Meal Planner + Voice Input + Chatbot
elif st.session_state.step == 4:
    st.success(f"Thanks for sharing your info, {st.session_state.memory['name']}! 🎉")

    st.markdown("""
    ### Meal Planner
    Tell me your dietary preferences or restrictions (e.g., vegetarian, keto, allergies) and I’ll create a simple meal plan for you.
    """)

    # Mic button for voice input
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
        
        # Voice play button for meal plan
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

# Step 5+: Freeform conversational chatbot interface
if st.session_state.step >= 5:

    st.markdown("---")
    st.header("💬 Chat with Lex, your AI Fitness Coach")

    # Initialize chat history if missing
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "system", "content": "You are Lex, a friendly and helpful AI fitness coach. Provide encouragement, advice, and support about fitness, nutrition, and motivation."}
        ]
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        elif msg["role"] == "assistant":
            st.markdown(f"**Lex:** {msg['content']}")

    def submit_chat():
        user_message = st.session_state.chat_input.strip()
        if not user_message:
            return

        # Append user message
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        st.session_state.chat_input = ""  # Clear input box

        with st.spinner("Lex is typing..."):
            response = client.chat.completions.create(
                model="gpt-4",
                messages=st.session_state.chat_history,
                temperature=0.7,
                max_tokens=300,
            )
        assistant_msg = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_msg})

    # Chat input with on_change to submit on Enter
    st.text_input(
        "Type your message here...",
        key="chat_input",
        on_change=submit_chat,
        placeholder="Type and press Enter or click Send",
    )

    # Send button (optional, for clicking instead of Enter)
    if st.button("Send"):
        submit_chat()

    # Mic button for voice input in chat
    components.html(CHAT_VOICE_HTML, height=60)

    if st.button("Reset Chat"):
        st.session_state.chat_history = [
            {"role": "system", "content": "You are Lex, a friendly and helpful AI fitness coach. Provide encouragement, advice, and support about fitness, nutrition, and motivation."}
        ]
        st.session_state.chat_input = ""
        rerun_app()
