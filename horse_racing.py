# horse_racing.py - Enhanced animated horse racing with 15-week season system
import streamlit as st # type: ignore
import random
import time
import copy
from datetime import datetime, timedelta
from firebase_utils import save_user_data, get_user_data, initialize_user_session, save_user_money
from jockeys import get_available_jockey
from racing_season import (
    get_current_race, calculate_derby_points, check_racing_achievements,
    render_derby_qualification_status, render_racing_achievements,
    get_current_race_week, is_derby_week, is_triple_crown_race,
    RACING_ACHIEVEMENTS
)
from betting_system import process_race_payouts

def initialize_derby_points_from_firebase():
    """Load Derby points from Firebase into session state"""
    user_id = st.session_state.get('user_id', 'default_user')
    user_data = get_user_data(user_id) or {}
    # Ensure user_data is a dictionary before calling .get()
    if isinstance(user_data, dict):
        derby_points = user_data.get('derby_points', {})
    else:
        derby_points = {}
    st.session_state.derby_points = derby_points



# AI Jockey banter - optional OpenAI integration
try:
    import openai # type: ignore
    client = openai.OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
    OPENAI_AVAILABLE = True
except (ImportError, KeyError):
    OPENAI_AVAILABLE = False

TRIPLE_CROWN = ["Kentucky Derby", "Preakness Stakes", "Belmont Stakes"]

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

def get_global_racing_pool(owned_horses):
    """Get the global racing pool with student horses replacing default horses."""
    # Collect all student horses in racing stables
    student_horses = []
    if owned_horses:  # Use the converted owned_horses list
        for horse in owned_horses:
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

