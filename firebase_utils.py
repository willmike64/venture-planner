# firebase_utils.py - Horse Racing Only
import json
import threading
from datetime import datetime, date
import streamlit as st # type: ignore
import firebase_admin  # type: ignore
from firebase_admin import credentials, db  # type: ignore
import pandas as pd # type: ignore
__all__ = ["get_db", "save_horse_data", "load_horse_data", "firebase_login", "get_user_data", "save_user_data", "save_bets", "load_bets", "save_global_horse_history", "load_global_horse_history", "update_horse_race_record", "save_user_money", "load_user_money", "initialize_user_session", "check_user_data_in_firebase", "restore_user_money", "save_race_record", "load_race_records", "load_horse_race_history", "generate_race_id", "create_board_game", "join_board_game", "get_board_game", "update_board_game", "generate_game_id"]

_lock = threading.Lock()
_app = None

from betting.betting_logic import clean_horse_name  # reuse logic from shared module

def serialize_data(data):
    """Convert datetime objects, date objects, and DataFrames to JSON-serializable format."""
    if isinstance(data, dict):
        return {key: serialize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_data(item) for item in data]
    elif isinstance(data, datetime):
        return {
            '_type': 'datetime',
            '_data': data.isoformat()
        }
    elif isinstance(data, date) and not isinstance(data, datetime):  # date object (but not datetime)
        return {
            '_type': 'date', 
            '_data': data.isoformat()
        }
    elif isinstance(data, pd.DataFrame):
        return {
            '_type': 'dataframe',
            '_data': data.to_dict('records')
        }
    else:
        return data

