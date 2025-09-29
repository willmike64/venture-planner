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
    from betting_system import render_betting_interface as legacy_betting_ui
    legacy_betting_ui()

# Optional hook for testing
if __name__ == "__main__":
    render_betting_interface()
