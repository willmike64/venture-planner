# horse_board_game_multiplayer.py - Multiplayer Horse Race Board Game
import streamlit as st
import random
from collections import defaultdict
import firebase_utils
import time

# Track lengths based on mathematical probability for fair racing
TRACK_LENGTHS = {
    2: 2, 3: 4, 4: 6, 5: 8, 6: 10, 7: 12,
    8: 10, 9: 8, 10: 6, 11: 4, 12: 2
}

def get_player_info():
    """Get the current player's info from their login session."""
    # Get user ID (email-based) and display name
    user_id = st.session_state.get('user_id', f'player_{int(time.time())}')
    
    # Use email as default name if logged in, otherwise allow custom name
    if "logged_in" in st.session_state and st.session_state.get("logged_in"):
        # Convert user_id back to email format for display
        # Handle format like "mwill1003_gmail_com" -> "mwill1003@gmail.com"
        if "_" in user_id and not user_id.startswith("session_") and not user_id.startswith("player_"):
            # Find the last two underscores (for domain)
            parts = user_id.split("_")
            if len(parts) >= 3:
                email_parts = parts[:-2] + [parts[-2] + "." + parts[-1]]
                email = "_".join(email_parts[:-1]) + "@" + email_parts[-1]
                default_name = email
            else:
                default_name = user_id.replace("_", "@", 1)
        else:
            default_name = user_id
    else:
        default_name = "Guest Player"
    
    # Get or set display name
    if 'multiplayer_player_name' not in st.session_state:
        st.session_state.multiplayer_player_name = default_name
    
    return user_id, st.session_state.multiplayer_player_name

def render_game_lobby():
    """Render the game lobby where players can create or join games."""
    st.header("🎲 Multiplayer Horse Race Lobby")
    
    # Get player info
    user_id, current_name = get_player_info()
    
    # Debug info
    with st.expander("🔍 Debug Info", expanded=False):
        st.write(f"User ID: {user_id}")
        st.write(f"Current Name: {current_name}")
        st.write(f"Session State Keys: {list(st.session_state.keys())}")
        st.write(f"Logged In: {st.session_state.get('logged_in', False)}")
    
    # Allow name customization
    player_name = st.text_input(
        "Your display name:", 
        value=current_name,
        key="player_name_input",
        help="This is how other players will see you in the game"
    )
    
    # Update session state when name changes
    if player_name != st.session_state.get('multiplayer_player_name', ''):
        st.session_state.multiplayer_player_name = player_name
    
    # Show current status
    st.info(f"👤 Playing as: **{player_name}** (ID: {user_id})")
    
    if not player_name or player_name.strip() == "":
        st.warning("👤 Please enter your display name to continue")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🆕 Create New Game")
        max_players = st.selectbox("Max Players:", [2, 3, 4, 5, 6, 7, 8], index=2)
        starting_chips = st.selectbox("Starting Chips:", [25, 50, 100, 200], index=1)
        
        if st.button("🎮 Create Game", type="primary", key="create_game_btn"):
            game_id = firebase_utils.create_board_game(
                user_id, player_name, max_players, starting_chips
            )
            if game_id:
                st.session_state.current_game_id = game_id
                st.success(f"✅ Created game: {game_id}")
                st.rerun()
    
    with col2:
        st.markdown("### 🔍 Join Existing Game")
        
        # Manual game ID input
        manual_game_id = st.text_input("Game ID:", placeholder="Enter 8-character game ID")
        
        col_join, col_rejoin = st.columns(2)
        
        with col_join:
            if st.button("🚪 Join by ID", key="join_by_id_btn") and manual_game_id:
                result = firebase_utils.join_board_game(manual_game_id, user_id, player_name)
                if result is not None:
                    success, message = result
                    if success:
                        st.session_state.current_game_id = manual_game_id
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Failed to join game - connection error")
        
        with col_rejoin:
            if st.button("🔄 Rejoin Game", key="rejoin_game_btn") and manual_game_id:
                result = firebase_utils.join_board_game(manual_game_id, user_id, player_name)
                if result is not None:
                    success, message = result
                    if success:
                        st.session_state.current_game_id = manual_game_id
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Failed to rejoin game - connection error")
        
        # List active games
        st.markdown("**Available Games:**")
        active_games = []  # Function not available - would need to be implemented
        
        if active_games:
            for game in active_games[:5]:  # Show max 5 games
                with st.container():
                    game_info = f"**{game['creator_name']}'s Game** ({game['players']}/{game['max_players']})"
                    st.markdown(game_info)
                    if st.button("Join", key=f"join_{game['game_id']}"):
                        result = firebase_utils.join_board_game(
                            game['game_id'], user_id, player_name
                        )
                        if result is not None:
                            success, message = result
                            if success:
                                st.session_state.current_game_id = game['game_id']
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.error("Failed to join game - connection error")
        else:
            st.info("No active games available. Create a new one!")