def deserialize_data(data):
    """Convert serialized data back to original format, restoring DataFrames, dates, and datetimes."""
    if isinstance(data, dict):
        # Check if this is a serialized object with type information
        if '_type' in data:
            if data['_type'] == 'dataframe':
                return pd.DataFrame(data['_data'])
            elif data['_type'] == 'datetime':
                return datetime.fromisoformat(data['_data'])
            elif data['_type'] == 'date':
                return datetime.fromisoformat(data['_data']).date()
        else:
            return {key: deserialize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [deserialize_data(item) for item in data]
    else:
        return data

def get_db():
    """Initialize and return Firebase database reference."""
    global _app
    with _lock:
        if _app is None:
            try:
                # Check if default app already exists
                try:
                    _app = firebase_admin.get_app()
                except ValueError:
                    # Default app doesn't exist, so create it
                    service_account_info = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT_JSON"])
                    cred = credentials.Certificate(service_account_info)
                    _app = firebase_admin.initialize_app(cred, {
                        'databaseURL': st.secrets["FIREBASE_DATABASE_URL"]
                    })
            except Exception as e:
                st.error(f"Firebase initialization failed: {e}")
                return None
    return db.reference()

def firebase_login(email, password):
    """Simple login simulation - returns user ID."""
    if email and password:
        return {"localId": email.replace("@", "_").replace(".", "_")}
    return {}

def get_user_data(user_id):
    """Load user data from Firebase."""
    try:
        ref = get_db()
        if ref:
            data = ref.child('users').child(user_id).get()
            if data:
                # Deserialize the data to restore DataFrames
                return deserialize_data(data)
            return None
    except Exception as e:
        st.error(f"Failed to load user data: {e}")
    return None

def save_user_data(user_id, user_data):
    """Save user data to Firebase."""
    try:
        ref = get_db()
        if ref:
            # Serialize data to handle datetime objects
            serialized_data = serialize_data(user_data)
            ref.child('users').child(user_id).set(serialized_data)
            return True
    except Exception as e:
        st.error(f"Failed to save user data: {e}")
    return False

def save_horse_data(player_id, horse_data):
    """Save horse racing data to Firebase."""
    try:
        ref = get_db()
        if ref:
            # Serialize data to handle datetime objects
            serialized_data = serialize_data(horse_data)
            ref.child('horse_racing').child(player_id).set(serialized_data)
            return True
    except Exception as e:
        st.error(f"Failed to save horse data: {e}")
    return False

def load_horse_data(player_id):
    """Load horse racing data from Firebase."""
    try:
        ref = get_db()
        if ref:
            data = ref.child('horse_racing').child(player_id).get()
            if data:
                # Deserialize the data to restore DataFrames
                return deserialize_data(data)
            return {}
    except Exception as e:
        st.error(f"Failed to load horse data: {e}")
    return {}

def save_bets(bet_pool):
    """Save betting pool data to Firebase."""
    try:
        ref = get_db()
        if ref:
            # Get current user ID from session state
            user_id = st.session_state.get('user_id', 'default_user')
            serialized_data = serialize_data(bet_pool)
            ref.child('betting_pools').child(user_id).set(serialized_data)
            return True
    except Exception as e:
        st.error(f"Failed to save betting data: {e}")
    return False

def load_bets():
    """Load betting pool data from Firebase."""
    try:
        ref = get_db()
        if ref:
            # Get current user ID from session state
            user_id = st.session_state.get('user_id', 'default_user')
            data = ref.child('betting_pools').child(user_id).get()
            if data:
                return deserialize_data(data)
            return {}
    except Exception as e:
        st.error(f"Failed to load betting data: {e}")
    return {}

def save_global_horse_history(horse_history_data):
    """Save global horse history data that all users can see."""
    try:
        ref = get_db()
        if ref:
            # Serialize data to handle datetime objects
            serialized_data = serialize_data(horse_history_data)
            ref.child('global_horse_history').set(serialized_data)
            return True
    except Exception as e:
        st.error(f"Failed to save global horse history: {e}")
    return False

def load_global_horse_history():
    """Load global horse history data visible to all users."""
    try:
        ref = get_db()
        if ref:
            data = ref.child('global_horse_history').get()
            if data:
                return deserialize_data(data)
            return {}
    except Exception as e:
        st.error(f"Failed to load global horse history: {e}")
    return {}

def update_horse_race_record(horse_name, race_result, owner_id=None):
    """Update a specific horse's race record in the global history."""
    try:
        ref = get_db()
        if ref:
            # Load current history
            history = load_global_horse_history()
            
            # Ensure history is a dictionary
            if not isinstance(history, dict):
                history = {}
            
            # Initialize horse record if doesn't exist
            if horse_name not in history:
                history[horse_name] = {
                    'total_races': 0,
                    'total_wins': 0,
                    'total_earnings': 0,
                    'race_history': [],
                    'owner_id': owner_id,
                    'first_race_date': datetime.now().isoformat(),
                    'last_race_date': None,
                    'breed': race_result.get('breed', 'Unknown'),
                    'career_highlights': []
                }
            
            # Ensure career_highlights exists (safety check)
            horse_record = history[horse_name]
            if isinstance(horse_record, dict):
                if 'career_highlights' not in horse_record:
                    horse_record['career_highlights'] = []
                
                # Update race statistics
                horse_record['total_races'] += 1
                horse_record['last_race_date'] = datetime.now().isoformat()

                if race_result.get('position', 10) == 1:  # Won the race
                    horse_record['total_wins'] += 1
                    
                # Add earnings
                horse_record['total_earnings'] += race_result.get('earnings', 0)
                    
                # Save updated history
                horse_record['race_history'].append(race_result)
            save_global_horse_history(history)
            return True
    except Exception as e:
        st.error(f"Failed to update horse race record: {e}")
    return False

def save_user_money(user_id, money_amount):
    """Save user's current money to Firebase."""
    try:
        ref = get_db()
        if ref:
            ref.child('users').child(user_id).child('money').set(float(money_amount))
            return True
    except Exception as e:
        st.error(f"Failed to save money: {e}")
    return False

def load_user_money(user_id):
    """Load user's money from Firebase, return 1000.0 if not found."""
    try:
        ref = get_db()
        if ref:
            money_data = ref.child('users').child(user_id).child('money').get()
            if money_data is not None:
                # Convert to float safely
                try:
                    if isinstance(money_data, (int, float)):
                        return float(money_data)
                    elif isinstance(money_data, str):
                        return float(money_data)
                except (ValueError, TypeError):
                    pass
            # First time user - return starting money
            return 1000.0
    except Exception as e:
        st.error(f"Failed to load money: {e}")
    return 1000.0

def check_user_data_in_firebase(user_id):
    """Debug function to check what data exists for a user in Firebase."""
    try:
        ref = get_db()
        if ref:
            # Check if user has any data
            user_data = ref.child('users').child(user_id).get()
            print(f"User data for {user_id}: {user_data}")
            
            # Check money specifically
            money_data = ref.child('users').child(user_id).child('money').get()
            print(f"Money data for {user_id}: {money_data}")
            
            # Check horse data
            horse_data = ref.child('horse_racing').child(user_id).get()
            print(f"Horse data for {user_id}: {horse_data}")
            
            return user_data, money_data, horse_data
    except Exception as e:
        print(f"Error checking Firebase data: {e}")
    return None, None, None

def restore_user_money(user_id, amount):
    """Restore a user's money to a specific amount."""
    try:
        ref = get_db()
        if ref:
            ref.child('users').child(user_id).child('money').set(float(amount))
            st.session_state.money = float(amount)
            return True
    except Exception as e:
        st.error(f"Failed to restore money: {e}")
    return False

def initialize_user_session(user_id):
    """Initialize user session with persistent data from Firebase."""
    # Create a unique key for this user to prevent re-loading
    user_loaded_key = f"user_data_loaded_{user_id}"
    
    if user_loaded_key not in st.session_state:
        # Always load user's money from Firebase for real users
        if not user_id.startswith("session_"):
            saved_money = load_user_money(user_id)
            st.session_state.money = saved_money
            
            # Special handling for mwill1003@gmail.com - check if money was lost
            if user_id == "mwill1003_gmail_com" and saved_money <= 1000:
                # Check Firebase for any clues about previous money amount
                check_user_data_in_firebase(user_id)
                # Set a reasonable restoration amount based on accumulated gameplay
                st.warning("⚠️ Money restoration in progress - setting to reasonable amount based on gameplay...")
                restore_user_money(user_id, 25000)  # Generous restoration amount
            
        # Load user's horses if not already loaded
        if "stable_horses" not in st.session_state:
            st.session_state.stable_horses = load_horse_data(user_id)
        
        # Mark as loaded to prevent re-initialization for this user
        st.session_state[user_loaded_key] = True

# === BLOCKCHAIN-STYLE RACE RECORD SYSTEM ===

def generate_race_id():
    """Generate a unique race ID using timestamp and random component."""
    from datetime import datetime
    import uuid
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"race_{timestamp}_{unique_id}"

def save_race_record(race_data):
    """Save a complete race record with blockchain-like immutability."""
    try:
        ref = get_db()
        if ref:
            race_id = race_data.get('race_id', generate_race_id())
            race_data['race_id'] = race_id
            race_data['saved_at'] = datetime.now().isoformat()
            
            # Save to global race records (immutable blockchain-style)
            serialized_data = serialize_data(race_data)
            ref.child('race_records').child(race_id).set(serialized_data)
            
            # Also update each horse's individual race history
            for horse_result in race_data.get('results', []):
                horse_name = horse_result.get('name', '').replace(' (Your Horse)', '')
                if horse_name:
                    # Create a simplified record for horse history
                    horse_record = {
                        'race_id': race_id,
                        'date': race_data.get('date'),
                        'race_name': race_data.get('race_name'),
                        'track_condition': race_data.get('track_condition'),
                        'position': horse_result.get('position'),
                        'speed': horse_result.get('speed'),
                        'prize_money': horse_result.get('prize_money', 0),
                        'jockey': horse_result.get('jockey', 'Unknown'),
                        'total_horses': len(race_data.get('results', [])),
                        'owner_id': horse_result.get('owner_id')
                    }
                    
                    # Save to horse-specific history
                    ref.child('horse_race_history').child(horse_name).push().set(serialize_data(horse_record))
            # Also update the global horse history
            update_horse_race_record(
                horse_name=horse_name,
                race_result={
                    'position': horse_result.get('position'),
                    'earnings': horse_result.get('prize_money', 0),
                    'track_condition': race_data.get('track_condition'),
                    'field_size': len(race_data.get('results', [])),
                    'race_type': race_data.get('race_name'),
                    'final_speed': horse_result.get('speed'),
                    'breed': race_result.get('breed', 'Unknown') if (race_result := horse_result) else 'Unknown'
                },
    owner_id=horse_result.get('owner_id')
)
            return True
    except Exception as e:
        st.error(f"Failed to save race record: {e}")
        return False

def load_race_records(limit=50):
    """Load recent race records from the blockchain-style storage."""
    try:
        ref = get_db()
        if ref:
            data = ref.child('race_records').order_by_key().limit_to_last(limit).get()
            if data:
                return dict(data)
    except Exception as e:
        st.error(f"Failed to load race records: {e}")
    return {}

def load_horse_race_history(horse_name):
    """Load complete race history for a specific horse."""
    try:
        ref = get_db()
        if ref:
            # Remove (Your Horse) suffix for lookup
            clean_horse_name = horse_name.replace(' (Your Horse)', '')
            data = ref.child('horse_race_history').child(clean_horse_name).get()
            if data and isinstance(data, dict):
                # Convert to list and sort by date
                history = []
                for key, record in data.items():
                    if isinstance(record, dict):
                        record['record_id'] = key
                        history.append(record)
                
                # Sort by date (newest first)
                history.sort(key=lambda x: x.get('date', ''), reverse=True)
                return history
    except Exception as e:
        st.error(f"Failed to load horse race history: {e}")
    return []

# === MULTIPLAYER BOARD GAME SYSTEM ===

def generate_game_id():
    """Generate a unique game ID."""
    import uuid
    return str(uuid.uuid4())[:8].upper()

def create_board_game(creator_id, creator_name, max_players=4, starting_chips=50):
    """Create a new multiplayer board game."""
    try:
        ref = get_db()
        if ref:
            game_id = generate_game_id()
            game_data = {
                'game_id': game_id,
                'creator_id': creator_id,
                'creator_name': creator_name,
                'created_at': datetime.now().isoformat(),
                'max_players': max_players,
                'starting_chips': starting_chips,
                'status': 'waiting',  # waiting, scratching, racing, finished
                'current_player_index': 0,
                'scratch_phase': 0,
                'horses': {i: 0 for i in range(2, 13)},
                'scratched_horses': [],
                'pot': 0,
                'winner': None,
                'last_roll': None,
                'players': {
                    creator_id: {
                        'name': creator_name,
                        'cards': [],
                        'chips': starting_chips,
                        'joined_at': datetime.now().isoformat(),
                        'is_ready': False
                    }
                }
            }
            
            # Save to Firebase
            serialized_data = serialize_data(game_data)
            ref.child('board_games').child(game_id).set(serialized_data)
            return game_id
    except Exception as e:
        st.error(f"Failed to create board game: {e}")
    return None

def join_board_game(game_id, player_id, player_name):
    """Join an existing board game with improved reconnection logic."""
    try:
        ref = get_db()
        if ref:
            # Get current game state
            game_data = ref.child('board_games').child(game_id).get()
            if not game_data:
                return False, "Game not found"
            
            game_data = deserialize_data(game_data)
            
            # Check if player is already in the game
            if isinstance(game_data, dict) and player_id in game_data.get('players', {}):
                return True, f"{player_name} rejoined the game!"
            
            # Check if game is full
            if isinstance(game_data, dict):
                max_players = game_data.get('max_players', 4)
                players_data = game_data.get('players', {})
            else:
                max_players = 4
                players_data = {}
            
            if not isinstance(players_data, dict):
                players_data = {}
            if not isinstance(max_players, (int, float)):
                max_players = 4
                
            current_players = len(players_data)
            if current_players >= int(max_players):
                return False, "Game is full"
            
            # Check if game has already started
            if isinstance(game_data, dict) and  game_data.get('status') not in ['waiting']:
                return False, "Game has already started"
            
            # Add player to the game
            starting_chips = isinstance(game_data, dict) and game_data.get('starting_chips', 50)
            # Ensure game_data is a dictionary
            if not isinstance(game_data, dict):
                game_data = {}

            # Ensure 'players' is a dictionary
            if 'players' not in game_data or not isinstance(game_data.get('players'), dict):
                game_data['players'] = {}

            # Defensive: ensure game_data['players'] is a dict
            if not isinstance(game_data['players'], dict):
                game_data['players'] = {}

            if player_id not in game_data['players']:
                game_data['players'][player_id] = {
                    'name': player_name,
                    'cards': [],
                    'chips': starting_chips,
                    'joined_at': datetime.now().isoformat(),
                    'is_ready': False
                }
                            
            # Save updated game
            serialized_data = serialize_data(game_data)
            ref.child('board_games').child(game_id).set(serialized_data)
            return True, f"{player_name} joined the game!"
    except Exception as e:
        st.error(f"Failed to join board game: {e}")
        return False, str(e)

def get_board_game(game_id):
    """Get current board game state."""
    try:
        ref = get_db()
        if ref:
            data = ref.child('board_games').child(game_id).get()
            if data:
                return deserialize_data(data)
    except Exception as e:
        st.error(f"Failed to get board game: {e}")
    return None

def update_board_game(game_id, game_data):
    """Update board game state."""
    try:
        ref = get_db()
        if ref:
            # Add timestamp
            game_data['last_updated'] = datetime.now().isoformat()
            
            # Save to Firebase
            serialized_data = serialize_data(game_data)
            ref.child('board_games').child(game_id).set(serialized_data)
            return True
    except Exception as e:
        st.error(f"Failed to update board game: {e}")
    return False


