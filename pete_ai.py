# pete_ai.py placeholder - replace with actual file if missing
import streamlit as st # type: ignore
import openai # type: ignore

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- AI PERSONALITIES ---
PERSONALITIES = {
    "Cowboy Philosopher": "Speak with poetic cowboy wisdom, always weaving life lessons into your horse racing advice.",
    "Sarcastic Gambler": "You're jaded, sharp-tongued, and suspicious of every bet—but deep down you're brilliant.",
    "Stable Economist": "You use economics, math, and probabilities to explain stable management and betting outcomes.",
    "Hype Jockey": "You're overly excited and dramatic, like a sports announcer with a love for horses.",
    "Zen Breeder": "You are calm, mystical, and view horses as spiritual beings with destined paths."
}

DEFAULT_PROMPT = "Give strategic, witty, or useful advice about horse racing or stable management."

def render_ai_advisor():
    st.header("🤖 Pete the AI Advisor")

    personality = st.selectbox("🧠 Choose Pete's Personality", list(PERSONALITIES.keys()))
    topic = st.text_input("Ask Pete a question...", "How do I pick the best horse to breed?")

    if st.button("🧠 Ask Pete"):
        system_prompt = PERSONALITIES[personality]

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": topic or DEFAULT_PROMPT}
                ]
            )
            st.success("💬 Pete says:")
            content = response.choices[0].message.content
            st.markdown(content.strip() if content else "Pete seems to be at a loss for words...")
        except Exception as e:
            st.error("Pete couldn't connect to OpenAI. Check your API key or try again later.")