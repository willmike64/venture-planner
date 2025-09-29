# horse_racing.py - Enhanced animated horse racing
import streamlit as st # type: ignore
import random
import time
import copy
from datetime import datetime, timedelta
from firebase_utils import save_user_data, get_user_data
from jockeys import get_available_jockey

# Import auto-save function - fallback if not available
try:
                  st.session_state.logs.append(f"🏆 Your racing horses earned ${total_earnings} while you were away!")
    
    st.session_state.last_offline_check = current_time

# --- STREAMLIT APP ---
def render_horse_racing():
    st.title("🐎 Gold Rush Horse Racing Showdown")

    # Initialize gold and casino
    if 'money' not in st.session_state:
        st.session_state.money = st.session_state.get('money', 50.0)

    if 'casino' not in st.session_state:
        st.session_state.casino = {"cash": 0.0, "transactions": []}

    # Process offline earnings
    process_offline_earnings()

    # Get current racing pool (mix of student and default horses)
    st.session_state.horses = get_global_racing_pool()
    
    # Check if player has entered their horse
    if 'horse_entered_in_race' not in st.session_state:
        st.session_state.horse_entered_in_race = None
    
    if 'player_id' not in st.session_state:
        st.session_state.player_id = f"player_{int(time.time())}_{random.randint(1000, 9999)}"
    
    # Add player's horse if they've entered one
    if st.session_state.horse_entered_in_race:
        entered_horse_id = st.session_state.horse_entered_in_race
        player_horse = next((h for h in st.session_state.get('owned_horses', []) if h['id'] == entered_horse_id), None)
        
        if player_horse:
            player_horse_name = f"{player_horse['name']} (Your Horse)"
            
            # Remove any existing player horse entry
            st.session_state.horses = [h for h in st.session_state.horses if not h['name'].endswith('(Your Horse)')]
            
            # Add player's horse with enhanced stats
            player_race_horse = {
                "name": player_horse_name,
                "base_speed": player_horse['speed'],
                "endurance": player_horse['stamina'],
                "mudder": player_horse['breed'] in ['Quarter Horse', 'Mustang'],
                "temperament": "proud" if player_horse['breed'] == 'Thoroughbred' else "steady",
                "race_history": [],
                "stable": "Your Stable",
                "story": f"Your prized {player_horse['name']}, trained and cared for by you!",
                "player_owned": True,
                "horse_id": player_horse['id']
            }
            st.session_state.horses.append(player_race_horse)
    
    st.write(f"**Gold:** {st.session_state.money:.2f}")
    st.write(f"**Casino Revenue:** ${st.session_state.casino['cash']:.2f}")
    
    # Horse Entry Section
    owned_horses = st.session_state.get('owned_horses', [])
    healthy_horses = [h for h in owned_horses if h['health'] > 50]  # Need >50 health to race
    
    if healthy_horses and not st.session_state.horse_entered_in_race:
        st.markdown("### 🏁 Enter Your Horse")
        
        selected_horse = st.selectbox(
            "Choose horse to enter:",
            healthy_horses,
            format_func=lambda h: f"{h['name']} ({h['breed']}) - Speed: {h['speed']:.1f}, Stamina: {h['stamina']:.1f}, Health: {h['health']}"
        )
        
        col1, col2 = st.columns([2, 1])
        with col1:
            if selected_horse is not None:
                st.write(f"🐎 **{selected_horse['name']}** ({selected_horse['breed']})")
                st.write(f"⚡ Speed: {selected_horse['speed']:.1f} | 💪 Stamina: {selected_horse['stamina']:.1f} | ❤️ Health: {selected_horse['health']}")
                st.write(f"🏆 Record: {selected_horse['wins']}/{selected_horse['races']} wins")
            st.caption("Entry fee: $50 (paid from cash or added to stable liabilities)")
        
        with col2:
            if st.button("🏁 Enter Race ($50)", key="enter_horse"):
                # Always allow race entry - handle payment through liability system
                try:
                    from stable_business import handle_race_entry_fee
                    handle_race_entry_fee(50, "race entry")
                except ImportError:
                    # Fallback if stable_business not available
                    if st.session_state.money >= 50:
                        st.session_state.money -= 50
                    else:
                        st.warning("Not enough money for entry fee, but racing anyway!")
                
                if selected_horse is not None:
                    st.session_state.horse_entered_in_race = selected_horse['id']
                    st.success(f"🎆 {selected_horse['name']} entered in the race!")
                    if 'logs' not in st.session_state or st.session_state.logs is None or not isinstance(st.session_state.logs, list):
                        st.session_state.logs = []
                    st.session_state.logs.append(f"🏁 Entered {selected_horse['name']} in horse race for $50")
                    st.rerun()
                else:
                    st.error("No horse selected to enter in the race.")
        
        st.markdown("---")
    
    elif st.session_state.horse_entered_in_race:
        entered_horse = next((h for h in owned_horses if h['id'] == st.session_state.horse_entered_in_race), None)
        if entered_horse:
            st.success(f"🏆 **{entered_horse['name']} is entered in today's race!** Look for '(Your Horse)' in the lineup below.")
            if st.button("❌ Withdraw Horse", key="withdraw_horse"):
                st.session_state.horse_entered_in_race = None
                st.info(f"Withdrew {entered_horse['name']} from the race.")
                st.rerun()
    
    elif owned_horses and not healthy_horses:
        st.warning("⚠️ Your horses need >50 health to race. Visit the Stable to care for them!")
    
    elif not owned_horses:
        st.info("💡 **Tip:** Buy Thoroughbreds at the Stable and add them to your Racing Stable to compete automatically!")
    
    # Show current racing stable status
    racing_horses = [h for h in st.session_state.get('owned_horses', []) if h.get('in_racing_stable')]
    if racing_horses:
        st.success(f"🏆 **Your Racing Stable:** {racing_horses[0]['name']} is competing in all races!")
    
    # Track condition
    track = random.choice(TRACK_CONDITIONS)
    st.subheader(f"Today's Track: **{track.upper()}**")

    # Show racing pool composition
    student_count = len([h for h in st.session_state.horses if h.get('student_owned')])
    default_count = len(st.session_state.horses) - student_count
    st.info(f"🏆 **Racing Pool:** {student_count} Student Horses, {default_count} House Horses")
    
    # Horse Profiles Display
    st.markdown("### 🐴 Horse Profiles")
    profile_cols = st.columns(4)
    for i, horse in enumerate(st.session_state.horses):
        with profile_cols[i % 4]:
            # Highlight student horses
            if horse.get('student_owned'):
                st.markdown(f"**🌟 {horse['name']}**")
            else:
                st.markdown(f"**{horse['name']}**")
            st.caption(f"🏠 *{horse['stable']}*")
            st.write(f"⚡ Speed: {horse['base_speed']}/10")
            st.write(f"💪 Endurance: {horse['endurance']}/10")
            st.write(f"🌧️ Mudder: {'Yes' if horse['mudder'] else 'No'}")
            st.write(f"📖 {horse['story']}")
            if horse['race_history']:
                recent = horse['race_history'][-3:]
                recent_positions = [str(r['position']) for r in recent if r.get('position') is not None]
                st.write(f"📈 Recent: {', '.join(recent_positions)}")
            st.markdown("---")

    # Show player's horse prominently if they have one entered
    player_horse_in_race = None
    for horse in st.session_state.horses:
        if horse['name'].endswith('(Your Horse)'):
            player_horse_in_race = horse
            break
    
    if player_horse_in_race:
        st.markdown("### 🌟 Your Horse in Today's Race")
        with st.container():
            st.markdown(f"**🐎 {player_horse_in_race['name']}**")
            col1, col2 = st.columns(2)
            col1.write(f"⚡ Speed: {player_horse_in_race['base_speed']:.1f}/10")
            col1.write(f"💪 Endurance: {player_horse_in_race['endurance']:.1f}/10")
            col2.write(f"🏠 Stable: {player_horse_in_race['stable']}")
            col2.write(f"📖 {player_horse_in_race['story']}")
        st.markdown("---")
    
    # Betting Interface
    st.markdown("### 🎫 Place Your Bet")
    bet_cols = st.columns([2, 1, 1])
    
    with bet_cols[0]: # Use st.session_state.horses for the selectbox options
        selected_horse = st.selectbox(
            "Choose Your Horse", st.session_state.horses, format_func=lambda x: x["name"] if x else "None"
        )
    
    with bet_cols[1]:
        bet_type = st.selectbox("Bet Type", ["Win", "Place", "Show"])
    
    with bet_cols[2]:
        player_money = int(st.session_state.money)
        if player_money >= 1:
            wager = st.number_input(
                "Wager ($)", min_value=1, max_value=player_money, 
                value=min(10, player_money)
            )
        else:
            st.error("💸 You need at least $1 to place a bet!")
            wager = 0

    # Horse Enhancement Shop
    st.markdown("### 🛒 Pre-Race Horse Enhancements")
    st.write("💡 *Give your horse the edge with these questionable but effective treats!*")
    
    enhancement_cols = st.columns(3)
    selected_item = "None"
    
    with enhancement_cols[0]:
        selected_item = st.selectbox("Choose Enhancement:", ["None"] + list(HORSE_ITEMS.keys()))
    
    with enhancement_cols[1]:
        if selected_item and selected_item != "None":
            item_info = HORSE_ITEMS[selected_item]
            st.write(f"💰 Price: ${item_info['price']}")
            st.write(f"⚡ Boost: +{item_info['boost']}")
    
    with enhancement_cols[2]:
        if selected_item and selected_item != "None":
            item_info = HORSE_ITEMS[selected_item]
            st.write(f"📝 {item_info['description']}")
    
    # Generate odds for all horses (including player's horse if entered)
    if 'horse_odds' not in st.session_state:
        st.session_state.horse_odds = {}
    
    # Update odds to include all current horses
    for horse in st.session_state.horses:
        if horse['name'] not in st.session_state.horse_odds:
            st.session_state.horse_odds[horse['name']] = round(random.uniform(1.5, 8.0), 1)
    
    st.markdown("### 🎲 Current Odds")
    odds_cols = st.columns(4)
    for i, horse in enumerate(st.session_state.horses):
        with odds_cols[i % 4]:
            odds = st.session_state.horse_odds.get(horse['name'], round(random.uniform(1.5, 8.0), 1))
            st.write(f"**{horse['name']}**: {odds}:1")

    # START RACE - The animated racing functionality
    if st.button("🏁 Start Race!"):
        total_cost = wager
        if selected_item and selected_item != "None":
            total_cost += HORSE_ITEMS[selected_item]["price"]
        
        if total_cost > st.session_state.money:
            st.error("Not enough gold for bet and enhancement!")
            st.stop()
        
        st.session_state.money -= total_cost
        
        # Log transaction for business tracking
        if 'logs' not in st.session_state:
            st.session_state.logs = []
        st.session_state.logs.append(f"🎰 Horse Racing: Wagered ${total_cost:.2f} on {selected_horse['name'] if selected_horse else 'Unknown'} ({bet_type})")
        
        # Show jockey banter
        for i, horse in enumerate(st.session_state.horses):
            jockey = JOCKEYS[i % len(JOCKEYS)]
            banter = get_jockey_banter(jockey["name"], track, horse["name"])
            st.write(f"👨‍🌾 {banter}")
        
        # Show enhancement effect
        item_boost = 0
        if selected_item and selected_item != "None" and selected_horse is not None:
            item_boost = HORSE_ITEMS[selected_item]["boost"]
            funny_messages = [
                f"🌾 {selected_horse['name']} devours the {selected_item} and starts prancing like a show pony!",
                f"⚡ {selected_horse['name']} eyes glow after eating {selected_item}. The other horses look nervous!",
                f"🎭 {selected_horse['name']} does a little dance after the {selected_item}. The crowd goes wild!",
                f"🚀 {selected_horse['name']} practically levitates after consuming {selected_item}!",
                f"🎪 {selected_horse['name']} starts neighing the national anthem after eating {selected_item}!"
            ]
            st.success(random.choice(funny_messages))

        # Compute speeds for all horses
        results = [] # This will store (horse_object, speed)
        for h in st.session_state.horses: # Iterate over the actual horse objects in session state
            jockey = JOCKEYS[st.session_state.horses.index(h) % len(JOCKEYS)] # Use st.session_state.horses for index
            boost = item_boost if (selected_horse is not None and h["name"] == selected_horse["name"]) else 0 # Apply boost if it's the selected horse
            results.append((copy.deepcopy(h), calculate_adjusted_speed(h, jockey, track, boost)))

        # 🌟 ANIMATED RACE - This is the key enhancement! 🌟
        st.markdown("### 🏁 Race in Progress!")
        race_area = st.empty()
        
        horse_emojis = ["🐎", "🐴", "🏇"]
        positions = {h[0]["name"]: 0 for h in results}
        finish_line = 30
        finished = []
        
        # Real-time animated race progress
        while len(finished) < len(results):
            time.sleep(0.15)  # Animation delay
            for horse_data, speed in results: # horse_data here is a deepcopy
                if horse_data["name"] not in finished:
                    # Speed affects probability of movement
                    move_prob = min(speed / 10.0, 0.9)
                    if random.random() < move_prob:
                        positions[horse_data["name"]] += random.randint(1, 2)
                    
                    if positions[horse_data["name"]] >= finish_line:
                        positions[horse_data["name"]] = finish_line
                        if horse_data["name"] not in finished:
                            finished.append(horse_data["name"])
            
            # 🎨 Display animated race progress bars
            with race_area.container():
                st.markdown("### 🐎 **LIVE RACE PROGRESS**")
                for horse_data, _ in results:
                    name = horse_data["name"]
                    pos = positions[name]
                    remaining = finish_line - pos
                    
                    # Create visual progress bar with emojis
                    progress_bar = "🏇" + "═" * pos + "🏁" + " " * remaining
                    
                    # Highlight player's horse
                    if name.endswith('(Your Horse)'):
                        st.markdown(f"**🌟 {name:20} | {progress_bar}**")
                    else:
                        st.text(f"{name:20} | {progress_bar}")

        # Final results - sort by speed (higher speed = better position)
        final_results = [(h, s) for h, s in results]
        final_results.sort(key=lambda x: x[1], reverse=True)  # Sort by speed, highest first
        
        st.markdown("### 🏆 **FINAL RACE RESULTS**")
        for idx, (h, speed) in enumerate(final_results):
            position_emoji = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "🏃"
            if h['name'].endswith('(Your Horse)'):
                st.markdown(f"**{position_emoji} {idx+1}. {h['name']} — Speed: {speed:.1f}**")
            else:
                st.write(f"{position_emoji} {idx+1}. {h['name']} — Speed: {speed:.1f}")

        # Update race history
        for idx, (h, _) in enumerate(final_results):
            update_race_history(h, idx + 1, random.uniform(120, 180)) # Pass the horse object (which is a deepcopy from results)
        
        # Calculate winnings based on bet type and odds
        winner = final_results[0][0] if final_results else None
        place_horses = [r[0] for r in final_results[:2]]
        show_horses = [r[0] for r in final_results[:3]]
        
        winnings = 0
        won = False
        
        if selected_horse is not None:
            if bet_type == "Win" and winner and winner.get("name") == selected_horse.get("name"):
                odds = st.session_state.horse_odds.get(selected_horse["name"], 3.0)
                winnings = wager * odds
                won = True
            elif bet_type == "Place" and selected_horse in place_horses:
                odds = st.session_state.horse_odds.get(selected_horse["name"], 3.0)
                winnings = wager * (odds * 0.5)
                won = True
            elif bet_type == "Show" and selected_horse in show_horses:
                odds = st.session_state.horse_odds.get(selected_horse["name"], 3.0)
                winnings = wager * (odds * 0.3)
                won = True
        
        # Track casino revenue from horse racing
        if 'casino' not in st.session_state:
            st.session_state.casino = {"cash": 0.0, "transactions": []}
        
        # Ensure transactions list exists
        if "transactions" not in st.session_state.casino:
            st.session_state.casino["transactions"] = []
        
        # Record the transaction
        horse_name = selected_horse["name"] if selected_horse else "Unknown"
        is_own_horse = (selected_horse and selected_horse.get('student_owned') and selected_horse.get('owner_id') == st.session_state.get('player_id')) or \
                      (selected_horse and selected_horse.get('name', '').endswith('(Your Horse)'))
        transaction = {
            "type": "horse_racing",
            "amount": total_cost,
            "horse": horse_name,
            "bet_type": bet_type,
            "won": won,
            "payout": winnings if won else 0,
            "own_horse": is_own_horse
        }
        st.session_state.casino["transactions"].append(transaction)
        
        if won:
            st.balloons()
            st.success(f"🎉 **YOU WON!** +${winnings:.2f} gold")
            st.session_state.money += winnings
            # Auto-save after winning money
            auto_save_user_data()
            
            # Track business revenue from betting winnings
            if 'business_financials' in st.session_state:
                try:
                    from stable_business import track_revenue
                    track_revenue(winnings, 'betting')
                except ImportError:
                    pass
            
            # Casino loses money on payout
            st.session_state.casino["cash"] -= (winnings - total_cost)
            
            # Special bonus if player's own horse won (student or entered horse)
            is_student_horse = selected_horse and selected_horse.get('student_owned') and selected_horse.get('owner_id') == st.session_state.get('player_id')
            is_entered_horse = selected_horse and selected_horse.get('name', '').endswith('(Your Horse)')
            
            if is_student_horse or is_entered_horse:
                bonus = 100
                st.session_state.money += bonus
                st.success(f"🎆 **OWNER'S BONUS!** Your horse won! +${bonus} extra prize money!")
                if 'logs' not in st.session_state:
                    st.session_state.logs = []
                st.session_state.logs.append(f"🐎 Your horse won the race! Earned ${bonus} owner's bonus!")
                
                # Improve horse stats slightly from winning
                for horse in st.session_state.get('owned_horses', []):
                    if (is_student_horse and horse['id'] == selected_horse.get('horse_id')) or \
                       (is_entered_horse and f"{horse['name']} (Your Horse)" == selected_horse['name']):
                        horse['speed'] = min(horse['speed'] * 1.05, horse['speed'] + 0.1)
                        horse['stamina'] = min(horse['stamina'] + 5, 200)
                        st.info(f"💪 {horse['name']} gained experience from winning! Stats improved slightly.")
                        break
        else:
            st.warning("💔 Better luck next time…")
            # Casino keeps the bet money
            st.session_state.casino["cash"] += total_cost
            st.session_state.logs.append(f"🎰 Casino earned ${total_cost:.2f} from horse racing")
            
            # Consolation if player's horse lost
            is_student_horse = selected_horse and selected_horse.get('student_owned') and selected_horse.get('owner_id') == st.session_state.get('player_id')
            is_entered_horse = selected_horse and selected_horse.get('name', '').endswith('(Your Horse)')
            
            if is_student_horse or is_entered_horse:
                consolation = 25
                st.session_state.money += consolation
                st.info(f"🐎 **OWNER'S CONSOLATION:** Even though your horse didn't win, you earned ${consolation} for participating!")
        
        # Refresh odds for next race and reset horse entry
        st.session_state.horse_odds = {h['name']: round(random.uniform(1.5, 8.0), 1) for h in st.session_state.horses}
        st.session_state.horse_entered_in_race = None  # Reset for next race

    # View detailed history and casino stats
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📜 View Horse Histories"):
            st.markdown("### 📊 Horse Racing Records")
            for h in st.session_state.horses:
                if h["race_history"]:
                    st.write(f"**{h['name']}** ({h['stable']})")
                    st.write(f"Story: {h['story']}")
                    for r in h["race_history"]:
                        st.write(f" - Position {r['position']} (Time: {r['time']:.1f}s)")
                    st.markdown("---")
                else:
                    st.write(f"**{h['name']}** - No race history yet")
    
    with col2:
        if st.button("💰 View Casino Stats"):
            if 'casino' in st.session_state:
                st.markdown("### 🎰 Casino Horse Racing Revenue")
                st.write(f"**Total Revenue:** ${st.session_state.casino['cash']:.2f}")
                st.write(f"**Total Races:** {len(st.session_state.casino['transactions'])}")
                
                if st.session_state.casino['transactions']:
                    st.markdown("**Recent Transactions:**")
                    for i, trans in enumerate(st.session_state.casino['transactions'][-5:]):
                        result = "WON" if trans['won'] else "LOST"
                        st.write(f"{i+1}. ${trans['amount']:.2f} on {trans['horse']} ({trans['bet_type']}) - {result}")
            else:
                st.write("No casino data yet.")

    # Legacy compatibility for older betting system
    with st.expander("📜 Legacy Race History"):
        history = st.session_state.get(LEADERBOARD_KEY, get_user_data("race_history") or [])
        for entry in history:
            if isinstance(entry, dict) and 'winners' in entry:
                st.markdown(f"{entry['time']} — 🏁 {entry['track']} track — 🥇 {entry['winners'][0]} | 🥈 {entry['winners'][1]} | 🥉 {entry['winners'][2]}")

