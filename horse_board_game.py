# horse_board_game.py - Horse Race Board Game
import streamlit as st
import random
from collections import defaultdict
import firebase_utils

# Track lengths based on mathematical probability for fair racing
# Each horse now has equal expected winning chances!
TRACK_LENGTHS = {
    2: 2,    # 1/36 probability (2.78%) - shortest track
    3: 4,    # 2/36 probability (5.56%)
    4: 6,    # 3/36 probability (8.33%)
    5: 8,    # 4/36 probability (11.11%)
    6: 10,   # 5/36 probability (13.89%)
    7: 12,   # 6/36 probability (16.67%) - longest track for most common roll
    8: 10,   # 5/36 probability (13.89%)
    9: 8,    # 4/36 probability (11.11%)
    10: 6,   # 3/36 probability (8.33%)
    11: 4,   # 2/36 probability (5.56%)
    12: 2    # 1/36 probability (2.78%) - shortest track
}

def initialize_board_game():
    """Initialize a new board game session."""
    if "board_game_state" not in st.session_state:
        st.session_state.board_game_state = {
            "horses": {i: 0 for i in range(2, 13)},  # Horse positions (0 = starting line)
            "scratched_horses": [],  # List of tuples (horse_number, scratch_slot)
            "cards": {},  # Player cards {player_id: [card_numbers]}
            "chips": {},  # Player chips {player_id: chip_count}
            "pot": 0,
            "current_player": 0,
            "players": [],
            "game_phase": "setup",  # setup, scratching, racing, finished
            "scratch_phase": 0,  # 0-3 for the 4 scratching rounds
            "winner": None,
            "dice_result": None,
            "last_move": ""
        }

def create_deck():
    """Create a deck of 44 cards (remove Aces, Kings, Jokers)."""
    # Cards 2-10 in 4 suits = 36 cards
    # Jacks (11) and Queens (12) in 4 suits = 8 cards
    # Total: 44 cards
    deck = []
    for suit in range(4):  # 4 suits
        for number in range(2, 11):  # 2-10
            deck.append(number)
        deck.append(11)  # Jack = 11
        deck.append(12)  # Queen = 12
    return deck

def deal_cards(players, deck):
    """Deal all cards to players."""
    random.shuffle(deck)
    cards_per_player = len(deck) // len(players)
    extra_cards = len(deck) % len(players)
    
    player_cards = {}
    card_index = 0
    
    for i, player in enumerate(players):
        num_cards = cards_per_player + (1 if i < extra_cards else 0)
        player_cards[player] = deck[card_index:card_index + num_cards]
        card_index += num_cards
    
    return player_cards

def render_board():
    """Render the visual horse racing board."""
    st.markdown("### 🏁 Horse Race Board")
    
    # Display scratched horses
    if st.session_state.board_game_state["scratched_horses"]:
        st.markdown("#### 🚫 Scratched Horses:")
        scratch_cols = st.columns(4)
        for i, (horse, slot) in enumerate(st.session_state.board_game_state["scratched_horses"]):
            with scratch_cols[i]:
                st.markdown(f"**Slot {slot}:** Horse #{horse}")
    
    # Main racing track
    st.markdown("#### 🏇 Racing Track:")
    
    horses = st.session_state.board_game_state["horses"]
    scratched_numbers = [h[0] for h in st.session_state.board_game_state["scratched_horses"]]
    
    for horse_num in sorted(horses.keys()):
        if horse_num in scratched_numbers:
            continue
            
        position = horses[horse_num]
        track_length = TRACK_LENGTHS[horse_num]
        
        # Create track visualization
        track = ["🏁"] + ["▫️"] * track_length + ["🏆"]
        
        # Place horse on track
        if position > 0:
            if position >= track_length:
                # Horse won!
                track[-1] = f"🏇{horse_num}"
            else:
                track[position] = f"🏇{horse_num}"
        else:
            track[0] = f"🏇{horse_num}"
        
        # Display track with progress
        progress_percentage = min(100, (position / track_length) * 100)
        st.markdown(f"**Horse #{horse_num}** ({progress_percentage:.1f}%)")
        st.markdown("".join(track))
        
        # Show progress bar
        if position > 0:
            st.progress(min(1.0, position / track_length))
        else:
            st.progress(0.0)

