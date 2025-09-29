import streamlit as st  # Needed for Firebase secrets
from datetime import datetime
from firebase_utils import (
    get_db,
    load_race_records,
    update_horse_race_record,
    serialize_data,
    deserialize_data
)

def clean_horse_name(name: str) -> str:
    """Strip '(Your Horse)', '⭐', or extra tags from horse names."""
    return name.split(" (")[0].replace("⭐", "").strip()

def rehydrate_global_horse_history(limit=200):
    """Replay all race records to rebuild global_horse_history."""
    print("🔄 Starting global horse history rehydration...")

    race_records = load_race_records(limit=limit)
    if not race_records:
        print("⚠️ No race records found!")
        return

    count = 0
    for race_id, race_data in race_records.items():
        results = race_data.get('results', [])
        track_condition = race_data.get('track_condition', 'normal')
        race_name = race_data.get('race_name', 'standard')
        race_date = race_data.get('date', datetime.now().isoformat())

        for horse_result in results:
            try:
                horse_name = clean_horse_name(horse_result.get('name', ''))
                if not horse_name:
                    continue

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
                count += 1
                print(f"✅ Updated: {horse_name} from {race_id}")
            except Exception as e:
                print(f"❌ Error updating {horse_result.get('name')} in {race_id}: {e}")
    
    print(f"🎉 Rehydration complete! {count} horse entries updated across {len(race_records)} races.")

# If running directly
if __name__ == "__main__":
    rehydrate_global_horse_history(limit=300)  # or 1000+ for full rebuild