# Entry point for standalone testing
if __name__ == "__main__":
    render_horse_racing()rom app import auto_save_user_data
except ImportError:
    def auto_save_user_data():
        """Fallback if import fails"""
        pass

# AI Jockey banter - optional OpenAI integration
try:
    import openai # type: ignore
    client = openai.OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
    OPENAI_AVAILABLE = True
except (ImportError, KeyError):
    OPENAI_AVAILABLE = False

TRIPLE_CROWN = ["Kentucky Derby", "Preakness Stakes", "Belmont Stakes"]

def run_triple_crown(player_horse, jockey):
    for leg in TRIPLE_CROWN:
        st.subheader(f"🏆 {leg}")
        won = run_single_race(player_horse, jockey, championship=True)
        if not won:
            st.error(f"{player_horse['name']} lost at {leg}. Triple Crown attempt failed.")
            return False
    st.success(f"🎉 {player_horse['name']} WON THE TRIPLE CROWN! Legendary!")
    st.balloons()
    return True

def run_single_race(player_horse, jockey, championship=False):
    """Run a single race and return True if player horse wins."""
    track = random.choice(TRACK_CONDITIONS)
    
    # Create race field with player horse and random opponents
    race_horses = [player_horse]
    opponents = random.sample([h for h in HORSES if h['name'] != player_horse['name']], 3)
    race_horses.extend(opponents)
    
    # Calculate speeds
    results = []
    for horse in race_horses:
        speed = calculate_adjusted_speed(horse, jockey, track)
        results.append((horse, speed))
    
    # Sort by speed (highest wins)
    results.sort(key=lambda x: x[1], reverse=True)
    
    # Display results
    st.write(f"Track: {track.upper()}")
    for i, (horse, speed) in enumerate(results):
        position_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏃"
        st.write(f"{position_emoji} {i+1}. {horse['name']} - Speed: {speed:.1f}")
    
    # Return True if player horse won
    return results[0][0]['name'] == player_horse['name']