def render_player_info():
    """Display player information including cards and chips."""
    st.markdown("### 👥 Player Information")
    
    state = st.session_state.board_game_state
    
    for player in state["players"]:
        with st.expander(f"Player: {player}"):
            # Show cards
            if player in state["cards"]:
                cards = state["cards"][player]
                card_counts = defaultdict(int)
                for card in cards:
                    card_counts[card] += 1
                
                st.markdown("**Cards:**")
                card_display = []
                for number in sorted(card_counts.keys()):
                    count = card_counts[number]
                    card_display.append(f"#{number} x{count}")
                st.markdown(" | ".join(card_display))
            
            # Show chips
            chips = state["chips"].get(player, 0)
            st.markdown(f"**Chips:** {chips}")

def roll_dice():
    """Roll two dice and return the sum."""
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    return die1, die2, die1 + die2

def scratch_horse(horse_number, slot):
    """Scratch a horse and handle chip payments."""
    state = st.session_state.board_game_state
    
    # Add to scratched horses
    state["scratched_horses"].append((horse_number, slot))
    
    # Remove cards and collect chips
    chips_per_card = slot  # Slot 1 = 1 chip, Slot 2 = 2 chips, etc.
    
    for player in state["players"]:
        if player in state["cards"]:
            cards_to_remove = [card for card in state["cards"][player] if card == horse_number]
            # Remove the cards
            state["cards"][player] = [card for card in state["cards"][player] if card != horse_number]
            
            # Charge chips
            chips_owed = len(cards_to_remove) * chips_per_card
            if chips_owed > 0:
                state["chips"][player] -= chips_owed
                state["pot"] += chips_owed
                st.info(f"{player} paid {chips_owed} chips for {len(cards_to_remove)} cards of Horse #{horse_number}")

def handle_race_move(dice_sum):
    """Handle a horse move during the race."""
    state = st.session_state.board_game_state
    scratched_numbers = [h[0] for h in state["scratched_horses"]]
    
    if dice_sum in scratched_numbers:
        # Rolled a scratched horse - pay chips based on scratch slot
        for horse, slot in state["scratched_horses"]:
            if horse == dice_sum:
                current_player = state["players"][state["current_player"]]
                state["chips"][current_player] -= slot
                state["pot"] += slot
                st.warning(f"{current_player} rolled scratched Horse #{dice_sum} and paid {slot} chips!")
                break
    else:
        # Move the horse
        state["horses"][dice_sum] += 1
        track_length = TRACK_LENGTHS[dice_sum]
        
        if state["horses"][dice_sum] >= track_length:
            # Horse won!
            state["winner"] = dice_sum
            state["game_phase"] = "finished"
            st.success(f"🏆 Horse #{dice_sum} WINS! 🏆")
        else:
            st.info(f"Horse #{dice_sum} moves to position {state['horses'][dice_sum]}")

def calculate_winnings():
    """Calculate and distribute winnings."""
    state = st.session_state.board_game_state
    winner = state["winner"]
    
    if not winner:
        return
    
    # Count winning cards per player
    winning_cards = {}
    total_winning_cards = 0
    
    for player in state["players"]:
        if player in state["cards"]:
            winner_cards = [card for card in state["cards"][player] if card == winner]
            if winner_cards:
                winning_cards[player] = len(winner_cards)
                total_winning_cards += len(winner_cards)
    
    # Collect chips from non-winners
    for player in state["players"]:
        if player not in winning_cards:
            remaining_cards = len(state["cards"].get(player, []))
            if remaining_cards > 0:
                state["chips"][player] -= remaining_cards
                state["pot"] += remaining_cards
                st.info(f"{player} paid {remaining_cards} chips for remaining cards")
    
    # Distribute pot to winners
    if total_winning_cards > 0:
        pot_per_card = state["pot"] / total_winning_cards
        
        st.markdown("### 💰 Winnings Distribution:")
        for player, cards in winning_cards.items():
            winnings = int(pot_per_card * cards)
            state["chips"][player] += winnings
            percentage = (cards / total_winning_cards) * 100
            st.success(f"🎉 {player} wins {winnings} chips ({cards} cards = {percentage:.1f}% of pot)")