def create_deck():
    """Create a deck of 44 cards (remove Aces, Kings, Jokers)."""
    deck = []
    for suit in range(4):
        for number in range(2, 11):
            deck.append(number)
        deck.append(11)  # Jack = 11
        deck.append(12)  # Queen = 12
    return deck

def deal_cards_to_players(game_data):
    """Deal cards to all players in the game."""
    deck = create_deck()
    random.shuffle(deck)
    
    players = list(game_data['players'].keys())
    cards_per_player = len(deck) // len(players)
    extra_cards = len(deck) % len(players)
    
    # Initialize chips with starting amount
    starting_chips = game_data.get('starting_chips', 50)
    
    card_index = 0
    for i, player_id in enumerate(players):
        num_cards = cards_per_player + (1 if i < extra_cards else 0)
        game_data['players'][player_id]['cards'] = deck[card_index:card_index + num_cards]
        # Initialize chips if not already set
        if 'chips' not in game_data['players'][player_id]:
            game_data['players'][player_id]['chips'] = starting_chips
        card_index += num_cards

def render_game_board(game_data):
    """Display the current game board"""
    # Validate that game_data is a dictionary
    if not isinstance(game_data, dict):
        st.error(f"Invalid game data type: {type(game_data)}")
        st.write("Game data:", game_data)
        return
        
    # Ensure all required fields exist
    required_fields = ['scratched_horses', 'horses', 'status', 'pot']
    for field in required_fields:
        if field not in game_data:
            st.warning(f"Missing field '{field}' in game data - initializing...")
            if field == 'scratched_horses':
                game_data[field] = []
            elif field == 'horses':
                # Initialize horses with just positions (Firebase format)
                game_data[field] = {i: 0 for i in range(2, 13)}
            elif field == 'status':
                game_data[field] = 'scratch_phase'
            elif field == 'pot':
                game_data[field] = 0
    
    # Display scratched horses
    scratched_horses = game_data.get('scratched_horses', [])
    if scratched_horses:
        st.markdown("#### 🚫 Scratched Horses:")
        scratch_cols = st.columns(4)
        for i, (horse, slot) in enumerate(scratched_horses):
            with scratch_cols[i]:
                st.markdown(f"**Slot {slot}:** Horse #{horse}")
    
    # Main racing track
    st.markdown("#### 🏇 Racing Track:")
    
    if not isinstance(scratched_horses, list):
        scratched_horses = []
    scratched_numbers = [h[0] for h in scratched_horses if isinstance(h, (list, tuple)) and len(h) > 0]
    
    for horse_num in sorted(range(2, 13)):
        if horse_num in scratched_numbers:
            continue
            
        # Try both string and integer keys for backwards compatibility
        if str(horse_num) in game_data['horses']:
            position = game_data['horses'][str(horse_num)]
        elif horse_num in game_data['horses']:
            position = game_data['horses'][horse_num]
        else:
            position = 0
        
        track_length = TRACK_LENGTHS[horse_num]
        
        # Create track visualization
        track = ["🏁"] + ["▫️"] * track_length + ["🏆"]
        
        # Place horse on track
        if position > 0:
            if position >= track_length:
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
        st.progress(min(1.0, position / track_length))