# --- DATA (Initial data, will be copied to session state) ---
HORSES = [
    {"name": "Blazing Fury", "base_speed": 9.0, "endurance": 8.5, "mudder": True, "temperament": "fiery", "race_history": [], "stable": "Fire Mountain Ranch", "story": "Born in a lightning storm, this fiery stallion has never lost his wild spirit."},
    {"name": "Swamp Donkey", "base_speed": 7.5, "endurance": 9.0, "mudder": True, "temperament": "lazy", "race_history": [], "stable": "Bayou Stables", "story": "Don't let the name fool you - this mudder thrives in the worst conditions."},
    {"name": "Silent Thunder", "base_speed": 8.2, "endurance": 7.8, "mudder": False, "temperament": "calm", "race_history": [], "stable": "Quiet Valley Farm", "story": "Moves like a whisper but strikes like lightning when it counts."},
    {"name": "Iron Hoof", "base_speed": 8.8, "endurance": 8.0, "mudder": False, "temperament": "aggressive", "race_history": [], "stable": "Steel Ridge Stables", "story": "Forged in the mines, this horse's hooves ring like anvils on the track."},
    {"name": "Whiskey Tango", "base_speed": 8.5, "endurance": 8.3, "mudder": True, "temperament": "wild", "race_history": [], "stable": "Saloon Stables", "story": "Named after a bar fight, this horse dances through chaos."},
    {"name": "Thunderbolt", "base_speed": 8.7, "endurance": 8.1, "mudder": False, "temperament": "aggressive", "race_history": [], "stable": "Storm Riders", "story": "Fast as lightning, twice as dangerous."},
    {"name": "Golden Wind", "base_speed": 8.0, "endurance": 8.8, "mudder": False, "temperament": "calm", "race_history": [], "stable": "Sunnyvale Ranch", "story": "Graceful as a prairie breeze, steady as the sunrise."},
    {"name": "Eclipse", "base_speed": 8.4, "endurance": 8.2, "mudder": True, "temperament": "steady", "race_history": [], "stable": "Moonlight Stable", "story": "Born during a solar eclipse, destined for greatness."},
    {"name": "Desert Storm", "base_speed": 8.9, "endurance": 7.9, "mudder": False, "temperament": "fierce", "race_history": [], "stable": "Sahara Stables", "story": "Raised in the harsh desert, knows only victory or dust."},
    {"name": "Majestic", "base_speed": 8.1, "endurance": 8.6, "mudder": True, "temperament": "proud", "race_history": [], "stable": "Royal Farms", "story": "Carries himself like royalty, races like a champion."},
    {"name": "Tornado", "base_speed": 8.6, "endurance": 7.7, "mudder": False, "temperament": "wild", "race_history": [], "stable": "Cyclone Stables", "story": "Unpredictable as a twister, devastating when unleashed."},
    {"name": "Midnight", "base_speed": 7.8, "endurance": 8.9, "mudder": True, "temperament": "patient", "race_history": [], "stable": "Twilight Stables", "story": "Waits for the perfect moment, then strikes in the darkness."}
]

