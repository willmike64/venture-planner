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