def render_players_panel(game_data, current_user_id):
    """Display all players and their status."""
    st.markdown("### 👥 Players")
    
    for player_id, player_info in game_data['players'].items():
        is_current_user = (player_id == current_user_id)
        
        with st.expander(f"{'🫵 ' if is_current_user else ''}{'👑 ' if player_id == game_data['creator_id'] else ''}{player_info['name']}", expanded=is_current_user):
            
            # Show cards (only for current user or if game finished)
            if is_current_user or game_data['status'] == 'finished':
                cards = player_info.get('cards', [])
                if cards:
                    card_counts = defaultdict(int)
                    for card in cards:
                        card_counts[card] += 1
                    
                    st.markdown("**Cards:**")
                    card_display = []
                    for number in sorted(card_counts.keys()):
                        count = card_counts[number]
                        card_display.append(f"#{number} x{count}")
                    st.markdown(" | ".join(card_display))
            else:
                st.markdown(f"**Cards:** {len(player_info.get('cards', []))} cards")
            
            # Show chips
            chips = player_info.get('chips', 0)
            st.markdown(f"**Chips:** {chips}")
            
            # Show ready status during waiting
            if game_data['status'] == 'waiting':
                ready = player_info.get('is_ready', False)
                st.markdown(f"**Ready:** {'✅' if ready else '⏳'}")

def roll_dice():
    """Roll two dice and return the sum."""
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    return die1, die2, die1 + die2

