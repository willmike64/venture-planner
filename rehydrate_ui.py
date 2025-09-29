import streamlit as st
from datetime import datetime
from firebase_utils import (
    load_race_records,
    update_horse_race_record,
    load_global_horse_history
)

# --- Helpers ---
def clean_horse_name(name: str) -> str:
    return name.split(" (")[0].replace("⭐", "").strip()

def rehydrate_from_blockchain(limit=250):
    race_records = load_race_records(limit)
    global_history = load_global_horse_history()
    updated, skipped, errors = 0, 0, 0
    horses_seen = set()

    if not race_records:
        return 0, 0, 0, []

    from stable_business import track_revenue
    user_id = st.session_state.get('user_id', None)
    for race_id, race_data in race_records.items():
        results = race_data.get("results", [])
        track_condition = race_data.get("track_condition", "normal")
        race_name = race_data.get("race_name", "standard")
        race_date = race_data.get("date", datetime.now().isoformat())

        for horse_result in results:
            horse_name = clean_horse_name(horse_result.get('name', ''))
            if not horse_name:
                continue

            horses_seen.add(horse_name)
            import pandas as pd
            if isinstance(global_history, dict):
                prior_record = global_history.get(horse_name)
            elif isinstance(global_history, list):
                prior_record = next(
                    (
                        rec
                        for rec in global_history
                        if isinstance(rec, dict) and rec.get('horse_name') == horse_name # type: ignore
                    ),
                    None
                )
            elif isinstance(global_history, pd.DataFrame):
                matches = global_history[global_history['horse_name'] == horse_name]
                if isinstance(matches, pd.DataFrame) and not matches.empty:
                        prior_record = matches.iloc[0].to_dict()
                else:
                        prior_record = None
            else:
                prior_record = None

            prior_record_is_none_or_empty = False
            if prior_record is None:
                prior_record_is_none_or_empty = True
            elif isinstance(prior_record, dict) and not prior_record:
                prior_record_is_none_or_empty = True
            elif isinstance(prior_record, list) and len(prior_record) == 0:
                prior_record_is_none_or_empty = True
            elif isinstance(prior_record, pd.DataFrame):
                prior_record_is_none_or_empty = prior_record.empty
            elif isinstance(prior_record, (datetime, tuple)):
                prior_record_is_none_or_empty = True
            if (
                prior_record_is_none_or_empty or
                (isinstance(prior_record, dict) and 'last_race_date' not in prior_record)
            ):
                try:
                    update_horse_race_record(
                        horse_name=horse_name,
                        race_result={
                            'position': horse_result.get('position', 10),
                            'earnings': horse_result.get('prize_money', 0),
                            'track_condition': track_condition,
                            'field_size': len(results),
                            'race_type': race_name,
                            'final_speed': horse_result.get('speed', 0),
                            'breed': horse_result.get('breed', 'Unknown')
                        },
                        owner_id=horse_result.get('owner_id', 'Unknown')
                    )
                    # Track revenue for this user if they are the owner
                    if user_id and horse_result.get('owner_id', None) == user_id:
                        prize = horse_result.get('prize_money', 0)
                        if prize > 0:
                            track_revenue(prize, 'rehydrated_race')
                    updated += 1
                except Exception as e:
                    st.warning(f"❌ Failed to update {horse_name}: {e}")
                    errors += 1
            else:
                skipped += 1

    return updated, skipped, errors, list(horses_seen)

# --- UI ---
st.set_page_config(page_title="🐎 Horse History Rehydrator", layout="wide")
st.title("🐴 Global Horse History Rehydrator")

st.markdown("""
This tool will replay **immutable race records** to **rebuild missing or incomplete global horse history** data.  
Useful for resolving issues where Derby horses or leaderboard horses are disappearing.
""")

limit = st.slider("🔢 How many recent races to process?", 50, 1000, 250, step=50)

if st.button("🛠️ Run Rehydration Process"):
    with st.spinner("Restoring horse history from blockchain records..."):
        updated, skipped, errors, all_horses = rehydrate_from_blockchain(limit=limit)

    st.success("✅ Rehydration Complete!")
    st.metric("Total Horses Seen", len(all_horses))
    st.metric("🐎 Updated in Global History", updated)
    st.metric("⏭️ Skipped (Already Exists)", skipped)
    st.metric("⚠️ Errors", errors)

    if all_horses:
        with st.expander("📋 Horses Processed"):
            st.write(sorted(all_horses))