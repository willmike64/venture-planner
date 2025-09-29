import os
import shutil

# --- Paths ---
SOURCE_FILE = "betting_system.py"
TARGET_FOLDER = "betting"
os.makedirs(TARGET_FOLDER, exist_ok=True)

# --- Templates ---
firebase_bets_code = '''\
from firebase_utils import save_bets, load_bets, save_user_money, load_global_horse_history

def persist_bets(bet_pools):
    try:
        save_bets(bet_pools)
    except Exception as e:
        print(f"🔥 Firebase Error (save_bets): {e}")

def persist_user_money(user_id, money):
    try:
        save_user_money(user_id, money)
    except Exception as e:
        print(f"🔥 Firebase Error (save_user_money): {e}")

def fetch_global_horse_history():
    try:
        return load_global_horse_history()
    except Exception as e:
        print(f"🔥 Firebase Error (load_global_horse_history): {e}")
        return {}
'''

betting_logic_code = '''\
def calculate_parimutuel_odds(bet_pool):
    total_pool = sum(bet_pool.values())
    odds = {}
    for horse, amount in bet_pool.items():
        odds[horse] = round(total_pool / amount, 2) if amount else 10.0
    return odds

def calculate_win_place_show_payouts(race_results, bet_pools):
    payouts = {'win': {}, 'place': {}, 'show': {}}
    if not race_results:
        return payouts

    first = race_results[0][0]['name'] if isinstance(race_results[0][0], dict) else race_results[0][0]
    second = race_results[1][0]['name'] if len(race_results) > 1 and isinstance(race_results[1][0], dict) else (race_results[1][0] if len(race_results) > 1 else None)
    third = race_results[2][0]['name'] if len(race_results) > 2 and isinstance(race_results[2][0], dict) else (race_results[2][0] if len(race_results) > 2 else None)

    def assign_payout(pool, winners):
        total = sum(pool.values())
        bets_on_winners = sum(pool.get(w, 0) for w in winners)
        if bets_on_winners > 0:
            return {w: total / bets_on_winners for w in winners if w in pool}
        return {}

    payouts['win'] = assign_payout(bet_pools.get('win', {}), [first])
    payouts['place'] = assign_payout(bet_pools.get('place', {}), list(filter(None, [first, second])))
    payouts['show'] = assign_payout(bet_pools.get('show', {}), list(filter(None, [first, second, third])))

    return payouts

def get_effective_bet(amount, is_own_horse, partnership_bonus=1.0):
    owner_bonus = 1.5 if is_own_horse else 1.0
    return amount * owner_bonus * partnership_bonus

def clean_horse_name(name):
    return name.split(" (YOUR HORSE")[0].strip()
'''

betting_ui_stub = '''\
import streamlit as st
from betting.betting_logic import (
    calculate_parimutuel_odds,
    calculate_win_place_show_payouts,
    get_effective_bet,
    clean_horse_name
)
from betting.firebase_bets import (
    persist_bets,
    persist_user_money,
    fetch_global_horse_history
)

def render_betting_interface():
    st.header("🎫 Racetrack Betting Windows")
    st.markdown("⚠️ Full UI implementation goes here... Patch your betting_system.py logic here.")

# Optional hook for testing
if __name__ == "__main__":
    render_betting_interface()
'''

# --- Save individual modules ---
with open(os.path.join(TARGET_FOLDER, "betting_logic.py"), "w") as f:
    f.write(betting_logic_code)

with open(os.path.join(TARGET_FOLDER, "firebase_bets.py"), "w") as f:
    f.write(firebase_bets_code)

with open(os.path.join(TARGET_FOLDER, "betting_ui.py"), "w") as f:
    f.write(betting_ui_stub)

# --- Backup and Cleanup ---
if os.path.exists(SOURCE_FILE):
    shutil.copyfile(SOURCE_FILE, os.path.join(TARGET_FOLDER, "deprecated_betting_system.py"))
    print(f"🗃️  Backed up old file to: {TARGET_FOLDER}/deprecated_betting_system.py")

print(f"✅ Betting system split completed into: {TARGET_FOLDER}/")