def handle_game_action(game_id, action, current_user_id):
    """Handle various game actions for scratch-and-race game."""

    game_data = firebase_utils.get_board_game(game_id)
    if game_data is None:
        st.error("Game not found!")
        return

    # Convert to dict if it's not already
    if not isinstance(game_data, dict):
        st.error("Invalid game data format!")
        return

    # Ensure required keys exist
    game_data.setdefault("players", {})
    game_data.setdefault("status", "waiting")
    game_data.setdefault("current_player_index", 0)
    game_data.setdefault("scratch_phase", 0)
    game_data.setdefault("pot", 0)
    game_data.setdefault("horses", {i: 0 for i in range(2, 13)})

    if action == "ready":
        # Additional validation for players data
        players_data = game_data.get("players")
        if not isinstance(players_data, dict):
            st.error("Invalid players data structure!")
            return
            
        if current_user_id not in players_data:
            st.error("You are not in this game!")
            return

        # Ensure the player data is a dictionary before setting is_ready
        player_data = players_data.get(current_user_id)
        if not isinstance(player_data, dict):
            st.error("Invalid player data structure!")
            return

        player_data["is_ready"] = True

        # Start the game if all players are ready and at least 2 joined
        players_dict = game_data["players"]
        # Ensure players_dict is a proper dictionary
        if not isinstance(players_dict, dict):
            st.error("Invalid players data structure!")
            return
        all_ready = all(p.get("is_ready", False) for p in players_dict.values())
        if all_ready and len(players_dict) >= 2:
            game_data["status"] = "scratching"
            deal_cards_to_players(game_data)

        firebase_utils.update_board_game(game_id, game_data)
        st.rerun()

    elif action == "roll_scratch":
        players_data = game_data.get("players")
        if not isinstance(players_data, dict):
            st.error("Invalid players data structure!")
            return
        player_ids = list(players_data.keys())
        if not player_ids:
            st.error("No players found.")
            return

        current_player_index = game_data.get("current_player_index", 0)
        if not isinstance(current_player_index, int):
            current_player_index = 0
        current_player_id = player_ids[current_player_index]
        if current_user_id != current_player_id:
            st.error("Not your turn!")
            return

        die1, die2, dice_sum = roll_dice()
        game_data["last_roll"] = {"die1": die1, "die2": die2, "sum": dice_sum}

        scratched_horses = game_data.setdefault("scratched_horses", [])
        # Ensure scratched_horses is a list and contains valid tuples
        if not isinstance(scratched_horses, list):
            scratched_horses = []
            game_data["scratched_horses"] = scratched_horses
        
        scratched_numbers = []
        for h in scratched_horses:
            if isinstance(h, (list, tuple)) and len(h) >= 2:
                scratched_numbers.append(h[0])

        if dice_sum in scratched_numbers:
            st.warning(f"Horse #{dice_sum} already scratched! Roll again.")
        else:
            scratch_phase = game_data.get("scratch_phase", 0)
            if not isinstance(scratch_phase, int):
                scratch_phase = 0
            slot = scratch_phase + 1
            if not isinstance(slot, int):
                slot = 0
            if not isinstance(game_data["scratched_horses"], list):
                if isinstance(game_data["scratched_horses"], list):
                    pass  # Already a list, do nothing
                elif isinstance(game_data["scratched_horses"], (tuple, set)):
                    game_data["scratched_horses"] = list(game_data["scratched_horses"])
                else:
                    game_data["scratched_horses"] = []
            game_data["scratched_horses"].append((dice_sum, slot))

            # Deduct chips for matching cards
            players_dict = game_data.get("players")
            if not isinstance(players_dict, dict):
                st.error("Invalid players data structure!")
                return
            for player_id, player_data in players_dict.items():
                player_data.setdefault("cards", [])
                # Don't reset chips to 0 - keep their starting amount
                if "chips" not in player_data:
                    player_data["chips"] = game_data.get("starting_chips", 50)

                matches = [card for card in player_data["cards"] if card == dice_sum]
                player_data["cards"] = [card for card in player_data["cards"] if card != dice_sum]
                chips_owed = len(matches) * slot
                player_data["chips"] -= chips_owed
                if not isinstance(game_data["pot"], int):
                    game_data["pot"] = 0
                game_data["pot"] += chips_owed


            if not isinstance(game_data["scratch_phase"], int):
                game_data["scratch_phase"] = 0
            game_data["scratch_phase"] += 1

            if game_data["scratch_phase"] >= 4:
                game_data["status"] = "racing"
                game_data["current_player_index"] = 0
            else:
                # Ensure current_player_index is an integer before incrementing
                current_index = game_data.get("current_player_index", 0)
                if not isinstance(current_index, int):
                    current_index = 0
                players_obj = game_data.get("players")
                if isinstance(players_obj, (dict, list)):
                    num_players = len(players_obj)
                else:
                    num_players = 0
                game_data["current_player_index"] = (current_index + 1) % num_players if num_players > 0 else 0

        firebase_utils.update_board_game(game_id, game_data)
        st.rerun()

    elif action == "roll_race":
        players_obj = game_data.get("players")
        if not isinstance(players_obj, dict):
            st.error("Invalid players data structure!")
            return
        player_ids = list(players_obj.keys())
        if not isinstance(player_ids, list) or not player_ids:
            st.error("No players found.")
            return

        current_index = game_data.get("current_player_index", 0)
        if not isinstance(current_index, int) or current_index < 0 or current_index >= len(player_ids):
            current_index = 0
        current_player_id = player_ids[current_index]
        if current_user_id != current_player_id:
            st.error("Not your turn!")
            return

        die1, die2, dice_sum = roll_dice()
        game_data["last_roll"] = {"die1": die1, "die2": die2, "sum": dice_sum}

        scratched_horses = game_data.get("scratched_horses", [])
        if not isinstance(scratched_horses, list):
            scratched_horses = []
        scratched_numbers = [h[0] for h in scratched_horses if isinstance(h, (list, tuple)) and len(h) > 0]

        if dice_sum in scratched_numbers:
            # Ensure scratched_horses is a list of tuples before iterating
            if isinstance(scratched_horses, list):
                for item in scratched_horses:
                    if isinstance(item, (list, tuple)) and len(item) == 2:
                        horse, slot = item
                        if horse == dice_sum:
                            isinstance(slot, int)
                            if slot > 0:
                                players_obj = game_data["players"]
                                if isinstance(players_obj, dict):
                                    player_obj = players_obj.get(current_user_id)
                                elif isinstance(players_obj, list):
                                    # If players is a list, try to find the player by id
                                    player_obj = next((p for p in players_obj if isinstance(p, dict) and p.get("id") == current_user_id), None)
                                else:
                                    player_obj = None
                                if isinstance(player_obj, dict) and isinstance(player_obj.get("chips"), int):
                                    player_obj["chips"] -= slot 
                            game_data["pot"] += slot
                            break
        else:
            # Ensure horses is a dict before using setdefault and subscript
            import pandas as pd
            horses_obj = game_data.get("horses")
            if isinstance(horses_obj, pd.DataFrame):
                game_data["horses"] = horses_obj.to_dict()[horses_obj.columns[0]] if horses_obj.columns.size > 0 else {i: 0 for i in range(2, 13)}
            elif isinstance(horses_obj, pd.Series):
                game_data["horses"] = horses_obj.to_dict()
            elif isinstance(horses_obj, dict):
                game_data["horses"] = horses_obj
            else:
                game_data["horses"] = {i: 0 for i in range(2, 13)}
            game_data["horses"].setdefault(dice_sum, 0)
            if not isinstance(game_data["horses"][dice_sum], int):
                game_data["horses"][dice_sum] = 0
            game_data["horses"][dice_sum] += 1

            track_length = TRACK_LENGTHS.get(dice_sum, 6)  # Default length if not defined
            if isinstance(game_data["horses"][dice_sum], int) and game_data["horses"][dice_sum] >= track_length:
                game_data["winner"] = dice_sum
                game_data["status"] = "finished"
                calculate_winnings(game_data)

        status = game_data.get("status")
        if isinstance(status, str) and status != "finished":
            if isinstance(game_data.get("players"), dict):
                players_obj = game_data.get("players")
                if isinstance(players_obj, (dict, list)):
                    num_players = len(players_obj)
                else:
                    num_players = 0
            else:
                num_players = 0
            if num_players > 0:
                current_player_index = game_data.get("current_player_index", 0)
                if not isinstance(current_player_index, int):
                    current_player_index = 0
                game_data["current_player_index"] = (current_player_index + 1) % num_players
            else:
                game_data["current_player_index"] = 0

        firebase_utils.update_board_game(game_id, game_data)
        st.rerun()