# --- STREAMLIT APP ---
def render_horse_racing():
    # Initialize Derby points from Firebase
    initialize_derby_points_from_firebase()
    
    # Get current race information
    current_race = get_current_race()
    current_week = get_current_race_week()
    
    # Enhanced title with season information
    st.title(f"🏁 Gold Creek Racing - Week {current_week}")
    st.subheader(f"🏆 {current_race['name']} | ${current_race['purse']:,} Purse")
    
    # Race type and significance
    race_types = {
        "maiden": "🔰 Maiden Race - For first-time winners",
        "allowance": "📈 Allowance Race - Stepping stone to stakes",
        "stakes": "⭐ Stakes Race - High-class competition", 
        "prep": "🎯 Prep Race - Building toward bigger goals",
        "derby_prep": "🏇 Derby Prep - Road to Kentucky Derby",
        "graded_stakes": "🌟 Graded Stakes - Elite competition",
        "triple_crown": "👑 Triple Crown Race - Racing immortality"
    }
    
    race_description = race_types.get(current_race['type'], "🏁 Horse Race")
    st.info(f"**{race_description}**")
    
    # Derby points available
    points = current_race.get('points', [0, 0, 0, 0])
    st.write(f"**🎯 Derby Points Available:** 1st: {points[0]} | 2nd: {points[1]} | 3rd: {points[2]} | 4th: {points[3]}")

    # Initialize user session with Firebase data
    if "user_id" in st.session_state:
        initialize_user_session(st.session_state.user_id)
    
    # Initialize gold and casino (only for guests, not logged-in users)
    if 'money' not in st.session_state:
        # Only set default if no user is logged in
        if "user_id" not in st.session_state or st.session_state.user_id.startswith("session_"):
            st.session_state.money = 1000.0

    if 'casino' not in st.session_state:
        st.session_state.casino = {"cash": 0.0, "transactions": []}

    # Convert stable horses to racing format (needed throughout this function)
    stable_horses = st.session_state.get('stable_horses', {})
    owned_horses = []
    
    # Convert stable horses dictionary to list format expected by racing system
    for horse_name, horse_stats in stable_horses.items():
        horse_dict = {
            'name': horse_name,
            'id': horse_name,  # Use name as ID for simplicity
            'breed': horse_stats.get('breed', 'Unknown'),
            'speed': horse_stats.get('speed', 5.0),
            'stamina': horse_stats.get('stamina', 5.0),
            'health': horse_stats.get('health', 100),
            'wins': horse_stats.get('wins', 0),
            'races': horse_stats.get('races', 0),
            'level': horse_stats.get('level', 1),
            'training_count': horse_stats.get('training_count', 0),
            'in_racing_stable': horse_stats.get('in_racing_stable', False),
            'owner_id': horse_stats.get('owner_id', 'player'),
            'certifications': horse_stats.get('certifications', {}),  # Include certifications
            'certification_expiry': horse_stats.get('certification_expiry', {})
        }
        owned_horses.append(horse_dict)

    # Get current racing pool (mix of student and default horses)
    st.session_state.horses = get_global_racing_pool(owned_horses)
    
    # Initialize multiple horse entry system (up to 5 horses)
    if 'horses_entered_in_race' not in st.session_state:
        st.session_state.horses_entered_in_race = []
    
    # Legacy support - convert old single horse entry to new system
    if 'horse_entered_in_race' not in st.session_state:
        st.session_state.horse_entered_in_race = None
    elif st.session_state.horse_entered_in_race and not st.session_state.horses_entered_in_race:
        # Migrate old single entry to new system
        st.session_state.horses_entered_in_race = [st.session_state.horse_entered_in_race]
        st.session_state.horse_entered_in_race = None
    
    if 'player_id' not in st.session_state:
        st.session_state.player_id = f"player_{int(time.time())}_{random.randint(1000, 9999)}"
    
    # Add player's horses if they've entered any
    entered_player_horses = []
    if st.session_state.horses_entered_in_race:
        for entered_horse_id in st.session_state.horses_entered_in_race:
            player_horse = next((h for h in owned_horses if h['id'] == entered_horse_id), None)
        
            if player_horse:
                player_horse_name = f"{player_horse['name']} (Your Horse)"
                
                # Remove any existing player horse entries
                st.session_state.horses = [h for h in st.session_state.horses if not h['name'].endswith('(Your Horse)')]
                
                # Calculate certification penalties
                certs = player_horse.get('certifications', {})
                required_certs = ['health_certificate', 'racing_license', 'performance_permit']
                missing_required = [cert for cert in required_certs if not certs.get(cert, False)]
                certification_penalty = len(missing_required) * 0.1  # 10% penalty per missing cert
                
                # Apply certification penalty to speed
                effective_speed = player_horse['speed'] * (1 - certification_penalty)
                
                # Add player's horse with enhanced stats (including certification effects)
                player_race_horse = {
                    "name": player_horse_name,
                    "base_speed": effective_speed,
                    "endurance": player_horse['stamina'],
                    "mudder": player_horse['breed'] in ['Quarter Horse', 'Mustang'],
                    "temperament": "proud" if player_horse['breed'] == 'Thoroughbred' else "steady",
                    "race_history": [],
                    "stable": "Your Stable",
                    "story": f"Your prized {player_horse['name']}, trained and cared for by you!" + (f" (Racing with {len(missing_required)} cert penalties)" if missing_required else ""),
                    "player_owned": True,
                    "horse_id": player_horse['id'],
                    "certification_penalty": certification_penalty
                }
                entered_player_horses.append(player_race_horse)
        
        # Add all valid entered horses to the race
        st.session_state.horses.extend(entered_player_horses)
        
        # Remove any invalid horse IDs that no longer exist
        valid_horse_ids = [h['horse_id'] for h in entered_player_horses if 'horse_id' in h]
        if len(valid_horse_ids) < len(st.session_state.horses_entered_in_race):
            st.session_state.horses_entered_in_race = valid_horse_ids
            if len(st.session_state.horses_entered_in_race) > len(valid_horse_ids):
                st.success("⚠️ Some previously entered horses are no longer available and have been removed from the race.")
    
    st.write(f"**Gold:** {st.session_state.money:.2f}")
    st.write(f"**Casino Revenue:** ${st.session_state.casino['cash']:.2f}")
    
    # Horse Entry Section
    healthy_horses = [h for h in owned_horses if h.get('health', 100) > 50]  # Need >50 health to race
    
    if healthy_horses:
        st.markdown("### 🏁 Enter Your Horses (Up to 5)")
        
        # Show currently entered horses
        if st.session_state.horses_entered_in_race:
            st.write("**Currently Entered:**")
            for i, horse_id in enumerate(st.session_state.horses_entered_in_race):
                horse = next((h for h in owned_horses if h['id'] == horse_id), None)
                if horse:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"🐎 {horse['name']} - Speed: {horse.get('speed', 5):.1f}, Stamina: {horse.get('stamina', 5):.1f}")
                    with col2:
                        if st.button("❌", key=f"remove_{horse_id}", help="Remove from race"):
                            st.session_state.horses_entered_in_race.remove(horse_id)
                            st.rerun()
        
        # Show horses available to add (not already entered)
        available_horses = [h for h in healthy_horses if h['id'] not in st.session_state.horses_entered_in_race]
        
        if available_horses and len(st.session_state.horses_entered_in_race) < 5:
            st.write("**Available Horses:**")
            selected_horse = st.selectbox(
                f"Choose horse to add ({len(st.session_state.horses_entered_in_race)}/5 entered):",
                [None] + available_horses,
                format_func=lambda h: "Select a horse..." if h is None else f"{h['name']} ({h.get('breed', 'Unknown')}) - Speed: {h.get('speed', 5):.1f}, Stamina: {h.get('stamina', 5):.1f}, Health: {h.get('health', 100)}"
            )
        
            if selected_horse is not None:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"🐎 **{selected_horse['name']}** ({selected_horse.get('breed', 'Unknown')})")
                    st.write(f"⚡ Speed: {selected_horse.get('speed', 5):.1f} | 💪 Stamina: {selected_horse.get('stamina', 5):.1f} | ❤️ Health: {selected_horse.get('health', 100)}")
                    st.write(f"🏆 Record: {selected_horse.get('wins', 0)}/{selected_horse.get('races', 0)} wins")
                    st.caption("Entry fee: $50 per horse (paid from cash or added to stable liabilities)")
                
                with col2:
                    # Check certification status before allowing race entry
                    # Check if horse has required certifications
                    certs = selected_horse.get('certifications', {})
                    cert_status = {
                        'health_certificate': certs.get('health_certificate', False),
                        'racing_license': certs.get('racing_license', False),
                        'bloodline_registration': certs.get('bloodline_registration', False),
                        'performance_permit': certs.get('performance_permit', False),
                        'insurance_coverage': certs.get('insurance_coverage', False)
                    }
                    
                    # Check if all required certifications are present
                    required_certs = ['health_certificate', 'racing_license', 'performance_permit']
                    missing_required = [cert for cert in required_certs if not cert_status[cert]]
                    
                    # Optional certifications for better odds
                    optional_certs = ['bloodline_registration', 'insurance_coverage']
                    missing_optional = [cert for cert in optional_certs if not cert_status[cert]]
                    
                    if missing_required:
                        st.warning("⚠️ **RACING WITHOUT FULL CERTIFICATION**")
                        st.write("Missing certifications (impacts performance):")
                        cert_names = {
                            'health_certificate': '🩺 Health Certificate',
                            'racing_license': '🏆 Racing License',
                            'performance_permit': '⚡ Performance Permit'
                        }
                        for cert in missing_required:
                            st.write(f"• {cert_names[cert]} - reduces speed by 10%")
                        st.caption("📋 Visit the Horse Stable tab → 🏥 Horse Certifications to improve performance")
                        
                        # Allow racing but with penalties
                        if st.button("🏁 Race Anyway ($50)", key="enter_horse_uncertified"):
                            # Apply same logic as certified horses
                            try:
                                from stable_business import handle_race_entry_fee
                                handle_race_entry_fee(50)
                            except ImportError:
                                if st.session_state.money >= 50:
                                    st.session_state.money -= 50
                                    if "user_id" in st.session_state:
                                        save_user_money(st.session_state.user_id, st.session_state.money)
                                else:
                                    st.warning("Not enough money for entry fee, but racing anyway!")
                            
                            st.session_state.horses_entered_in_race.append(selected_horse['id'])
                            st.success(f"🎆 {selected_horse['name']} entered with penalties!")
                            if 'logs' not in st.session_state or st.session_state.logs is None or not isinstance(st.session_state.logs, list):
                                st.session_state.logs = []
                            st.session_state.logs.append(f"🏁 Entered {selected_horse['name']} (uncertified) for $50")
                            st.rerun()
                        
                    else:
                        # Horse is race eligible
                        if missing_optional:
                            st.warning("⚠️ **ELIGIBLE** (Recommended certs missing)")
                            for cert in missing_optional:
                                if cert == 'bloodline_registration':
                                    st.caption("📜 Bloodline registration improves odds")
                                elif cert == 'insurance_coverage':
                                    st.caption("🛡️ Insurance protects against injury")
                        else:
                            st.success("✅ **FULLY CERTIFIED**")
                            st.caption("🏆 Maximum racing performance!")
                        
                        if st.button("🏁 Add to Race ($50)", key="enter_horse"):
                            # Always allow race entry - handle payment through liability system
                            try:
                                from stable_business import handle_race_entry_fee
                                handle_race_entry_fee(50)
                            except ImportError:
                                # Fallback if stable_business not available
                                if st.session_state.money >= 50:
                                    st.session_state.money -= 50
                                    # Save money to Firebase
                                    if "user_id" in st.session_state:
                                        save_user_money(st.session_state.user_id, st.session_state.money)
                                else:
                                    st.warning("Not enough money for entry fee, but racing anyway!")
                            
                            st.session_state.horses_entered_in_race.append(selected_horse['id'])
                            st.success(f"🎆 {selected_horse['name']} added to the race!")
                            if 'logs' not in st.session_state or st.session_state.logs is None or not isinstance(st.session_state.logs, list):
                                st.session_state.logs = []
                            st.session_state.logs.append(f"🏁 Entered {selected_horse['name']} in horse race for $50")
                            st.rerun()
        elif len(st.session_state.horses_entered_in_race) >= 5:
            st.info("🏁 Maximum of 5 horses entered. Remove a horse to add another.")
        elif not available_horses:
            st.info("🐎 All your healthy horses are already entered in the race!")
        
        
        if st.session_state.horses_entered_in_race:
            total_fees = len(st.session_state.horses_entered_in_race) * 50
            st.info(f"💰 Total entry fees: ${total_fees} ({len(st.session_state.horses_entered_in_race)} horses × $50)")
        
        st.markdown("---")
    
    elif owned_horses and not healthy_horses:
        st.warning("⚠️ Your horses need >50 health to race. Visit the Stable to care for them!")
    
    elif not owned_horses:
        st.info("💡 **Tip:** Buy horses at the Stable to participate in races!")
    
    # Debug: Show horse status information
    if owned_horses:
        with st.expander("🔍 Debug: Horse Status"):
            st.write(f"**Total owned horses:** {len(owned_horses)}")
            st.write(f"**Healthy horses (>50 health):** {len(healthy_horses)}")
            for horse in owned_horses:
                certs = horse.get('certifications', {})
                required_certs = ['health_certificate', 'racing_license', 'performance_permit']
                missing_required = [cert for cert in required_certs if not certs.get(cert, False)]
                cert_status = "✅ Certified" if not missing_required else f"❌ Missing: {', '.join(missing_required)}"
                st.write(f"• **{horse['name']}** - Health: {horse.get('health', 100)} - {cert_status}")
    
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
    
    with bet_cols[0]:
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
    
    # Generate odds for all horses
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
        
        # Save money to Firebase
        if "user_id" in st.session_state:
            save_user_money(st.session_state.user_id, st.session_state.money)
        
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
        results = []
        for h in st.session_state.horses:
            jockey = JOCKEYS[st.session_state.horses.index(h) % len(JOCKEYS)]
            boost = item_boost if (selected_horse is not None and h["name"] == selected_horse["name"]) else 0
            results.append((copy.deepcopy(h), calculate_adjusted_speed(h, jockey, track, boost)))

        # 🌟 ANIMATED RACE - This is the key enhancement! 🌟
        st.markdown("### 🏁 Race in Progress!")
        race_area = st.empty()
        
        positions = {h[0]["name"]: 0 for h in results}
        finish_line = 30
        finished = []
        
        # Real-time animated race progress
        while len(finished) < len(results):
            time.sleep(0.15)  # Animation delay
            for horse_data, speed in results:
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
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        # Process new multi-bet Win/Place/Show payouts
        process_race_payouts(final_results)
        
        st.markdown("### 🏆 **FINAL RACE RESULTS**")
        
        # Process Derby Points and Achievements
        derby_points_awarded = []
        new_achievements = []
        
        for idx, (h, speed) in enumerate(final_results):
            position = idx + 1
            position_emoji = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "🏃"
            
            # Calculate Derby points for this horse
            points_earned = calculate_derby_points(h['name'], position, current_week)
            if points_earned > 0:
                derby_points_awarded.append((h['name'], position, points_earned))
            
            # Check for new achievements
            career_earnings = 0  # TODO: Track career earnings
            achievements = check_racing_achievements(h['name'], position, current_race['type'], career_earnings)
            if achievements:
                new_achievements.extend([(h['name'], ach) for ach in achievements])
            
            # Display results with points
            points_text = f" (+{points_earned} Derby pts)" if points_earned > 0 else ""
            if h['name'].endswith('(Your Horse)'):
                st.markdown(f"**{position_emoji} {idx+1}. {h['name']} — Speed: {speed:.1f}**{points_text}")
            else:
                st.write(f"{position_emoji} {idx+1}. {h['name']} — Speed: {speed:.1f}{points_text}")
        
        # Show Derby Points Summary
        if derby_points_awarded:
            st.markdown("### 🎯 **Derby Points Awarded**")
            for horse_name, position, points in derby_points_awarded:
                st.write(f"🏆 {horse_name} - {points} points for {position}{'st' if position==1 else 'nd' if position==2 else 'rd' if position==3 else 'th'} place")
        
        # Show New Achievements
        if new_achievements:
            st.markdown("### 🏅 **New Achievements Unlocked!**")
            for horse_name, achievement in new_achievements:
                achievement_info = RACING_ACHIEVEMENTS.get(achievement, {})
                icon = achievement_info.get('icon', '🏆')
                description = achievement_info.get('description', achievement)
                st.success(f"{icon} **{horse_name}** earned: {description}")
                st.balloons()

        # === BLOCKCHAIN-STYLE RACE RECORD SAVING ===
        from firebase_utils import save_race_record, generate_race_id
        from datetime import datetime
        
        # Create comprehensive race record with blockchain-like immutability
        race_record = {
            'race_id': generate_race_id(),
            'date': datetime.now().isoformat(),
            'race_name': current_race['name'],
            'purse': current_race['purse'],
            'race_week': current_week,
            'track_condition': st.session_state.get('weather', 'normal'),
            'field_size': len(final_results),
            'race_type': current_race.get('type', 'standard'),
            'results': [],
            'derby_points_awarded': derby_points_awarded,
            'achievements_earned': new_achievements
        }
        
        # Add detailed result for each horse
        for idx, (horse, final_speed) in enumerate(final_results):
            position = idx + 1
            base_earnings = 1000 if position == 1 else 500 if position == 2 else 250 if position == 3 else 100
            
            # Determine owner and clean horse name
            horse_name = horse['name']
            owner_id = "NPC"
            is_player_horse = False
            
            if horse_name.endswith('(Your Horse)'):
                clean_horse_name = horse_name.replace(' (Your Horse)', '')
                owner_id = st.session_state.get('user_id', 'player')
                is_player_horse = True
            elif horse.get('student_owned'):
                clean_horse_name = horse_name
                owner_id = horse.get('owner_id', 'student')
            else:
                clean_horse_name = horse_name
                owner_id = "NPC"
            
            # Create detailed horse result record
            horse_result = {
                'name': clean_horse_name,
                'display_name': horse_name,  # Keep original display name with (Your Horse)
                'position': position,
                'speed': round(final_speed, 2),
                'prize_money': base_earnings,
                'owner_id': owner_id,
                'is_player_horse': is_player_horse,
                'breed': horse.get('breed', 'Unknown'),
                'stable': horse.get('stable', 'Unknown'),
                'jockey': horse.get('jockey', 'Unknown'),
                'temperament': horse.get('temperament', 'Unknown'),
                'mudder': horse.get('mudder', False),
                'derby_points': next((points for name, pos, points in derby_points_awarded if pos == position), 0)
            }
            
            race_record['results'].append(horse_result)
        
        # Save the complete race record to blockchain-style storage
        try:
            save_race_record(race_record)
            st.success("🔗 Race permanently recorded to blockchain-style history!")
        except Exception as e:
            st.error(f"Failed to save race record: {e}")
        
        # Update Global Horse History for all horses in the race (legacy system)
        from firebase_utils import update_horse_race_record
        track_condition = st.session_state.get('weather', 'normal')
        
        for idx, (horse, final_speed) in enumerate(final_results):
            position = idx + 1
            
            # Calculate earnings based on position
            base_earnings = 1000 if position == 1 else 500 if position == 2 else 250 if position == 3 else 100
            
            # Determine owner ID
            horse_name = horse['name']
            owner_id = "NPC"
            if horse_name.endswith('(Your Horse)'):
                horse_name = horse_name.replace(' (Your Horse)', '')
                owner_id = st.session_state.get('user_id', 'player')
            elif horse.get('student_owned'):
                owner_id = horse.get('owner_id', 'student')
            
            # Create race result record
            race_result = {
                'position': position,
                'earnings': base_earnings,
                'final_speed': final_speed,
                'track_condition': track_condition,
                'field_size': len(final_results),
                'race_type': 'standard',
                'breed': horse.get('breed', 'Unknown')
            }
            
            # Update global history (async, don't wait for result to avoid slowing down UI)
            try:
                update_horse_race_record(horse_name, race_result, owner_id)
            except Exception as e:
                # Don't show error to user, just log it silently
                pass

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
        
        # Track casino revenue
        if "transactions" not in st.session_state.casino:
            st.session_state.casino["transactions"] = []
        
        horse_name = selected_horse["name"] if selected_horse else "Unknown"
        is_own_horse = selected_horse and selected_horse.get('name', '').endswith('(Your Horse)')
        
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
        
        # Calculate prize purse for owner's entered horse (regardless of betting outcome)
        prize_purse = 0
        if is_own_horse and selected_horse:
            # Find player's horse position in final results
            finishing_position = None
            for i, (horse_data, speed) in enumerate(final_results):
                if horse_data.get('name') == selected_horse.get('name'):
                    finishing_position = i + 1
                    break
            
            # Substantial prize purse based on finishing position
            if finishing_position and finishing_position == 1:
                prize_purse = 2500  # First place: $2,500
            elif finishing_position and finishing_position == 2:
                prize_purse = 1500  # Second place: $1,500
            elif finishing_position and finishing_position == 3:
                prize_purse = 750   # Third place: $750
            elif finishing_position and finishing_position == 4:
                prize_purse = 300   # Fourth place: $300
            elif finishing_position:
                prize_purse = 100   # Participation prize: $100
            
            # Handle jockey payment from prize purse
            jockey_payment = 0
            jockey_percentage = 0
            jockey_name = "House Jockey"
            net_earnings = prize_purse
            
            # Check if player has jockey contracts
            if 'jockey_contracts' in st.session_state:
                # Find assigned jockey for this horse
                horse_name = selected_horse['name'] if selected_horse else "Unknown"
                for j_name, contract in st.session_state.jockey_contracts.items():
                    if contract.get('assigned_horse') == horse_name:
                        jockey_name = j_name
                        jockey_percentage = contract['percentage']
                        jockey_payment = (prize_purse * jockey_percentage) / 100
                        net_earnings = prize_purse - jockey_payment
                        
                        # Update jockey stats
                        contract['total_earnings'] = contract.get('total_earnings', 0) + jockey_payment
                        if finishing_position == 1:
                            contract['races_won'] = contract.get('races_won', 0) + 1
                        break
            
            # Add accounting record
            if prize_purse > 0:
                from datetime import datetime
                # Import the function here to avoid circular imports
                try:
                    from horse_stable import add_race_transaction
                    add_race_transaction(
                        horse_name=selected_horse['name'] if selected_horse else "Unknown",
                        jockey_name=jockey_name,
                        prize_purse=prize_purse,
                        jockey_percentage=jockey_percentage,
                        jockey_payment=jockey_payment,
                        net_earnings=net_earnings,
                        race_date=datetime.now().strftime('%Y-%m-%d %H:%M')
                    )
                except ImportError:
                    pass  # Function not available
            
            # Add net earnings to player money (after jockey payment)
            st.session_state.money += net_earnings
            
            # Save money to Firebase
            if "user_id" in st.session_state:
                save_user_money(st.session_state.user_id, st.session_state.money)
            
            # Prize purse notification with balloons for top 3
            if finishing_position and finishing_position <= 3:
                st.balloons()
                
            if finishing_position == 1:
                st.success(f"🏆 **WINNER'S PURSE!** Your horse finished 1st! Prize: ${prize_purse:,}")
            elif finishing_position == 2:
                st.success(f"🥈 **RUNNER-UP PURSE!** Your horse finished 2nd! Prize: ${prize_purse:,}")
            elif finishing_position == 3:
                st.info(f"🥉 **SHOW PURSE!** Your horse finished 3rd! Prize: ${prize_purse:,}")
            elif finishing_position == 4:
                st.info(f"� **GOOD EFFORT PURSE!** Your horse finished 4th! Prize: ${prize_purse:,}")
            else:
                st.info(f"🐎 **PARTICIPATION PURSE!** Your horse finished {finishing_position}th! Prize: ${prize_purse:,}")
            
            if 'logs' not in st.session_state:
                st.session_state.logs = []
            
            position_suffix = 'st' if finishing_position == 1 else 'nd' if finishing_position == 2 else 'rd' if finishing_position == 3 else 'th'
            st.session_state.logs.append(f"🏇 Your horse finished {finishing_position}{position_suffix} and earned ${prize_purse:,} prize purse!")
            
            # Update horse statistics in stable
            if selected_horse and selected_horse.get('player_owned') and selected_horse.get('horse_id'):
                horse_id = selected_horse['horse_id']
                if horse_id in st.session_state.get('stable_horses', {}):
                    # Update race count and wins
                    st.session_state.stable_horses[horse_id]['races'] = st.session_state.stable_horses[horse_id].get('races', 0) + 1
                    if finishing_position == 1:
                        st.session_state.stable_horses[horse_id]['wins'] = st.session_state.stable_horses[horse_id].get('wins', 0) + 1
                    
                    # Track career earnings
                    if 'career_earnings' not in st.session_state.stable_horses[horse_id]:
                        st.session_state.stable_horses[horse_id]['career_earnings'] = 0
                    st.session_state.stable_horses[horse_id]['career_earnings'] += prize_purse
                    
                    # Track best finish
                    if 'best_finish' not in st.session_state.stable_horses[horse_id] or finishing_position < st.session_state.stable_horses[horse_id]['best_finish']:
                        st.session_state.stable_horses[horse_id]['best_finish'] = finishing_position
                    
                    # Save updated stats to Firebase
                    from firebase_utils import save_horse_data
                    save_horse_data(st.session_state.get('user_id', 'default_user'), st.session_state.stable_horses)

        # Handle betting results separately from prize purse
        if won:
            if not is_own_horse:  # Only show betting celebration if not already celebrating prize purse
                st.balloons()
            st.success(f"🎉 **BETTING WIN!** +${winnings:.2f} from your bet")
            st.session_state.money += winnings
            # Save money to Firebase
            if "user_id" in st.session_state:
                save_user_money(st.session_state.user_id, st.session_state.money)
            st.session_state.casino["cash"] -= (winnings - total_cost)
        else:
            st.warning("💔 Better luck next time with your bet…")
            st.session_state.casino["cash"] += total_cost
            if 'logs' not in st.session_state:
                st.session_state.logs = []
            st.session_state.logs.append(f"🎰 Casino earned ${total_cost:.2f} from horse racing betting")
        
        # Refresh odds for next race and reset horse entry
        st.session_state.horse_odds = {h['name']: round(random.uniform(1.5, 8.0), 1) for h in st.session_state.horses}
        st.session_state.horse_entered_in_race = None

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
                        st.write(f" - Position {r['position']} (Time: {r.get('time', 0):.1f}s)")
                    st.markdown("---")
                else:
                    st.write(f"**{h['name']}** - No race history yet")
    
    with col2:
        if st.button("💰 View Casino Stats"):
            st.markdown("### 🎰 Casino Horse Racing Revenue")
            st.write(f"**Total Revenue:** ${st.session_state.casino['cash']:.2f}")
            st.write(f"**Total Races:** {len(st.session_state.casino.get('transactions', []))}")
            
            if st.session_state.casino.get('transactions'):
                st.markdown("**Recent Transactions:**")
                for i, trans in enumerate(st.session_state.casino['transactions'][-5:]):
                    result = "WON" if trans['won'] else "LOST"
                    st.write(f"{i+1}. ${trans['amount']:.2f} on {trans['horse']} ({trans['bet_type']}) - {result}")

    # Racing Season Information Tabs
    st.markdown("---")
    season_tab1, season_tab2, season_tab3, season_tab4 = st.tabs(["🎯 Derby Standings", "🏅 Achievements", "� Horse Racing Records", "📜 Race History"])
    
    with season_tab1:
        render_derby_qualification_status()
    
    with season_tab2:
        render_racing_achievements()
    
    with season_tab3:
        st.markdown("### 📊 Horse Racing Records")
        
        # Display all horses and their race history
        all_horses = []
        
        # Add player horses
        stable_horses = st.session_state.get('stable_horses', {})
        for horse_name in stable_horses.keys():
            all_horses.append((horse_name, True))  # (name, is_owned)
        
        # Add default racing horses
        for horse in HORSES:
            all_horses.append((horse['name'], False))
        
        # Load and display race history for each horse
        from firebase_utils import load_horse_race_history
        
        for horse_name, is_owned in all_horses:
            with st.expander(f"🐎 {horse_name}{' (Your Horse)' if is_owned else ''}"):
                history = load_horse_race_history(horse_name)
                
                if history:
                    st.markdown(f"**Total Races:** {len(history)}")
                    
                    # Calculate statistics
                    wins = sum(1 for race in history if race.get('position') == 1)
                    podium_finishes = sum(1 for race in history if race.get('position', 99) <= 3)
                    total_earnings = sum(race.get('prize_money', 0) for race in history)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Wins", wins)
                    with col2:
                        st.metric("Podium", podium_finishes)
                    with col3:
                        st.metric("Win %", f"{(wins/len(history)*100):.1f}%" if history else "0%")
                    with col4:
                        st.metric("Earnings", f"${total_earnings:,}")
                    
                    # Recent race history
                    st.markdown("**Recent Races:**")
                    for race in history[:10]:  # Show last 10 races
                        date_str = race.get('date', 'Unknown')[:10] if race.get('date') else 'Unknown'
                        position = race.get('position', '?')
                        race_name = race.get('race_name', 'Unknown Race')
                        prize = race.get('prize_money', 0)
                        track = race.get('track_condition', 'normal')
                        
                        position_emoji = "🥇" if position == 1 else "🥈" if position == 2 else "🥉" if position == 3 else "🏃"
                        
                        st.write(f"{position_emoji} **{position}{'st' if position==1 else 'nd' if position==2 else 'rd' if position==3 else 'th'}** place • {date_str} • {race_name} • ${prize} • {track} track")
                else:
                    st.info("No race history yet")
    
    with season_tab4:
        st.markdown("### 📜 Complete Race History (Blockchain-Style)")
        
        # Load recent race records
        from firebase_utils import load_race_records
        race_records = load_race_records(20)  # Load last 20 races
        
        if race_records:
            st.markdown(f"**Showing {len(race_records)} most recent races**")
            
            # Sort by date (newest first)
            sorted_races = sorted(race_records.items(), key=lambda x: x[1].get('date', ''), reverse=True)
            
            for race_id, race_data in sorted_races:
                with st.expander(f"🏁 {race_data.get('race_name', 'Unknown Race')} - {race_data.get('date', 'Unknown')[:16]}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Race ID:** {race_id}")
                        st.write(f"**Date:** {race_data.get('date', 'Unknown')[:16]}")
                        st.write(f"**Purse:** ${race_data.get('purse', 0):,}")
                    
                    with col2:
                        st.write(f"**Track:** {race_data.get('track_condition', 'normal').title()}")
                        st.write(f"**Field Size:** {race_data.get('field_size', 0)} horses")
                        st.write(f"**Week:** {race_data.get('race_week', '?')}")
                    
                    with col3:
                        derby_points = race_data.get('derby_points_awarded', [])
                        if derby_points:
                            st.write(f"**Derby Points:** {len(derby_points)} horses earned points")
                        achievements = race_data.get('achievements_earned', [])
                        if achievements:
                            st.write(f"**Achievements:** {len(achievements)} earned")
                    
                    # Results table
                    st.markdown("**Results:**")
                    results = race_data.get('results', [])
                    
                    if results:
                        for i, result in enumerate(results):
                            position = result.get('position', i+1)
                            horse_name = result.get('display_name', result.get('name', 'Unknown'))
                            speed = result.get('speed', 0)
                            prize = result.get('prize_money', 0)
                            owner = result.get('owner_id', 'Unknown')
                            
                            position_emoji = "🥇" if position == 1 else "🥈" if position == 2 else "🥉" if position == 3 else "🏃"
                            
                            st.write(f"{position_emoji} **{position}.** {horse_name} • Speed: {speed} • Prize: ${prize} • Owner: {owner}")
        else:
            st.info("No race records found. Run some races to see history!")

# Entry point for standalone testing
if __name__ == "__main__":
    render_horse_racing()