def render_game_controls():
    """Render game control buttons and dice rolling."""
    state = st.session_state.board_game_state
    
    if state["game_phase"] == "setup":
        st.markdown("### 🎲 Game Setup")
        
        col1, col2 = st.columns(2)
        with col1:
            # Number of players
            num_players = st.number_input("Number of Players", min_value=2, max_value=8, value=4)
            
        with col2:
            starting_chips = st.number_input("Starting Chips per Player", min_value=10, max_value=100, value=50)
        
        if st.button("🎮 Start New Game", type="primary"):
            # Initialize players
            state["players"] = [f"Player {i+1}" for i in range(num_players)]
            
            # Deal cards
            deck = create_deck()
            state["cards"] = deal_cards(state["players"], deck)
            
            # Add bonus cards for owned horses
            add_bonus_cards_for_owned_horses()
            
            # Give starting chips
            for player in state["players"]:
                state["chips"][player] = starting_chips
            
            # Move to scratching phase
            state["game_phase"] = "scratching"
            st.rerun()
    
    elif state["game_phase"] == "scratching":
        st.markdown("### 🚫 Scratching Phase")
        st.markdown(f"**Round {state['scratch_phase'] + 1}/4** - Scratch horses before racing begins")
        
        current_player = state["players"][state["current_player"]]
        st.markdown(f"**{current_player}'s turn to roll**")
        
        if st.button("🎲 Roll Dice to Scratch Horse", type="primary"):
            die1, die2, dice_sum = roll_dice()
            st.markdown(f"🎲 Rolled: {die1} + {die2} = **{dice_sum}**")
            
            # Check if horse already scratched
            scratched_numbers = [h[0] for h in state["scratched_horses"]]
            if dice_sum in scratched_numbers:
                st.warning(f"Horse #{dice_sum} already scratched! Roll again.")
            else:
                slot = state["scratch_phase"] + 1
                scratch_horse(dice_sum, slot)
                
                state["scratch_phase"] += 1
                if state["scratch_phase"] >= 4:
                    state["game_phase"] = "racing"
                    state["current_player"] = 0  # Reset to first player
                    st.success("All horses scratched! Racing begins!")
                else:
                    state["current_player"] = (state["current_player"] + 1) % len(state["players"])
                
                st.rerun()
    
    elif state["game_phase"] == "racing":
        st.markdown("### 🏇 Racing Phase")
        
        current_player = state["players"][state["current_player"]]
        st.markdown(f"**{current_player}'s turn**")
        
        if st.button("🎲 Roll Dice to Move Horse", type="primary"):
            die1, die2, dice_sum = roll_dice()
            st.markdown(f"🎲 Rolled: {die1} + {die2} = **{dice_sum}**")
            
            handle_race_move(dice_sum)
            
            if state["game_phase"] != "finished":
                state["current_player"] = (state["current_player"] + 1) % len(state["players"])
            else:
                calculate_winnings()
            
            st.rerun()
    
    elif state["game_phase"] == "finished":
        st.markdown("### 🏆 Game Finished!")
        st.balloons()
        
        if st.button("🎮 Start New Game"):
            # Reset game state
            st.session_state.board_game_state = None
            initialize_board_game()
            st.rerun()