def calculate_winnings(game_data):
    """Calculate and distribute winnings."""
    winner = game_data['winner']
    if not winner:
        return
    
    # Count winning cards per player
    winning_cards = {}
    total_winning_cards = 0
    
    for player_id, player_data in game_data['players'].items():
        winner_cards = [card for card in player_data['cards'] if card == winner]
        if winner_cards:
            winning_cards[player_id] = len(winner_cards)
            total_winning_cards += len(winner_cards)
    
    # Collect chips from non-winners
    for player_id, player_data in game_data['players'].items():
        if player_id not in winning_cards:
            remaining_cards = len(player_data['cards'])
            if remaining_cards > 0:
                player_data['chips'] -= remaining_cards
                game_data['pot'] += remaining_cards
    
    # Distribute pot to winners
    if total_winning_cards > 0:
        pot_per_card = game_data['pot'] / total_winning_cards
        
        for player_id, cards in winning_cards.items():
            winnings = int(pot_per_card * cards)
            game_data['players'][player_id]['chips'] += winnings

def render_game_controls(game_data, game_id, current_user_id):
    """Render game control buttons."""
    if game_data['status'] == 'waiting':
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### ⏳ Waiting for Players")
            st.info(f"Players: {len(game_data['players'])}/{game_data['max_players']}")
            
            # Show current players with ready status
            for player_id, player_info in game_data['players'].items():
                is_creator = (player_id == game_data['creator_id'])
                is_ready = player_info.get('is_ready', False)
                ready_icon = "✅" if is_ready else "⏳"
                creator_icon = "👑 " if is_creator else ""
                
                st.markdown(f"{ready_icon} {creator_icon}{player_info['name']}")
            
            current_player = game_data['players'].get(current_user_id, {})
            is_ready = current_player.get('is_ready', False)
            
            if not is_ready:
                if st.button("✅ Ready to Play", type="primary", key="ready_to_play_btn"):
                    handle_game_action(game_id, "ready", current_user_id)
            else:
                st.success("✅ You are ready! Waiting for other players...")
        
        with col2:
            # Player management for game creator
            if current_user_id == game_data['creator_id']:
                st.markdown("### 👥 Player Management")
                
                # Show kicked players who can rejoin
                kicked_players = game_data.get('kicked_players', {})
                if kicked_players:
                    st.markdown("**Kicked Players (can rejoin):**")
                    for kicked_id, kicked_info in kicked_players.items():
                        st.markdown(f"🚫 {kicked_info['name']}")
                
                # Kick player interface
                kickable_players = [(pid, pinfo['name']) for pid, pinfo in game_data['players'].items() 
                                  if pid != current_user_id]
                
                if kickable_players:
                    st.markdown("**Remove Player:**")
                    player_to_kick = st.selectbox(
                        "Select player to remove:",
                        options=[None] + kickable_players,
                        format_func=lambda x: "Choose a player..." if x is None else x[1]
                    )
                    
                    if player_to_kick and st.button("🚫 Remove Player", type="secondary", key="remove_player_btn"):
                        # Remove player from the game
                        player_id_to_kick = player_to_kick[0]
                        player_name_to_kick = player_to_kick[1]
                        
                        # Move player to kicked_players list
                        if 'kicked_players' not in game_data:
                            game_data['kicked_players'] = {}
                        
                        game_data['kicked_players'][player_id_to_kick] = game_data['players'][player_id_to_kick]
                        
                        # Remove from active players
                        del game_data['players'][player_id_to_kick]
                        
                        # Update the game data in Firebase
                        firebase_utils.update_board_game(game_id, game_data)
                        
                        st.success(f"Removed {player_name_to_kick} from the game")
                        st.rerun()
            
            else:
                # Show game info for non-creators
                st.markdown("### 🎮 Game Info")
                st.markdown(f"**Creator:** 👑 {game_data['creator_name']}")
                st.markdown(f"**Game ID:** {game_data['game_id']}")
                
                if st.button("🚪 Leave Game", key="leave_game_waiting"):
                    st.session_state.current_game_id = None
                    st.rerun()
    
    elif game_data['status'] == 'scratching':
        st.markdown("### 🚫 Scratching Phase")
        st.markdown(f"**Round {game_data['scratch_phase'] + 1}/4** - Eliminating horses")
        
        if not isinstance(game_data, dict) or 'players' not in game_data or 'current_player_index' not in game_data:
            st.error("Invalid game data structure")
            return
        
        players_data = game_data['players']
        if not isinstance(players_data, dict):
            st.error("Invalid players data")
            return
            
        current_player_id = list(players_data.keys())[game_data['current_player_index']]
        is_current_turn = (current_player_id == current_user_id)
        current_player_name = game_data['players'][current_player_id]['name']
        
        if is_current_turn:
            st.info("🎯 Your turn to roll!")
            if st.button("🎲 Roll Dice to Scratch Horse", type="primary", key="roll_scratch_btn"):
                handle_game_action(game_id, "roll_scratch", current_user_id)
        else:
            st.info(f"⏳ Waiting for {current_player_name} to roll...")
            if st.button("🔄 Refresh", key="refresh_scratch"):
                st.rerun()
    
    elif game_data['status'] == 'racing':
        st.markdown("### 🏇 Racing Phase")
        
        if not isinstance(game_data, dict) or 'players' not in game_data or 'current_player_index' not in game_data:
            st.error("Invalid game data structure")
            return
        
        players_data = game_data['players']
        if not isinstance(players_data, dict):
            st.error("Invalid players data")
            return
            
        current_player_id = list(players_data.keys())[game_data['current_player_index']]
        is_current_turn = (current_player_id == current_user_id)
        current_player_name = game_data['players'][current_player_id]['name']
        
        if is_current_turn:
            st.info("🎯 Your turn to roll!")
            if st.button("🎲 Roll Dice to Move Horse", type="primary", key="roll_move_btn"):
                handle_game_action(game_id, "roll_race", current_user_id)
        else:
            st.info(f"⏳ Waiting for {current_player_name} to roll...")
            if st.button("🔄 Refresh", key="refresh_race"):
                st.rerun()
    
    elif game_data['status'] == 'finished':
        st.markdown("### 🏆 Game Finished!")
        if game_data['winner']:
            st.success(f"🎉 Horse #{game_data['winner']} wins!")
        
        if st.button("🏠 Back to Lobby", key="back_lobby_finished"):
            st.session_state.current_game_id = None
            st.rerun()
    
    # Show last roll
    if 'last_roll' in game_data and game_data['last_roll']:
        roll_data = game_data['last_roll']
        st.info(f"🎲 Last roll: {roll_data['die1']} + {roll_data['die2']} = {roll_data['sum']}")

