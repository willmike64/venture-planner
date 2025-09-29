import streamlit as st
from firebase_utils import save_race_record, load_race_records
from horse_racing import render_horse_racing
from datetime import datetime

GLOBAL_RACE_KEY = "global_race_entries"

def submit_horse_to_global_race(horse):
    user_id = st.session_state.get("user_id", "unknown")
    entries = st.session_state.get(GLOBAL_RACE_KEY, [])
    entry = {
        "horse": horse,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat()
    }
    entries.append(entry)
    st.session_state[GLOBAL_RACE_KEY] = entries
    # Persist entries in session only for now (multi-user: use Firebase board game logic)

def get_global_race_entries():
    # For now, use session state (multi-user: aggregate from Firebase)
    return st.session_state.get(GLOBAL_RACE_KEY, [])

def run_global_race():
    entries = get_global_race_entries()
    horses = [e["horse"] for e in entries]
    # Use render_horse_racing or refactor race logic to accept custom horses
    # For now, just return the horses list as a placeholder
    # TODO: Integrate with actual race simulation and results
    race_results = {"entries": horses, "timestamp": datetime.now().isoformat()}
    save_race_record({
        "race_name": "Global Race",
        "date": datetime.now().isoformat(),
        "results": horses
    })
    return race_results