def render_owned_horse_integration():
    """Allow players to enter their owned horses into the board game."""
    if "stable_horses" not in st.session_state or not st.session_state.stable_horses:
        return
    
    st.markdown("### 🏇 Enter Your Horses")
    
    stable_horses = st.session_state.stable_horses
    state = st.session_state.board_game_state
    
    # Show available horses
    available_horses = [name for name, stats in stable_horses.items() 
                       if stats.get('health', 100) > 50]  # Only healthy horses
    
    if available_horses and state["game_phase"] == "setup":
        st.markdown("**Your Available Horses:**")
        
        selected_horses = st.multiselect(
            "Select horses to enter (you'll get their corresponding number cards)",
            available_horses,
            help="Each horse will be assigned a random number (2-12) and you'll get extra cards for that number!"
        )
        
        if selected_horses and "entered_horses" not in state:
            state["entered_horses"] = {}
            
        if selected_horses:
            # Assign numbers to horses
            for horse_name in selected_horses:
                if horse_name not in state.get("entered_horses", {}):
                    # Assign a random number 2-12
                    assigned_number = random.randint(2, 12)
                    state.setdefault("entered_horses", {})[horse_name] = assigned_number
                    st.success(f"🎯 {horse_name} assigned to Horse #{assigned_number}!")
            
            # Show entered horses
            if "entered_horses" in state:
                st.markdown("**Your Entered Horses:**")
                for horse_name, number in state["entered_horses"].items():
                    horse_stats = stable_horses[horse_name]
                    speed = horse_stats.get('speed', 5)
                    stamina = horse_stats.get('stamina', 5)
                    st.markdown(f"- **{horse_name}** → Horse #{number} (Speed: {speed:.1f}, Stamina: {stamina:.1f})")

def add_bonus_cards_for_owned_horses():
    """Give extra cards to players for their entered horses."""
    state = st.session_state.board_game_state
    
    if "entered_horses" not in state:
        return
        
    # Add bonus cards for entered horses
    for horse_name, number in state["entered_horses"].items():
        # Give the current player 2 extra cards of this number
        if state["players"]:
            current_user = "You"  # Assuming single player mode for now
            if current_user not in state["cards"]:
                state["cards"][current_user] = []
            state["cards"][current_user].extend([number, number])
            st.info(f"Added 2 bonus cards for Horse #{number} ({horse_name})")

def render_betting_system():
    """Add betting capabilities using existing money system."""
    if "money" not in st.session_state:
        return
        
    state = st.session_state.board_game_state
    
    if state["game_phase"] in ["scratching", "racing"]:
        st.markdown("### 💰 Place Bets")
        
        current_money = st.session_state.money
        st.markdown(f"**Your Money:** ${current_money:,.2f}")
        
        # Betting options
        scratched_numbers = [h[0] for h in state["scratched_horses"]]
        available_horses = [i for i in range(2, 13) if i not in scratched_numbers]
        
        if available_horses:
            col1, col2 = st.columns(2)
            
            with col1:
                bet_horse = st.selectbox("Bet on Horse #:", available_horses)
                
            with col2:
                max_bet = float(min(current_money, 1000))  # Max bet of $1000 or current money
                bet_amount = st.number_input("Bet Amount ($):", min_value=1.0, max_value=max_bet, value=10.0, step=5.0)
            
            if st.button(f"💸 Bet ${bet_amount:.2f} on Horse #{bet_horse}"):
                # Place the bet
                if "bets" not in state:
                    state["bets"] = {}
                if "You" not in state["bets"]:
                    state["bets"]["You"] = []
                
                state["bets"]["You"].append({
                    "horse": bet_horse,
                    "amount": bet_amount,
                    "odds": calculate_horse_odds(bet_horse)
                })
                
                st.session_state.money -= bet_amount
                st.success(f"Bet placed! ${bet_amount:.2f} on Horse #{bet_horse}")
                st.rerun()
        
        # Show current bets
        if "bets" in state and "You" in state["bets"] and state["bets"]["You"]:
            st.markdown("**Your Current Bets:**")
            total_bet = 0
            for bet in state["bets"]["You"]:
                total_bet += bet["amount"]
                odds_text = f"{bet['odds']:.1f}:1"
                potential_win = bet["amount"] * bet["odds"]
                st.markdown(f"- Horse #{bet['horse']}: ${bet['amount']:.2f} (Odds: {odds_text}, Potential: ${potential_win:.2f})")
            st.markdown(f"**Total Bet:** ${total_bet:.2f}")