def render_multiplayer_board_game():
    """Main function to render the multiplayer board game."""
    st.title("🎲 Multiplayer Horse Race")
    
    # Check if player is in a game
    if 'current_game_id' not in st.session_state:
        render_game_lobby()
        return
    
    game_id = st.session_state.current_game_id
    game_data = firebase_utils.get_board_game(game_id)
    
    if game_data is None:
        st.error("❌ Game not found! This may happen if:")
        st.error("• The game was deleted")  
        st.error("• Your connection was interrupted")
        st.error("• The Game ID is incorrect")
        st.info("💡 Try rejoining with the Game ID or create a new game")
        if st.button("🏠 Back to Lobby", key="back_lobby_error"):
            st.session_state.current_game_id = None
            st.rerun()
        return
    
    # Get current user info
    user_id, player_name = get_player_info()
    
    # Update player activity heartbeat (commented out until function is implemented)
    # firebase_utils.update_player_activity(game_id, user_id)
    
    # Check if user is in this game
    if not isinstance(game_data, dict) or user_id not in game_data.get('players', {}):
        st.error("❌ You are not in this game!")
        st.info("💡 This may happen if:")
        st.info("• You were removed for inactivity")
        st.info("• You were kicked by the game creator") 
        st.info("• There was a connection issue")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try to Rejoin", key="try_rejoin_btn"):
                result = firebase_utils.join_board_game(game_id, user_id, player_name)
                if result and result[0]:
                    st.success("✅ Successfully rejoined!")
                    st.rerun()
                else:
                    st.error(f"❌ {result[1] if result else 'Failed to rejoin'}")
        
        with col2:
            if st.button("🏠 Back to Lobby", key="back_lobby_not_in_game"):
                st.session_state.current_game_id = None
                st.rerun()
        return
    
    # Display game info
    st.markdown(f"**Game ID:** `{game_id}` | **Share this ID with friends!**")
    
    # Auto-refresh for real-time updates
    if game_data['status'] in ['scratching', 'racing'] and st.checkbox("🔄 Auto-refresh", value=True):
        time.sleep(2)
        st.rerun()
    
    # Main game layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_game_board(game_data)
        render_game_controls(game_data, game_id, user_id)
    
    with col2:
        render_players_panel(game_data, user_id)
    
    # Game rules
    with st.expander("📋 How to Play", expanded=False):
        st.markdown("""
        **Multiplayer Horse Racing Game**
        
        1. **Join:** Enter your name and join or create a game
        2. **Ready:** Mark yourself as ready when all players join
        3. **Scratch:** Take turns rolling dice to eliminate 4 horses
        4. **Race:** Roll dice to move horses toward the finish line
        5. **Win:** Horse reaches finish first! Players with matching cards win chips!
        
        **Mathematical Balance:** All horses have equal winning chances due to balanced track lengths!
        """)
    
    # Leave game option
    if st.button("🚪 Leave Game", type="secondary", key="leave_game_main"):
        st.session_state.current_game_id = None
        st.rerun()

if __name__ == "__main__":
    render_multiplayer_board_game()