JOCKEYS = [
    {"name": "Slick Rick", "skill": 8.5, "aggression": 6.5, "reaction": 9.0, "endurance": 8.0},
    {"name": "Anxious Annie", "skill": 7.0, "aggression": 3.0, "reaction": 6.0, "endurance": 7.5},
    {"name": "Billy Biceps", "skill": 8.0, "aggression": 8.0, "reaction": 7.5, "endurance": 8.5},
    {"name": "No-Nose Ned", "skill": 6.0, "aggression": 5.0, "reaction": 4.0, "endurance": 6.5},
    {"name": "Calm Carlita", "skill": 7.8, "aggression": 2.5, "reaction": 8.2, "endurance": 8.0},
]

TRACK_CONDITIONS = ["dry", "wet", "muddy", "frozen"]

# Horse Enhancement Items
HORSE_ITEMS = {
    "🌾 Magic Oats": {"price": 25, "boost": 1.5, "description": "These oats are so good, horses start doing backflips!"},
    "⚡ Lightning Carrots": {"price": 35, "boost": 2.0, "description": "Carrots struck by lightning. Horse goes ZOOM!"},
    "🍯 Honey Energy Bars": {"price": 20, "boost": 1.2, "description": "Sweet treats that make horses hum show tunes."},
    "🌶️ Spicy Peppers": {"price": 30, "boost": 1.8, "description": "Horse breathes fire and runs like the devil's chasing them!"},
    "🧙‍♂️ Wizard's Brew": {"price": 50, "boost": 2.5, "description": "Mysterious potion. Horse may sprout wings (results not guaranteed)."}
}