def calculate_horse_odds(horse_number):
    """Calculate betting odds based on balanced track system."""
    # Since all horses now have equal expected winning chances due to balanced tracks,
    # odds are now based on the excitement factor rather than pure probability
    
    # Dice probability for reference
    probability_ways = {
        2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6,
        8: 5, 9: 4, 10: 3, 11: 2, 12: 1
    }
    
    # Track lengths (inversely proportional to probability)
    track_length = TRACK_LENGTHS.get(horse_number, 6)
    ways = probability_ways.get(horse_number, 1)
    
    # Calculate expected moves to win: track_length / (ways/36)
    expected_moves = track_length * 36 / ways
    
    # Since tracks are balanced, base odds around 10:1 with slight variations for excitement
    base_odds = 9.0 + (track_length / 2)  # Longer tracks get slightly better odds
    return max(7.0, min(15.0, base_odds))  # Keep odds reasonable for balanced gameplay

def process_betting_payouts():
    """Process betting payouts when the race finishes."""
    state = st.session_state.board_game_state
    winner = state.get("winner")
    
    if not winner or "bets" not in state:
        return
    
    total_winnings = 0
    
    if "You" in state["bets"]:
        st.markdown("### 💰 Betting Results:")
        
        for bet in state["bets"]["You"]:
            if bet["horse"] == winner:
                # Winning bet
                winnings = bet["amount"] * bet["odds"]
                total_winnings += winnings
                st.success(f"🎉 WIN! Horse #{bet['horse']}: ${bet['amount']:.2f} bet → ${winnings:.2f} payout!")
            else:
                # Losing bet
                st.error(f"❌ Lost: Horse #{bet['horse']}: ${bet['amount']:.2f}")
        
        if total_winnings > 0:
            st.session_state.money += total_winnings
            st.success(f"💰 Total winnings: ${total_winnings:.2f}")
            
            # Save money to Firebase
            user_id = st.session_state.get('user_id', 'default_user')
            firebase_utils.save_user_money(user_id, st.session_state.money)

def render_horse_board_game():
    """Main function to render the horse board game."""
    st.header("🎲 Horse Race Board Game")
    st.markdown("*A classic probability-based horse racing game with dice, cards, and chips!*")
    
    initialize_board_game()
    
    # Integration with owned horses
    render_owned_horse_integration()
    
    # Game info
    with st.expander("📋 How to Play", expanded=False):
        st.markdown("""
        **Objective:** Win chips by holding cards of the winning horse!
        
        **Setup:**
        1. Each player gets cards (2-12) representing horses
        2. Players start with chips for betting
        
        **Scratching Phase (4 rounds):**
        1. Roll dice to eliminate 4 horses before racing
        2. Pay chips for each card of scratched horses:
           - Round 1: 1 chip per card
           - Round 2: 2 chips per card  
           - Round 3: 3 chips per card
           - Round 4: 4 chips per card
        
        **Racing Phase:**
        1. Roll dice to move horses 
        2. If you roll a scratched horse number, pay chips equal to its scratch slot
        3. First horse to finish wins!
        
        **Mathematical Balance:**
        - Track lengths are proportional to dice probability for fair racing
        - Horse #2,12: 2 spaces (2.78% chance to roll)
        - Horse #3,11: 4 spaces (5.56% chance to roll)  
        - Horse #4,10: 6 spaces (8.33% chance to roll)
        - Horse #5,9: 8 spaces (11.11% chance to roll)
        - Horse #6,8: 10 spaces (13.89% chance to roll)
        - Horse #7: 12 spaces (16.67% chance to roll)
        - **All horses have equal expected winning chances!**
        
        **Winning:**
        - Players with cards matching the winning horse split the pot
        - Players without winning cards pay 1 chip per remaining card
        """)
    
    # Current pot display
    state = st.session_state.board_game_state
    if state["pot"] > 0:
        st.metric("💰 Current Pot", f"{state['pot']} chips")
    
    # Betting system
    render_betting_system()
    
    # Main game display
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_board()
    
    with col2:
        render_game_controls()
        st.markdown("---")
        render_player_info()
    
    # Process betting payouts if game finished
    state = st.session_state.board_game_state
    if state["game_phase"] == "finished" and state.get("winner"):
        process_betting_payouts()

if __name__ == "__main__":
    render_horse_board_game()