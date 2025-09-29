# app.py placeholder - replace with actual file if missing
import streamlit as st # type: ignore
import random
from horse_stable import render_horse_stable
from horse_racing import render_horse_racing
from stable_business import render_financial_dashboard
from jockeys import render_jockey_management
from auction_house import render_auction_house
from betting.betting_ui import render_betting_interface
from pete_ai import render_ai_advisor
from horse_board_game import render_horse_board_game
from horse_board_game_multiplayer import render_multiplayer_board_game
from firebase_utils import firebase_login, initialize_user_session

# --- AUTH & SETUP ---
if "logged_in" not in st.session_state:
    st.title("🔐 Login to Gold Creek Stables")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email and password:
            user_data = firebase_login(email, password)
            if user_data:
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user_data.get("localId")
                st.rerun()
        else:
            st.error("Please enter both email and password")
    st.stop()

st.set_page_config(page_title="🐎 Gold Creek Stables", layout="wide")
st.title("🏇 Gold Creek Stables & Racing Management")

# Initialize session-based user ID if not logged in
if "user_id" not in st.session_state and "logged_in" in st.session_state and st.session_state["logged_in"]:
    # User is logged in but no user_id (shouldn't happen, but safety check)
    pass
elif "user_id" not in st.session_state:
    # Create a session-based user ID for temporary data storage
    import time
    import random
    st.session_state["user_id"] = f"session_{int(time.time())}_{random.randint(1000,9999)}"

# Initialize user session data
if "user_id" in st.session_state:
    initialize_user_session(st.session_state["user_id"])

# --- MAIN CONTENT AREA (Based on Sidebar Navigation) ---
# Get selected page from sidebar
selected = st.session_state.get('selected_page', '🐴 My Stable')

# Render the appropriate content based on sidebar selection
if selected == "🐴 My Stable":
    render_horse_stable()
elif selected == "🏁 Race Track":
    render_horse_racing()
elif selected == "📈 Business Dashboard":
    render_financial_dashboard()
elif selected == "👨‍🌾 Jockeys":
    render_jockey_management()
elif selected == "💸 Betting Hall":
    render_betting_interface()
elif selected == "🏦 Auction House":
    render_auction_house()
elif selected == "🤖 Pete's AI Office":
    render_ai_advisor()
elif selected == "🎲 Board Game":
    render_horse_board_game()
elif selected == "🌐 Multiplayer Board Game":
    render_multiplayer_board_game()
elif selected == "🏆 Global Race Event":
        from global_race import submit_horse_to_global_race, get_global_race_entries, run_global_race
        st.header("🏆 Global Race Event")
        st.markdown("Enter your best horse to compete against other players in a big race!")
        # Select horse to enter
        owned_horses = st.session_state.get("owned_horses", [])
        horse_names = [h["name"] for h in owned_horses]
        selected_horse = st.selectbox("Select horse to enter:", horse_names) if horse_names else None
        if selected_horse:
            horse_obj = next((h for h in owned_horses if h["name"] == selected_horse), None)
            if st.button("Enter Horse in Global Race"):
                submit_horse_to_global_race(horse_obj)
                st.success(f"{selected_horse} entered in the Global Race!")
                st.rerun()
        st.markdown("---")
        st.subheader("Current Entries:")
        entries = get_global_race_entries()
        for entry in entries:
            st.write(f"{entry['horse']['name']} (by {entry['user_id']})")
        st.markdown("---")
        if st.button("Run Global Race!"):
            results = run_global_race()
            st.success("Race complete! Results:")
            for idx, horse in enumerate(results["entries"]):
                st.write(f"{idx+1}. {horse['name']}")
else:
    # Default fallback
    render_horse_stable()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("## 🏘️ **Navigate Gold Creek**")
    
    # Navigation menu
    page_options = [
        "🐴 My Stable",
        "🏁 Race Track", 
        "📈 Business Dashboard",
        "👨‍🌾 Jockeys",
        "💸 Betting Hall",
        "🏦 Auction House",
        "🤖 Pete's AI Office",
        "🎲 Board Game",
        "🌐 Multiplayer Board Game"
    ]
    
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = "🐴 My Stable"

    # Use callback to handle selection changes immediately
    def on_page_change():
        st.session_state.selected_page = st.session_state.page_selector

    selected_page = st.selectbox(
        "Choose Location:",
        page_options,
        index=page_options.index(st.session_state.selected_page) if st.session_state.selected_page in page_options else 0,
        key="page_selector",
        on_change=on_page_change
    )
    
    st.markdown("---")
    st.markdown("## 💰 **Stable Summary**")
    st.metric("Money", f"${st.session_state.get('money', 1000):,.2f}")
    st.metric("Debt", f"${abs(min(0, st.session_state.get('money', 1000))):,.2f}")
    st.metric("# of Horses", len(st.session_state.get('horses', {})))

    st.markdown("---")
    
    # Import and render racing season sidebar
    try:
        from racing_season import render_racing_season_sidebar
        render_racing_season_sidebar()
    except ImportError:
        st.markdown("## 🏁 **Racing Info**")
    
    # Track conditions
    track_conditions = ["dry", "wet", "muddy", "frozen"]
    if 'daily_track_condition' not in st.session_state:
        st.session_state.daily_track_condition = random.choice(track_conditions)
    
    track_icons = {"dry": "☀️", "wet": "🌧️", "muddy": "🟤", "frozen": "❄️"}
    track_icon = track_icons.get(st.session_state.daily_track_condition, "🏁")
    st.write(f"{track_icon} **Track:** {st.session_state.daily_track_condition.title()}")
    
    # Triple Crown Info
    triple_crown = ["Kentucky Derby", "Preakness Stakes", "Belmont Stakes"]
    st.write("🏆 **Triple Crown Races:**")
    for i, race in enumerate(triple_crown, 1):
        st.write(f"  {i}. {race}")
    
    # Race Stats
    total_races = len(st.session_state.get('race_history', []))
    st.write(f"🎯 **Races Run:** {total_races}")
    
    # Current Purse Pool
    current_purse = random.randint(5000, 15000)
    st.write(f"💰 **Today's Purse:** ${current_purse:,}")
    
    # Weather conditions
    weather_conditions = ["☀️ Sunny", "⛅ Cloudy", "🌧️ Rainy", "🌪️ Windy", "🌫️ Foggy"]
    if 'daily_weather' not in st.session_state:
        st.session_state.daily_weather = random.choice(weather_conditions)
    st.write(f"🌤️ **Weather:** {st.session_state.daily_weather}")
    
    # Featured Jockey
    jockeys = ["Slick Rick", "Anxious Annie", "Billy Biceps", "No-Nose Ned", "Calm Carlita"]
    if 'featured_jockey' not in st.session_state:
        st.session_state.featured_jockey = random.choice(jockeys)
    st.write(f"🏇 **Featured Jockey:** {st.session_state.featured_jockey}")

    st.markdown("---")
    st.markdown("### 🕒 Last Login")
    last_login = st.session_state.get("last_login", "Unknown")
    user_email = st.session_state.get("email", None)
    if user_email:
        st.write(f"{last_login} ({user_email})")
    else:
        st.write(last_login)