# Legacy constants for compatibility
LEADERBOARD_KEY = "race_leaderboard"
BET_POOL_KEY = "parimutuel_bet_pool"

def get_jockey_banter(name, condition, horse):
    """Get AI-generated jockey banter if OpenAI is available, otherwise use fallback"""
    if OPENAI_AVAILABLE and client.api_key:
        prompt = f"You are {name}, a quirky jockey. You're racing under {condition} conditions on a horse named {horse}. Give a short, fun, strategic line."
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a horse racing jockey."},
                          {"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            return content.strip() if content else f"{name} nods silently."
        except Exception:
            pass
    
    # Fallback banter
    banters = [
        f"{name}: 'Time to show them what we're made of, {horse}!'",
        f"{name}: 'This {condition} track won't slow us down!'",
        f"{name}: 'Let's give them a race to remember!'",
        f"{name}: '{horse} and I are ready for anything!'",
        f"{name}: 'May the best horse win... which will be us!'"
    ]
    return random.choice(banters)

# --- RACE LOGIC ---
def calculate_adjusted_speed(horse, jockey, track, item_boost=0):
    # Handle both 'speed' (user horses) and 'base_speed' (HORSES constant) structures
    horse_speed = horse.get("speed", horse.get("base_speed", 5.0))
    base = horse_speed + jockey["skill"] * 0.2 + jockey["reaction"] * 0.1 + item_boost
    if track == "muddy":
        # Check if horse has 'mudder' attribute, default to False
        base += 1.5 if horse.get("mudder", False) else -1.0
    if jockey["aggression"] > 7 and horse.get("temperament", "calm") == "fiery":
        base += 0.5
    return round(base + random.uniform(-1.0, 1.0), 2)

def update_race_history(horse, position, t):
    """Update the race history for a horse in session state."""
    # Find the actual horse object in session state and update its history
    for h in st.session_state.horses:
        if h["name"] == horse["name"]:
            h["race_history"].append({"position": position, "time": t})
            if len(h["race_history"]) > 3:
                h["race_history"] = h["race_history"][-3:]
            
            # If this is a student-owned horse, update their stable horse
            if h.get('student_owned') and h.get('horse_id'):
                for owned_horse in st.session_state.get('owned_horses', []):
                    if owned_horse['id'] == h['horse_id']:
                        owned_horse['races'] += 1
                        prize = 200 if position == 1 else 100 if position == 2 else 50 if position == 3 else 25
                        owned_horse['earnings'] += prize
                        
                        # Only give money to current player if it's their horse
                        if h.get('owner_id') == st.session_state.get('player_id'):
                            st.session_state.money += prize
                            
                            # Track business revenue
                            if 'business_financials' in st.session_state:
                                try:
                                    from stable_business import track_revenue
                                    track_revenue(prize, 'race')
                                    st.session_state.business_metrics["total_race_winnings"] += prize
                                except ImportError:
                                    pass
                            
                            if 'logs' not in st.session_state:
                                st.session_state.logs = []
                            st.session_state.logs.append(f"� {owned_horse['name']} earned ${prize} prize money!")
                        
                        if position == 1:
                            owned_horse['wins'] += 1
                        
                        # Reduce health from racing
                        owned_horse['health'] = max(20, owned_horse['health'] - random.randint(5, 15))
                        break
            
            # If this is a player-entered horse (old system), update their stable horse too
            if h.get('player_owned') and h.get('horse_id'):
                for owned_horse in st.session_state.get('owned_horses', []):
                    if owned_horse['id'] == h['horse_id']:
                        owned_horse['races'] += 1
                        if position == 1:
                            owned_horse['wins'] += 1
                            prize = 200 if position == 1 else 100 if position == 2 else 50
                            owned_horse['earnings'] += prize
                            st.session_state.money += prize
                            
                            # Track business revenue
                            if 'business_financials' in st.session_state:
                                try:
                                    from stable_business import track_revenue
                                    track_revenue(prize, 'race')
                                    st.session_state.business_metrics["total_race_winnings"] += prize
                                except ImportError:
                                    pass
                            
                            if 'logs' not in st.session_state:
                                st.session_state.logs = []
                            st.session_state.logs.append(f"🏆 {owned_horse['name']} won ${prize} prize money!")
                        
                        # Reduce health from racing
                        owned_horse['health'] = max(20, owned_horse['health'] - random.randint(5, 15))
                        break
            break

def get_global_racing_pool():
    """Get the global racing pool with student horses replacing default horses."""
    from datetime import datetime
    
    # Collect all student horses in racing stables
    student_horses = []
    if 'owned_horses' in st.session_state:
        for horse in st.session_state.owned_horses:
            if horse.get('in_racing_stable') and horse['breed'] == 'Thoroughbred':
                student_horses.append({
                    "name": f"{horse['name']} ({horse.get('owner_id', 'Unknown')[:8]})",
                    "base_speed": horse['speed'],
                    "endurance": horse['stamina'],
                    "mudder": False,
                    "temperament": "proud",
                    "race_history": [],
                    "stable": "Student Stable",
                    "story": f"A prized thoroughbred owned by a Gold Rush student!",
                    "student_owned": True,
                    "horse_id": horse['id'],
                    "owner_id": horse.get('owner_id')
                })
    
    # Fill remaining slots with default horses
    total_horses = 12
    remaining_slots = total_horses - len(student_horses)
    default_horses = copy.deepcopy(HORSES[:remaining_slots])
    
    return student_horses + default_horses

def process_offline_earnings():
    """Process earnings for student horses from races that happened while offline."""
    from datetime import datetime
    
    if 'last_offline_check' not in st.session_state:
        st.session_state.last_offline_check = datetime.now()
        return
    
    current_time = datetime.now()
    
    # Handle the case where last_offline_check might be a string (from Firebase)
    last_check = st.session_state.last_offline_check
    if isinstance(last_check, str):
        try:
            # Try to parse the ISO format string back to datetime
            last_check = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            # If parsing fails, reset to current time
            st.session_state.last_offline_check = current_time
            return
    elif not isinstance(last_check, datetime):
        # If it's neither string nor datetime, reset
        st.session_state.last_offline_check = current_time
        return
    
    time_diff = current_time - last_check
    hours_offline = time_diff.total_seconds() / 3600
    
    # Simulate races every 2 hours
    races_missed = int(hours_offline / 2)
    
    if races_missed > 0 and 'owned_horses' in st.session_state:
        total_earnings = 0
        for horse in st.session_state.owned_horses:
            if horse.get('in_racing_stable'):
                # Simulate race results based on horse stats
                for _ in range(races_missed):
                    # Higher speed = better chance of winning
                    win_chance = (horse['speed'] - 5) / 5
                    # Enhanced Tamagotchi-style race tracking
                    won_race = random.random() < win_chance * 0.3
                    if won_race:
                        earnings = random.randint(50, 150)
                        horse['earnings'] += earnings
                        horse['wins'] += 1
                        total_earnings += earnings
                    
                    horse['races'] += 1
                    horse['racing_experience'] = horse.get('racing_experience', 0) + 1
                    
                    # Add to detailed racing history
                    if 'racing_history' not in horse:
                        horse['racing_history'] = []
                    horse['racing_history'].append({
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'race_type': 'offline_simulation',
                        'result': 'won' if won_race else 'lost',
                        'earnings': earnings if won_race else 0,
                        'experience_gained': 1
                    })
                    
                    # Tamagotchi care effects from racing
                    horse['energy'] = max(20, horse.get('energy', 100) - random.randint(15, 25))
                    horse['hunger'] = max(30, horse.get('hunger', 100) - random.randint(10, 20))
                    horse['cleanliness'] = max(40, horse.get('cleanliness', 100) - random.randint(15, 30))
                    
                    # Health reduction with care level consideration
                    care_score = (horse.get('hunger', 100) + horse.get('happiness', 100) + 
                                horse.get('energy', 100) + horse.get('cleanliness', 100)) / 4
                    health_loss = random.randint(1, 3)
                    if care_score < 50:  # Poor care = more health loss
                        health_loss += 2
                    horse['health'] = max(50, horse['health'] - health_loss)
        
        if total_earnings > 0:
            st.session_state.money += total_earnings
            # Auto-save after earning money
            auto_save_user_data()
            
            # Track business revenue from offline earnings
            if 'business_financials' in st.session_state:
                try:
                    from stable_business import track_revenue
                    track_revenue(total_earnings, 'race')
                    st.session_state.business_metrics["total_race_winnings"] += total_earnings
                except ImportError:
                    pass
            if 'logs' not in st.session_state:
                st.session_state.logs = []
            st.session_state.logs.append(f"🏆 Your racing horses earned ${total_earnings} while you were away!")
    
    st.session_state.last_offline_check = current_time