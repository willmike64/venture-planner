import streamlit as st # type: ignore


if 'stable_name' not in st.session_state:
    st.session_state['stable_name'] = ''

with st.sidebar:
    st.header("🏇 Your Stable")
    stable_name = st.text_input("Stable Name", value=st.session_state['stable_name'], key="sidebar_stable_name")
    if stable_name:
        st.session_state['stable_name'] = stable_name
import streamlit as st # type: ignore
import random
from datetime import datetime, timedelta
from stable_business import (
    render_financial_dashboard,
    process_daily_log,
    check_expansion_eligibility,
    calculate_daily_operating_costs,
    DAILY_BASE_COSTS,
    handle_race_entry_fee
)
from firebase_utils import save_horse_data, load_horse_data, initialize_user_session, save_user_money

# --- FUN HORSE NAMES ---
HORSE_PREFIXES = [
    "Sir", "Lady", "Captain", "Princess", "Lord", "Duchess", "Baron", "Countess", "Duke", "Queen",
    "King", "Prince", "Earl", "Admiral", "General", "Commander", "Chief", "Master", "Dame", "Madam",
    "Doctor", "Professor", "Sergeant", "Major", "Colonel", "Judge", "Honorable", "Noble", "Royal", "Grand"
]

HORSE_FIRST_NAMES = [
    "Thunderbolt", "Lightning", "Starfire", "Moonbeam", "Sundance", "Stormchaser", "Windwhisper", "Firecracker",
    "Shadowdancer", "Goldstreak", "Silverwind", "Rapidfire", "Blaze", "Comet", "Meteor", "Galaxy", "Nebula",
    "Phoenix", "Dragon", "Unicorn", "Pegasus", "Tornado", "Hurricane", "Cyclone", "Tempest", "Thunder",
    "Sparkle", "Glitter", "Shimmer", "Dazzle", "Twinkle", "Glow", "Radiance", "Brilliance", "Flash",
    "Rocket", "Jet", "Zoom", "Dash", "Sprint", "Rush", "Bolt", "Speed", "Turbo", "Nitro", "Boost",
    "Magic", "Mystery", "Wonder", "Dream", "Fantasy", "Miracle", "Marvel", "Mystic", "Enchant", "Charm",
    "Courage", "Valor", "Honor", "Glory", "Victory", "Triumph", "Champion", "Hero", "Legend", "Destiny",
    "Fortune", "Lucky", "Chance", "Hope", "Faith", "Joy", "Happiness", "Delight", "Cheer", "Spirit",
    "Rebel", "Rogue", "Bandit", "Outlaw", "Maverick", "Wildcard", "Chaos", "Havoc", "Mischief", "Trouble"
]

HORSE_LAST_NAMES = [
    "Thunderhoof", "Windrunner", "Stormrider", "Firetail", "Lightningbolt", "Stargazer", "Moonwalker", "Sunburst",
    "Gallopper", "Speedster", "Racer", "Charger", "Sprinter", "Dasher", "Rusher", "Flyer", "Soarer", "Glider",
    "Dreamweaver", "Spellbinder", "Enchanter", "Magician", "Sorcerer", "Wizard", "Mystique", "Phantom", "Spirit",
    "Destroyer", "Conqueror", "Dominator", "Crusher", "Smasher", "Breaker", "Shatterer", "Blaster", "Boomer",
    "Whirlwind", "Cyclone", "Typhoon", "Blizzard", "Avalanche", "Earthquake", "Volcano", "Inferno", "Wildfire",
    "Magnificent", "Majestic", "Glorious", "Spectacular", "Fantastic", "Incredible", "Amazing", "Awesome", "Epic",
    "Unstoppable", "Invincible", "Unbeatable", "Supreme", "Ultimate", "Perfect", "Flawless", "Peerless", "Elite",
    "the Bold", "the Brave", "the Fierce", "the Mighty", "the Great", "the Magnificent", "the Legendary", "the Swift"
]

SILLY_NAMES = [
    "Pancake McFlufferson", "Sir Neighs-A-Lot", "Buttercup Biscuit", "Marshmallow Mayhem", "Pickle Pants",
    "Snuggles McGallop", "Whoopee Cushion", "Jellybean Jester", "Bubblegum Bandit", "Taco Tuesday",
    "Captain Carrot", "Professor Pony", "Disco Dave", "Funky Frank", "Groovy Gary", "Silly Sally",
    "Wacky Walter", "Crazy Carl", "Loopy Lucy", "Nutty Nancy", "Bonkers Bob", "Giggles Galore",
    "Tickles McTrot", "Wiggles Wonder", "Noodles Napoleon", "Spaghetti Steve", "Meatball Mike",
    "Cookie Monster", "Cupcake Cutie", "Donut Daredevil", "Pizza Pete", "Burger Bob", "Hotdog Harry"
]

FOOD_NAMES = [
    "Cinnamon Swirl", "Chocolate Chip", "Vanilla Bean", "Caramel Crunch", "Peppermint Twist",
    "Strawberry Shortcake", "Blueberry Muffin", "Honey Glazed", "Sugar Rush", "Candy Cane",
    "Peanut Butter Cup", "Gingerbread", "Apple Pie", "Cherry Bomb", "Lemon Drop", "Peach Cobbler",
    "Bacon Bits", "Waffle Wonder", "French Toast", "Cereal Killer", "Milkshake Madness"
]

SPACE_NAMES = [
    "Cosmic Cruiser", "Stellar Stallion", "Galactic Galloper", "Asteroid Annie", "Meteor Mike",
    "Supernova Sally", "Black Hole Betty", "Quasar Quest", "Pulsar Power", "Comet Chaser",
    "Solar Flare", "Lunar Eclipse", "Mars Rover", "Saturn's Ring", "Jupiter's Storm", "Venus Fly",
    "Mercury Rising", "Pluto's Revenge", "Alpha Centauri", "Milky Way Warrior", "Starlight Express"
]

MYTHOLOGY_NAMES = [
    "Zeus's Thunder", "Athena's Wisdom", "Apollo's Light", "Artemis Arrow", "Hercules Might",
    "Pegasus Flight", "Medusa's Gaze", "Phoenix Rising", "Thor's Hammer", "Odin's Raven",
    "Loki's Trick", "Freya's Beauty", "Poseidon's Wave", "Hades Fury", "Demeter's Harvest",
    "Dionysus Party", "Hermes Speed", "Aphrodite's Kiss", "Ares Battle", "Hera's Crown"
]

CELEBRITY_NAMES = [
    "Neigh-oncé", "Brad Trot", "Leonardo DiCloprio", "Will Neigh", "Johnny Hopp", "Tom Cruise Control",
    "Scarlett Johoofson", "Ryan Galloping", "Jennifer Anistallion", "George Clooney Tunes",
    "Morgan Freehorse", "Denzel Washingallop", "Meryl Streeep", "Robert Downey Jr Mint",
    "Chris Hemshorse", "Emma Stallion", "Taylor Swifthooves", "Ed Sheeran's Horse",
    "Oprah Whinney", "Ellen DeGallop", "Jimmy Fallon Down", "Stephen Coldhoof", "Conan O'Bridle"
]

WEATHER_NAMES = [
    "Thunderstorm Tracy", "Hurricane Hannah", "Blizzard Bob", "Tornado Tom", "Cyclone Cindy",
    "Drizzle Dave", "Foggy Fred", "Sunny Susan", "Cloudy Carl", "Windy William", "Frosty Frank",
    "Hailstone Harry", "Lightning Larry", "Rainbow Rita", "Misty Mike", "Stormy Steve"
]

ROYAL_TITLES = [
    "His Royal Horseness", "Her Majesty Mane", "The Duke of Gallop", "Duchess of Derby",
    "Prince of Prancing", "Princess Pony", "Earl of Elegance", "Countess Canter",
    "Baron von Bolt", "Lady Lightning", "Sir Speedy", "Dame Dash"
]

# --- JOCKEY CONTRACT SYSTEM ---
AVAILABLE_JOCKEYS = [
    {
        "name": "Lightning Lou", 
        "skill": 9.2, 
        "experience": 8.5, 
        "win_rate": 0.28,
        "preferred_percentage": 12,  # 12% of prize purse
        "minimum_percentage": 8,    # Will accept as low as 8%
        "specialty": "Speed Races",
        "bio": "Former champion with lightning-fast reflexes and strategic mind."
    },
    {
        "name": "Sassy Sadie", 
        "skill": 8.8, 
        "experience": 9.0, 
        "win_rate": 0.25,
        "preferred_percentage": 10,
        "minimum_percentage": 6,
        "specialty": "Long Distance",
        "bio": "Veteran jockey known for patience and endurance strategy."
    },
    {
        "name": "Whiskey Jack", 
        "skill": 8.5, 
        "experience": 7.2, 
        "win_rate": 0.22,
        "preferred_percentage": 9,
        "minimum_percentage": 5,
        "specialty": "Muddy Tracks",
        "bio": "Rough-and-tumble rider who thrives in difficult conditions."
    },
    {
        "name": "Moonshine Molly", 
        "skill": 9.0, 
        "experience": 8.0, 
        "win_rate": 0.26,
        "preferred_percentage": 11,
        "minimum_percentage": 7,
        "specialty": "Night Racing",
        "bio": "Mysterious jockey with uncanny intuition for horse psychology."
    },
    {
        "name": "Sheriff Stirrup", 
        "skill": 8.2, 
        "experience": 9.5, 
        "win_rate": 0.24,
        "preferred_percentage": 8,
        "minimum_percentage": 4,
        "specialty": "Crowd Control",
        "bio": "Old-school jockey who keeps calm under pressure."
    },
    {
        "name": "Dusty Dan", 
        "skill": 7.8, 
        "experience": 6.8, 
        "win_rate": 0.18,
        "preferred_percentage": 7,
        "minimum_percentage": 3,
        "specialty": "Budget Racing",
        "bio": "Hardworking rookie looking to prove himself on any horse."
    },
    {
        "name": "Crazy Colt Carter", 
        "skill": 9.5, 
        "experience": 7.5, 
        "win_rate": 0.30,
        "preferred_percentage": 15,
        "minimum_percentage": 10,
        "specialty": "High Stakes",
        "bio": "Unpredictable genius who either wins big or crashes spectacularly."
    }
]

def get_jockey_contracts():
    """Get current jockey contracts from session state"""
    if 'jockey_contracts' not in st.session_state:
        st.session_state.jockey_contracts = {}
    return st.session_state.jockey_contracts

def get_race_accounting():
    """Get race accounting history from session state"""
    if 'race_accounting' not in st.session_state:
        st.session_state.race_accounting = []
    return st.session_state.race_accounting

def add_race_transaction(horse_name, jockey_name, prize_purse, jockey_percentage, jockey_payment, net_earnings, race_date):
    """Add a race transaction to accounting records"""
    accounting = get_race_accounting()
    transaction = {
        "date": race_date,
        "horse": horse_name,
        "jockey": jockey_name,
        "gross_prize": prize_purse,
        "jockey_percentage": jockey_percentage,
        "jockey_payment": jockey_payment,
        "net_earnings": net_earnings,
        "race_type": "Regular Race"
    }
    accounting.append(transaction)
    st.session_state.race_accounting = accounting
    # Track race prize money in business analytics
    try:
        from stable_business import track_revenue, track_expense
        if prize_purse > 0:
            track_revenue(prize_purse, "race")
        if jockey_payment > 0:
            track_expense(jockey_payment, "jockey_payment")
        if net_earnings > 0:
            track_revenue(net_earnings, "race_net")
    except ImportError:
        pass
    # Save to Firebase
    if "user_id" in st.session_state:
        from firebase_utils import save_user_data
        save_user_data(st.session_state.user_id + "_accounting", accounting)

def generate_fun_horse_name():
    """Generate a fun, creative horse name"""
    name_type = random.choice(["formal", "creative", "silly", "food", "space", "mythology", "celebrity", "weather", "royal"])
    
    if name_type == "formal":
        # Title + First + Last format
        prefix = random.choice(HORSE_PREFIXES)
        first = random.choice(HORSE_FIRST_NAMES)
        last = random.choice(HORSE_LAST_NAMES)
        return f"{prefix} {first} {last}"
    
    elif name_type == "creative":
        # First + Last format
        first = random.choice(HORSE_FIRST_NAMES)
        last = random.choice(HORSE_LAST_NAMES)
        return f"{first} {last}"
    
    elif name_type == "food":
        return random.choice(FOOD_NAMES)
    
    elif name_type == "space":
        return random.choice(SPACE_NAMES)
    
    elif name_type == "mythology":
        return random.choice(MYTHOLOGY_NAMES)
    
    elif name_type == "celebrity":
        return random.choice(CELEBRITY_NAMES)
    
    elif name_type == "weather":
        return random.choice(WEATHER_NAMES)
    
    elif name_type == "royal":
        return random.choice(ROYAL_TITLES)
    
    else:  # silly
        return random.choice(SILLY_NAMES)

# --- HORSE BREEDS ---
HORSE_BREEDS = {
    "Thoroughbred": {
        "base_price": 500,
        "speed_range": (7.0, 9.5),
        "stamina_range": (6.0, 8.5),
        "training_cost": 25,
        "description": "Elite racing breed - fast but requires premium care"
    },
    "Quarter Horse": {
        "base_price": 300,
        "speed_range": (6.5, 8.5),
        "stamina_range": (7.0, 9.0),
        "training_cost": 15,
        "description": "Balanced breed - good speed and endurance"
    },
    "Arabian": {
        "base_price": 400,
        "speed_range": (6.0, 8.0),
        "stamina_range": (8.0, 9.5),
        "training_cost": 20,
        "description": "Endurance specialist - excels in long races"
    },
    "Mustang": {
        "base_price": 200,
        "speed_range": (5.5, 7.5),
        "stamina_range": (6.0, 8.0),
        "training_cost": 10,
        "description": "Tough wild breed - scrappy and unpredictable"
    },
    "Mixed": {
        "base_price": 150,
        "speed_range": (5.0, 7.0),
        "stamina_range": (5.0, 7.0),
        "training_cost": 15,
        "description": "Mixed breed - balanced characteristics from parent breeds"
    }
}

# --- UI + LOGIC ---
def render_horse_stable():
    # --- Stable Name Sidebar ---
    if 'stable_name' not in st.session_state:
        st.session_state['stable_name'] = ''

    with st.sidebar:
        st.header("🏇 Your Stable")
        stable_name = st.text_input("Stable Name", value=st.session_state['stable_name'], key="sidebar_stable_name")
        if stable_name:
            st.session_state['stable_name'] = stable_name
    # Initialize Derby points from Firebase
    from horse_racing import initialize_derby_points_from_firebase
    initialize_derby_points_from_firebase()
    
    # Header with stable info
    col_title, col_money = st.columns([2, 1])
    with col_title:
        st.title("🏇 Gold Creek Stables")
        st.caption("🐴 Premier Horse Racing & Training Facility")
    with col_money:
        st.metric("💰 Stable Balance", f"${st.session_state.get('money', 0):,.2f}")
    
    st.markdown("---")
    
    # Money restoration for mwill1003@gmail.com (minimized)
    if st.session_state.get('user_id') == 'mwill1003_gmail_com':
        with st.expander("🔧 Money Recovery System"):
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🎯 $25,000"):
                    from firebase_utils import restore_user_money
                    if restore_user_money(st.session_state.user_id, 25000):
                        st.success("✅ Restored!")
                        st.rerun()
            with col2:
                if st.button("🏆 $50,000"):
                    from firebase_utils import restore_user_money
                    if restore_user_money(st.session_state.user_id, 50000):
                        st.success("✅ Restored!")
                        st.rerun()
            with col3:
                custom_amount = st.number_input("Custom:", min_value=1000, max_value=100000, value=25000)
                if st.button("💎 Restore"):
                    from firebase_utils import restore_user_money
                    if restore_user_money(st.session_state.user_id, custom_amount):
                        st.success(f"✅ ${custom_amount:,} restored!")
                        st.rerun()

    # Initialize user session with Firebase data
    if "user_id" in st.session_state:
        initialize_user_session(st.session_state.user_id)
    
    # Initialize session state variables ONLY if not loaded from Firebase and no user logged in
    if "money" not in st.session_state:
        if "user_id" not in st.session_state or st.session_state.user_id.startswith("session_"):
            st.session_state.money = 1000.0
    
    if "stable_horses" not in st.session_state:
        st.session_state.stable_horses = {}

    # Get current horses
    horses = st.session_state.get("stable_horses", {})
    
    # Check if this is a temporary session
    if not horses and st.session_state.get("user_id", "").startswith("session_"):
        st.info("💡 You're using a temporary session. Log in to save your horses permanently!")
    
    # Ensure horses is always a dict
    if not isinstance(horses, dict):
        horses = {}
    
    # Ensure all horses have required certification fields (backwards compatibility)
    for horse_name, horse_data in horses.items():
        if isinstance(horse_data, dict):
            if 'certifications' not in horse_data:
                horse_data['certifications'] = {
                    'health_certificate': False,
                    'racing_license': False,
                    'bloodline_registration': False,
                    'performance_permit': False,
                    'insurance_coverage': False
                }
            if 'certification_expiry' not in horse_data:
                horse_data['certification_expiry'] = {}

    # ========== MAIN HORSE DISPLAY - FIRST AND PROMINENT ==========
    st.markdown("## 🐎 **Your Racing Stable**")
    
    if horses:
        # Stable overview stats
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        total_horses = len(horses)
        total_races = sum(stats.get('races', 0) for stats in horses.values())
        total_wins = sum(stats.get('wins', 0) for stats in horses.values())
        win_rate = (total_wins / max(total_races, 1)) * 100 if total_races > 0 else 0
        with col_stats1:
            st.metric("🐴 Total Horses", total_horses)
        with col_stats2:
            st.metric("🏁 Total Races", total_races)
        with col_stats3:
            st.metric("🏆 Total Wins", total_wins)
        with col_stats4:
            st.metric("📊 Win Rate", f"{win_rate:.1f}%")
        st.markdown("---")

        # Individual horse cards - BEAUTIFUL DISPLAY
        with st.expander("### 🏇 Individual Horse Profiles", expanded=False):
            # Create a nice grid layout for horses
            horses_list = list(horses.items())
            for i in range(0, len(horses_list), 2):  # Display 2 horses per row
                cols = st.columns(2)
                for j, (name, stats) in enumerate(horses_list[i:i+2]):
                    with cols[j]:
                        # Create a bordered container for each horse
                        with st.container():
                            st.markdown(f"### 🐎 **{name}**")
                            # Horse basic info
                            col_breed, col_health = st.columns(2)
                            with col_breed:
                                st.write(f"**Breed:** {stats['breed']}")
                            with col_health:
                                health = stats.get('health', 100)
                                if health >= 80:
                                    st.success(f"❤️ Health: {health}%")
                                elif health >= 60:
                                    st.warning(f"💛 Health: {health}%")
                                else:
                                    st.error(f"💔 Health: {health}%")
                            # Performance stats with visual bars
                            st.write("**📊 Performance:**")
                            speed = stats.get('speed', 5)
                            stamina = stats.get('stamina', 5)
                            col_speed, col_stamina = st.columns(2)
                            with col_speed:
                                # Adjust scale for horses with stats above 10
                                max_speed = max(15, speed)  # Use at least 15 or the horse's speed as max
                                st.write(f"⚡ Speed: {speed:.1f}")
                                st.progress(min(speed / max_speed, 1.0))
                                if speed > 10:
                                    st.caption("🌟 Elite Level!")
                            with col_stamina:
                                # Adjust scale for horses with stats above 10  
                                max_stamina = max(15, stamina)  # Use at least 15 or the horse's stamina as max
                                st.write(f"💪 Stamina: {stamina:.1f}")
                                st.progress(min(stamina / max_stamina, 1.0))
                                if stamina > 10:
                                    st.caption("🌟 Elite Level!")
                            # Racing record
                            wins = stats.get('wins', 0)
                            races = stats.get('races', 0)
                            win_pct = (wins / max(races, 1)) * 100 if races > 0 else 0
                            if races > 0:
                                st.write(f"**🏆 Racing Record:** {wins}-{races-wins}-0 ({win_pct:.1f}% wins)")
                                # Performance badge
                                if races >= 5 and win_pct >= 60:
                                    st.success("🌟 **Elite Performer**")
                                elif races >= 3 and win_pct >= 40:
                                    st.info("⭐ **Proven Winner**")
                                elif races > 0:
                                    st.warning("� **Developing Talent**")
                            else:
                                st.write("**🆕 Rookie** - Ready for first race!")
                                st.info("🎯 No racing experience yet")
                            # Certification status
                            certs = stats.get('certifications', {})
                            if certs:
                                completed_certs = sum(certs.values())
                                total_certs = len(certs)
                                cert_percentage = (completed_certs / total_certs * 100) if total_certs > 0 else 0
                                if cert_percentage == 100:
                                    st.success("✅ **Fully Certified** - Race Ready!")
                                elif cert_percentage >= 60:
                                    st.warning(f"⚠️ **{cert_percentage:.0f}% Certified** - Missing some permits")
                                else:
                                    st.error("❌ **Not Race Eligible** - Needs certifications")
                            else:
                                st.error("📋 **No Certifications** - Visit Certification section")
                            # Quick action buttons
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button(f"🏁 Race {name}", key=f"quick_race_{name}"):
                                    st.info("Go to Racing tab to enter races!")
                            with col_btn2:
                                if st.button(f"✏️ Rename {name}", key=f"quick_rename_{name}"):
                                    st.info("Use 'Change Horse Names' section below!")
                            st.markdown("---")
            st.markdown("---")
                        
    else:
        # Empty stable - encouraging message
        st.markdown("### 🏗️ **Welcome to Your Empty Stable!**")
        st.info("🐎 Your stable is ready for horses! Purchase your first racing champion below.")
        
        # Show sample horses to encourage purchase
        st.markdown("#### 🌟 **Available Horse Breeds:**")
        col_breed1, col_breed2, col_breed3 = st.columns(3)
        
        breed_samples = list(HORSE_BREEDS.items())[:3]
        for i, (breed_name, breed_info) in enumerate(breed_samples):
            with [col_breed1, col_breed2, col_breed3][i]:
                st.write(f"**{breed_name}**")
                st.write(f"💰 ${breed_info['base_price']}")
                st.write(f"⚡ Speed: {breed_info['speed_range'][0]}-{breed_info['speed_range'][1]}")
                st.write(f"💪 Stamina: {breed_info['stamina_range'][0]}-{breed_info['stamina_range'][1]}")
        
        st.markdown("👇 **Purchase your first horse in the 'Buy New Horse' section below!**")
    
    # Jockey Management Section
    with st.expander("🏇 Jockey Contracts & Management", expanded=False):
        st.markdown("### Available Jockeys for Hire")
        
        jockey_contracts = get_jockey_contracts()
        
        # Show available jockeys
        cols = st.columns(2)
        for i, jockey in enumerate(AVAILABLE_JOCKEYS):
            with cols[i % 2]:
                st.markdown(f"**{jockey['name']}** - {jockey['specialty']}")
                st.write(f"💪 Skill: {jockey['skill']}/10 | 🎯 Win Rate: {jockey['win_rate']*100:.1f}%")
                st.write(f"💼 Wants: {jockey['preferred_percentage']}% (Min: {jockey['minimum_percentage']}%)")
                st.caption(jockey['bio'])
                
                # Contract management
                if jockey['name'] in jockey_contracts:
                    contract = jockey_contracts[jockey['name']]
                    st.success(f"✅ **CONTRACTED** - {contract['percentage']}% of prize purse")
                    st.write(f"🐎 Assigned to: {contract.get('assigned_horse', 'Available')}")
                    if st.button(f"Release {jockey['name']}", key=f"release_{jockey['name']}"):
                        del jockey_contracts[jockey['name']]
                        st.session_state.jockey_contracts = jockey_contracts
                        st.success(f"{jockey['name']} released from contract!")
                        st.rerun()
                else:
                    percentage = st.slider(
                        f"Offer % of prize purse to {jockey['name']}", 
                        jockey['minimum_percentage'], 
                        20, 
                        jockey['preferred_percentage'],
                        key=f"slider_{jockey['name']}"
                    )
                    
                    if st.button(f"Hire {jockey['name']}", key=f"hire_{jockey['name']}"):
                        if percentage >= jockey['minimum_percentage']:
                            from datetime import datetime as dt
                            jockey_contracts[jockey['name']] = {
                                'percentage': percentage,
                                'hired_date': dt.now().strftime('%Y-%m-%d'),
                                'races_won': 0,
                                'total_earnings': 0,
                                'assigned_horse': None
                            }
                            st.session_state.jockey_contracts = jockey_contracts
                            st.success(f"🤝 {jockey['name']} hired at {percentage}% of prize purse!")
                            st.rerun()
                        else:
                            st.error(f"{jockey['name']} won't accept less than {jockey['minimum_percentage']}%")
                
                st.markdown("---")
        
        # Horse-Jockey Assignment
        if jockey_contracts and horses:
            st.markdown("### 🐎 Horse-Jockey Assignments")
            
            horse_assignments = {}
            for horse_name in horses.keys():
                # Find current assignment
                current_jockey = None
                for jockey_name, contract in jockey_contracts.items():
                    if contract.get('assigned_horse') == horse_name:
                        current_jockey = jockey_name
                        break
                
                available_jockeys = ['Unassigned'] + [j for j in jockey_contracts.keys()]
                current_index = 0
                if current_jockey:
                    current_index = available_jockeys.index(current_jockey)
                
                selected = st.selectbox(
                    f"Jockey for {horse_name}:",
                    available_jockeys,
                    index=current_index,
                    key=f"assign_{horse_name}"
                )
                
                if selected != 'Unassigned' and selected != current_jockey:
                    # Clear previous assignment
                    for jockey_name, contract in jockey_contracts.items():
                        if contract.get('assigned_horse') == horse_name:
                            contract['assigned_horse'] = None
                    
                    # Set new assignment
                    jockey_contracts[selected]['assigned_horse'] = horse_name
                    st.session_state.jockey_contracts = jockey_contracts
                elif selected == 'Unassigned' and current_jockey:
                    jockey_contracts[current_jockey]['assigned_horse'] = None
                    st.session_state.jockey_contracts = jockey_contracts
    
    # Race Accounting Section
    with st.expander("📊 Race Accounting & Earnings History", expanded=False):
        accounting = get_race_accounting()
        
        if accounting:
            st.markdown("### Recent Race Transactions")
            
            # Summary stats
            total_gross = sum(t['gross_prize'] for t in accounting)
            total_jockey_payments = sum(t['jockey_payment'] for t in accounting)
            total_net = sum(t['net_earnings'] for t in accounting)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Gross Prize", f"${total_gross:,.2f}")
            with col2:
                st.metric("Total Jockey Payments", f"${total_jockey_payments:,.2f}")
            with col3:
                st.metric("Total Net Earnings", f"${total_net:,.2f}")
            
            # Recent transactions
            st.markdown("### Transaction History")
            for transaction in accounting[-10:]:  # Show last 10
                st.write(f"**{transaction['date']}** - {transaction['horse']} (Jockey: {transaction['jockey']})")
                st.write(f"   Prize: ${transaction['gross_prize']:,.2f} → Jockey ({transaction['jockey_percentage']}%): ${transaction['jockey_payment']:.2f} → Net: ${transaction['net_earnings']:.2f}")
        else:
            st.info("No race transactions yet. Enter a race to start tracking earnings!")
    
    # ========== STABLE MANAGEMENT SECTIONS ==========
    st.markdown("## 🛠️ **Stable Management**")
    
    # Quick Actions Row
    col_quick1, col_quick2, col_quick3, col_quick4 = st.columns(4)
    with col_quick1:
        if st.button("🛒 Buy Horse", width="stretch"):
            st.info("👇 Use 'Buy New Horse' section below")
    with col_quick2:
        if st.button("💪 Train Horse", width="stretch"):
            st.info("👇 Use 'Train Horse' section below")
    with col_quick3:
        if st.button("📋 Get Certifications", width="stretch"):
            st.info("👇 Use 'Certification' section below")
    with col_quick4:
        if st.button("🏇 Manage Jockeys", width="stretch"):
            st.info("👇 Use 'Jockey Management' section below")
    
    st.markdown("---")
    
    # ========== PRIMARY HORSE MANAGEMENT ==========
    
    # 1. BUY NEW HORSE - Most important for new users
    st.markdown("### 🛒 **Purchase Racing Horses**")
    
    col_breed_info, col_breed_select = st.columns([2, 1])
    
    with col_breed_info:
        st.write("**🐎 Available Breeds & Their Characteristics:**")
        
        # Show breed comparison in a nice table format
        breed_data = []
        for breed_name, breed_info in list(HORSE_BREEDS.items())[:3]:  # Show first 3
            breed_data.append({
                "Breed": breed_name,
                "Price": f"${breed_info['base_price']:,}",
                "Speed Range": f"{breed_info['speed_range'][0]}-{breed_info['speed_range'][1]}",
                "Stamina Range": f"{breed_info['stamina_range'][0]}-{breed_info['stamina_range'][1]}"
            })
        
        import pandas as pd
        df = pd.DataFrame(breed_data)
        st.dataframe(df, width="stretch", hide_index=True)
        
        if len(HORSE_BREEDS) > 3:
            with st.expander("📋 View All Available Breeds"):
                all_breed_data = []
                for breed_name, breed_info in HORSE_BREEDS.items():
                    all_breed_data.append({
                        "Breed": breed_name,
                        "Price": f"${breed_info['base_price']:,}",
                        "Speed": f"{breed_info['speed_range'][0]:.1f}-{breed_info['speed_range'][1]:.1f}",
                        "Stamina": f"{breed_info['stamina_range'][0]:.1f}-{breed_info['stamina_range'][1]:.1f}",
                        "Training Cost": f"${breed_info['training_cost']}"
                    })
                df_all = pd.DataFrame(all_breed_data)
                st.dataframe(df_all, width="stretch", hide_index=True)
    
    with col_breed_select:
        st.write("**🏇 Purchase Your Horse:**")
        breed = st.selectbox("Choose a breed", list(HORSE_BREEDS.keys()), key="buy_horse_breed")
        price = HORSE_BREEDS[breed]["base_price"]
        
        st.write(f"**💰 Price:** ${price:,}")
        st.write(f"**⚡ Speed:** {HORSE_BREEDS[breed]['speed_range'][0]:.1f}-{HORSE_BREEDS[breed]['speed_range'][1]:.1f}")
        st.write(f"**💪 Stamina:** {HORSE_BREEDS[breed]['stamina_range'][0]:.1f}-{HORSE_BREEDS[breed]['stamina_range'][1]:.1f}")
        
        if st.session_state.money >= price:
            if st.button(f"🛒 Buy {breed}", type="primary", width="stretch"):
                name = generate_fun_horse_name()
                # Make sure name is unique in stable
                counter = 1
                original_name = name
                while name in horses:
                    name = f"{original_name} {counter}"
                    counter += 1
                
                stats = {
                    "breed": breed,
                    "speed": round(random.uniform(*HORSE_BREEDS[breed]["speed_range"]), 2),
                    "stamina": round(random.uniform(*HORSE_BREEDS[breed]["stamina_range"]), 2),
                    "level": 1,
                    "training_count": 0,
                    "health": 100,
                    "wins": 0,
                    "races": 0,
                    "birthdate": "2023-01-01 12:00:00",
                    "certifications": {  # Initialize with no certifications
                        'health_certificate': False,
                        'racing_license': False,
                        'bloodline_registration': False,
                        'performance_permit': False,
                        'insurance_coverage': False
                    },
                    "certification_expiry": {}
                }
                horses[name] = stats
                st.session_state.stable_horses = horses
                st.session_state.money -= price
                # Save money to Firebase
                if "user_id" in st.session_state:
                    save_user_money(st.session_state.user_id, st.session_state.money)
                st.success(f"🎉 Welcome {name} to Gold Creek Stables!")
                st.balloons()
                save_horse_data(st.session_state.get('user_id', 'default_user'), horses)
                st.rerun()
        else:
            st.error(f"💸 Need ${price - st.session_state.money:,} more")
            st.button("💸 Insufficient Funds", disabled=True, width="stretch")
    
    st.markdown("---")
    
    # 2. HORSE NAME CHANGING - SECOND PRIORITY
    with st.expander("✏️ Change Horse Names"):
        if horses:
            st.write("🐴 **Rename Your Horses**")
            st.write("Give your horses new names that better reflect their personality or achievements!")
            
            # Select horse to rename
            horse_names = list(horses.keys())
            selected_horse = st.selectbox("Choose a horse to rename:", horse_names, key="rename_horse_select")
            
            # Always define rename_option before any conditional usage
            rename_option = st.session_state.get("rename_option", "✍️ Enter Custom Name")
            
            if selected_horse:
                current_stats = horses[selected_horse]
                
                # Display current horse info
                col_info, col_rename = st.columns([2, 3])
                
                with col_info:
                    st.write(f"**Current Horse:** {selected_horse}")
                    st.write(f"**Breed:** {current_stats['breed']}")
                    st.write(f"**Speed:** {current_stats['speed']}")
                    st.write(f"**Stamina:** {current_stats['stamina']}")
                    wins = current_stats.get('wins', 0)
                    races = current_stats.get('races', 0)
                    if races > 0:
                        st.write(f"**Record:** {wins}-{races-wins}-0")
                
                with col_rename:
                    st.write("**🎨 Choose New Name:**")
                    
                    # Name input options
                    rename_option = st.radio("Choose how to rename:", 
                                           ["✍️ Enter Custom Name", "🎲 Generate Fun Name", "🎯 Generate Serious Name"], 
                                           key="rename_option")
                    
                    new_name = ""
                    
                    if rename_option == "✍️ Enter Custom Name":
                        new_name = st.text_input("Enter new name:", value="", key="custom_horse_name")
                        
                    elif rename_option == "🎲 Generate Fun Name":
                        if st.button("🎪 Generate Fun Name", key="gen_fun_name"):
                            new_name = generate_fun_horse_name()
                            st.session_state.suggested_name = new_name
                        
                        if 'suggested_name' in st.session_state:
                            new_name = st.text_input("Generated fun name:", value=st.session_state.suggested_name, key="fun_name_input")
                            
                    elif rename_option == "🎯 Generate Serious Name":
                        if st.button("🏆 Generate Serious Name", key="gen_serious_name"):
                            # Generate a more traditional racing name
                            prefix = random.choice(HORSE_PREFIXES)
                            first = random.choice(HORSE_FIRST_NAMES)
                            last = random.choice(HORSE_LAST_NAMES)
                            new_name = f"{prefix} {first} {last}"
                            st.session_state.suggested_serious_name = new_name
                        
                        if 'suggested_serious_name' in st.session_state:
                            new_name = st.text_input("Generated serious name:", value=st.session_state.suggested_serious_name, key="serious_name_input")
                    
                    # Rename button and validation
                    if new_name and new_name.strip():
                        new_name = new_name.strip()
                        
                        # Get user's stable horses (ensure we're only checking user's horses)
                        user_horses = st.session_state.get("stable_horses", {})
                        user_horse_names = list(user_horses.keys())
                        
                        # Debug info (remove in production)
                        if st.checkbox("🔍 Show debug info", key="debug_rename"):
                            st.write(f"**Debug:** Your horses: {user_horse_names}")
                            st.write(f"**Debug:** Selected horse: '{selected_horse}'")
                            st.write(f"**Debug:** New name: '{new_name}'")
                            st.write(f"**Debug:** Name in horses: {new_name in user_horses}")
                        

                    # Bulk purchase UI (moved to correct location)
                    st.markdown("---")
                    st.write("**🛒 Bulk Stable Purchase:**")
                    max_bulk = min(100, st.session_state.money // price) if price > 0 else 0
                    bulk_count = st.number_input(
                        "Number of horses to buy",
                        min_value=1,
                        max_value=max_bulk if max_bulk > 0 else 1,
                        value=1,
                        step=1,
                        key=f"bulk_horse_count_{breed}"
                    )
                    total_bulk_price = bulk_count * price
                    st.write(f"**Total Price:** ${total_bulk_price:,}")
                    if st.session_state.money >= total_bulk_price:
                        if st.button(f"🛒 Buy {bulk_count} {breed}(s)", type="primary", key="bulk_buy_btn"):
                            for i in range(bulk_count):
                                name = generate_fun_horse_name()
                                counter = 1
                                original_name = name
                                while name in horses:
                                    name = f"{original_name} {counter}"
                                    counter += 1
                                stats = {
                                    "breed": breed,
                                    "speed": round(random.uniform(*HORSE_BREEDS[breed]["speed_range"]), 2),
                                    "stamina": round(random.uniform(*HORSE_BREEDS[breed]["stamina_range"]), 2),
                                    "level": 1,
                                    "training_count": 0,
                                    "health": 100,
                                    "wins": 0,
                                    "races": 0,
                                    "birthdate": "2023-01-01 12:00:00",
                                    "certifications": {
                                        'health_certificate': False,
                                        'racing_license': False,
                                        'bloodline_registration': False,
                                        'performance_permit': False,
                                        'insurance_coverage': False
                                    },
                                    "certification_expiry": {}
                                }
                                horses[name] = stats
                            st.session_state.stable_horses = horses
                            st.session_state.money -= total_bulk_price
                            if "user_id" in st.session_state:
                                save_user_money(st.session_state.user_id, st.session_state.money)
                            save_horse_data(st.session_state.get('user_id', 'default_user'), horses)
                            st.success(f"🎉 Added {bulk_count} {breed}(s) to your stable!")
                            st.balloons()
                            st.rerun()
                    else:
                        st.warning("Not enough money for bulk purchase.")

                        # Check if name already exists in user's stable
                        if new_name in user_horse_names and new_name != selected_horse:
                            st.error(f"❌ Name '{new_name}' is already used by one of your horses!")
                            st.info("💡 Choose a different name - each of your horses needs a unique name.")
                        elif new_name == selected_horse:
                            st.info("💡 That's the same name. Choose a different name to rename.")
                        elif len(new_name) > 50:
                            st.error("❌ Name is too long! Please keep it under 50 characters.")
                        elif len(new_name) < 2:
                            st.error("❌ Name is too short! Please use at least 2 characters.")
                        else:
                            # Show rename button
                            rename_cost = 50  # Small cost for renaming
                            st.write(f"💰 **Renaming Cost:** ${rename_cost}")
                            st.success(f"✅ '{new_name}' is available!")
                            
                            if st.session_state.money >= rename_cost:
                                if st.button(f"✅ Rename to '{new_name}' (${rename_cost})", key="confirm_rename"):
                                    # Perform the rename
                                    horses[new_name] = horses.pop(selected_horse)
                                    st.session_state.money -= rename_cost
                                    
                                    # Save data to Firebase
                                    if "user_id" in st.session_state:
                                        save_horse_data(st.session_state.user_id, horses)
                                        save_user_money(st.session_state.user_id, st.session_state.money)
                                    
                                    # Clear suggestions
                                    if 'suggested_name' in st.session_state:
                                        del st.session_state.suggested_name
                                    if 'suggested_serious_name' in st.session_state:
                                        del st.session_state.suggested_serious_name
                                    
                                    st.success(f"🎉 Successfully renamed '{selected_horse}' to '{new_name}'!")
                                    st.balloons()
                                    st.rerun()
                            else:
                                st.error(f"❌ Not enough money! You need ${rename_cost} but only have ${st.session_state.money:.2f}")
                    
    #                elif rename_option == "✍️ Enter Custom Name" and not new_name:
                        st.info("💡 Enter a new name above to rename your horse.")
        else:
            st.info("🐎 You need to own horses before you can rename them. Buy some horses first!")
    # Global Recognition section
    with st.expander("🌟 Your Horses in Global Hall of Fame"):
        try:
            from firebase_utils import load_global_horse_history
            global_history = load_global_horse_history()
            
            if global_history is not None and isinstance(global_history, dict):
                # Find your horses in global history
                user_id = st.session_state.get('user_id', '')
                your_famous_horses = {}
                
                for horse_name, record in global_history.items():
                    if isinstance(record, dict) and record.get('owner_id') == user_id and record.get('total_races', 0) >= 3:
                        your_famous_horses[horse_name] = record
                
                if your_famous_horses:
                    st.success(f"🎉 You have {len(your_famous_horses)} horses in the Global Hall of Fame!")
                    
                    for horse_name, record in your_famous_horses.items():
                        wins = record.get('total_wins', 0)
                        races = record.get('total_races', 0) 
                        earnings = record.get('total_earnings', 0)
                        highlights = record.get('career_highlights', [])
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(f"🐎 {horse_name}", f"{wins} wins", f"{races} races")
                        with col2:
                            st.metric("Global Earnings", f"${earnings:,}")
                        with col3:
                            if highlights:
                                st.success(f"🏆 {', '.join(highlights)}")
                            else:
                                st.info("Building reputation...")
                else:
                    st.info("🎯 Race your horses 3+ times to appear in the Global Hall of Fame!")
            else:
                st.info("🏁 Global racing records not available yet.")
        except Exception as e:
            st.warning("Unable to load global racing data.")

    with st.expander("🛒 Buy New Horse"):
        breed = st.selectbox("Choose a breed", list(HORSE_BREEDS.keys()))
        price = HORSE_BREEDS[breed]["base_price"]
        if st.button(f"Buy {breed} for ${price}"):
            if st.session_state.money >= price:
                name = generate_fun_horse_name()
                # Make sure name is unique in stable
                counter = 1
                original_name = name
                while name in horses:
                    name = f"{original_name} {counter}"
                    counter += 1
                
                from datetime import datetime as dt
                stats = {
                    "breed": breed,
                    "speed": round(random.uniform(*HORSE_BREEDS[breed]["speed_range"]), 2),
                    "stamina": round(random.uniform(*HORSE_BREEDS[breed]["stamina_range"]), 2),
                    "level": 1,
                    "training_count": 0,
                    "health": 100,
                    "wins": 0,
                    "races": 0,
                    "birthdate": str(dt.now())
                }
                horses[name] = stats
                st.session_state.stable_horses = horses
                st.session_state.money -= price
                # Save money to Firebase
                if "user_id" in st.session_state:
                    save_user_money(st.session_state.user_id, st.session_state.money)
                st.success(f"You bought {name} the {breed}!")
                save_horse_data(st.session_state.get('user_id', 'default_user'), horses)
            else:
                st.error("Not enough money to buy this horse.")

    # Horse Certification & Licensing System
    with st.expander("📋 Horse Certification & Racing Permits"):
        st.write("### 🏛️ Official Racing Commission Certifications")
        st.write("All horses must be properly certified before they can compete in official races!")
        
        if horses:
            # Initialize certification status for existing horses
            for horse_name, stats in horses.items():
                if 'certifications' not in stats:
                    stats['certifications'] = {
                        'health_certificate': False,
                        'racing_license': False,
                        'bloodline_registration': False,
                        'performance_permit': False,
                        'insurance_coverage': False
                    }
                    stats['certification_expiry'] = {}
            
            # Display certification status
            st.write("#### 📊 Current Certification Status")
            
            for horse_name, stats in horses.items():
                with st.container():
                    st.write(f"**🐎 {horse_name}** ({stats['breed']})")
                    
                    # Check overall certification status
                    certs = stats.get('certifications', {})
                    total_certs = len(certs)
                    completed_certs = sum(certs.values())
                    cert_percentage = (completed_certs / total_certs * 100) if total_certs > 0 else 0
                    
                    col_status, col_progress = st.columns([2, 3])
                    
                    with col_status:
                        if cert_percentage == 100:
                            st.success("✅ **FULLY CERTIFIED** - Ready to Race!")
                        elif cert_percentage >= 60:
                            st.warning(f"⚠️ **PARTIALLY CERTIFIED** ({cert_percentage:.0f}%)")
                        else:
                            st.error("❌ **NOT RACE ELIGIBLE** - Missing Certifications")
                    
                    with col_progress:
                        st.progress(cert_percentage / 100)
                        st.caption(f"{completed_certs}/{total_certs} certifications complete")
                    
                    # Detailed certification breakdown
                    cert_details = {
                        'health_certificate': {
                            'name': '🩺 Health Certificate',
                            'cost': 75,
                            'description': 'Veterinary health clearance and vaccination records'
                        },
                        'racing_license': {
                            'name': '🏆 Racing License', 
                            'cost': 150,
                            'description': 'Official permit to compete in sanctioned races'
                        },
                        'bloodline_registration': {
                            'name': '📜 Bloodline Registration',
                            'cost': 100, 
                            'description': 'Certified pedigree and breed documentation'
                        },
                        'performance_permit': {
                            'name': '⚡ Performance Permit',
                            'cost': 125,
                            'description': 'Speed and stamina testing certification'
                        },
                        'insurance_coverage': {
                            'name': '🛡️ Racing Insurance',
                            'cost': 200,
                            'description': 'Comprehensive coverage for racing injuries'
                        }
                    }
                    
                    # Show missing certifications with purchase options
                    missing_certs = [cert_id for cert_id, status in certs.items() if not status]
                    
                    if missing_certs:
                        st.write("**📋 Missing Certifications:**")
                        
                        for cert_id in missing_certs:
                            cert_info = cert_details[cert_id]
                            col_cert, col_action = st.columns([3, 1])
                            
                            with col_cert:
                                st.write(f"• {cert_info['name']} - ${cert_info['cost']}")
                                st.caption(f"   {cert_info['description']}")
                            
                            with col_action:
                                button_key = f"get_cert_{horse_name}_{cert_id}"
                                if st.session_state.money >= cert_info['cost']:
                                    if st.button("📋 Get", key=button_key):
                                        # Purchase certification
                                        st.session_state.money -= cert_info['cost']
                                        horses[horse_name]['certifications'][cert_id] = True
                                        
                                        # Set expiry date (1 year from now)
                                        from datetime import datetime, timedelta
                                        expiry_date = datetime.now() + timedelta(days=365)
                                        
                                        # Ensure certification_expiry field exists
                                        if 'certification_expiry' not in horses[horse_name]:
                                            horses[horse_name]['certification_expiry'] = {}
                                        horses[horse_name]['certification_expiry'][cert_id] = expiry_date.isoformat()
                                        
                                        # Save data
                                        if "user_id" in st.session_state:
                                            save_horse_data(st.session_state.user_id, horses)
                                            save_user_money(st.session_state.user_id, st.session_state.money)
                                        
                                        st.success(f"✅ {cert_info['name']} acquired for {horse_name}!")
                                        st.balloons()
                                        st.rerun()
                                else:
                                    st.button("💸 Need $", key=button_key, disabled=True)
                        
                        # Quick certification package
                        total_missing_cost = sum(cert_details[cert_id]['cost'] for cert_id in missing_certs)
                        if len(missing_certs) > 1:
                            st.write("---")
                            package_discount = int(total_missing_cost * 0.15)  # 15% discount
                            package_cost = total_missing_cost - package_discount
                            
                            col_package, col_buy = st.columns([3, 1])
                            with col_package:
                                st.write(f"🎁 **Complete Certification Package**")
                                st.write(f"   Regular Price: ${total_missing_cost}")
                                st.write(f"   Package Price: ${package_cost} (Save ${package_discount}!)")
                            
                            with col_buy:
                                if st.session_state.money >= package_cost:
                                    if st.button("🎁 Buy All", key=f"package_{horse_name}"):
                                        # Purchase all missing certifications
                                        st.session_state.money -= package_cost
                                        from datetime import datetime, timedelta
                                        expiry_date = datetime.now() + timedelta(days=365)
                                        
                                        # Ensure certification_expiry field exists
                                        if 'certification_expiry' not in horses[horse_name]:
                                            horses[horse_name]['certification_expiry'] = {}
                                        
                                        for cert_id in missing_certs:
                                            horses[horse_name]['certifications'][cert_id] = True
                                            horses[horse_name]['certification_expiry'][cert_id] = expiry_date.isoformat()
                                        
                                        # Save data
                                        if "user_id" in st.session_state:
                                            save_horse_data(st.session_state.user_id, horses)
                                            save_user_money(st.session_state.user_id, st.session_state.money)
                                        
                                        st.success(f"🎉 Complete certification package acquired for {horse_name}!")
                                        st.balloons()
                                        st.rerun()
                                else:
                                    st.button("💸 Need $", key=f"package_need_{horse_name}", disabled=True)
                    
                    st.write("---")
            
            # Certification renewal system
            st.write("#### 🔄 Certification Renewal")
            st.write("💡 All certifications expire after 1 year and must be renewed to maintain racing eligibility.")
            
            # Check for expiring certifications
            from datetime import datetime, timedelta
            now = datetime.now()
            soon = now + timedelta(days=30)  # 30 days warning
            
            expiring_soon = []
            expired = []
            
            for horse_name, stats in horses.items():
                for cert_id, status in stats.get('certifications', {}).items():
                    if status and cert_id in stats.get('certification_expiry', {}):
                        expiry_str = stats['certification_expiry'][cert_id]
                        expiry_date = datetime.fromisoformat(expiry_str)
                        
                        if expiry_date < now:
                            expired.append((horse_name, cert_id))
                            # Auto-expire the certification
                            horses[horse_name]['certifications'][cert_id] = False
                        elif expiry_date < soon:
                            expiring_soon.append((horse_name, cert_id, expiry_date))
            
            if expired:
                st.error("⚠️ **EXPIRED CERTIFICATIONS** - These horses are no longer race eligible:")
                for horse_name, cert_id in expired:
                    cert_name = cert_details[cert_id]['name']
                    st.write(f"• {horse_name}: {cert_name}")
            
            if expiring_soon:
                st.warning("🔔 **CERTIFICATIONS EXPIRING SOON:**")
                for horse_name, cert_id, expiry_date in expiring_soon:
                    cert_name = cert_details[cert_id]['name']
                    days_left = (expiry_date - now).days
                    st.write(f"• {horse_name}: {cert_name} expires in {days_left} days")
        
        else:
            st.info("🐎 Purchase horses first to manage their certifications and racing permits!")

    with st.expander("💪 Train Horse"):
        if horses:
            selected = st.selectbox("Choose horse to train", list(horses.keys()))
            mode = st.radio("Training focus", ["Speed", "Stamina", "Balanced"])
            cost = HORSE_BREEDS[horses[selected]["breed"]]["training_cost"]

            if st.button(f"Train {selected} (${cost})"):
                if st.session_state.money >= cost:
                    if mode == "Speed":
                        horses[selected]["speed"] += round(random.uniform(0.1, 0.4), 2)
                    elif mode == "Stamina":
                        horses[selected]["stamina"] += round(random.uniform(0.1, 0.4), 2)
                    else:
                        horses[selected]["speed"] += round(random.uniform(0.05, 0.2), 2)
                        horses[selected]["stamina"] += round(random.uniform(0.05, 0.2), 2)

                    horses[selected]["training_count"] += 1
                    st.session_state.stable_horses = horses
                    st.session_state.money -= cost
                    # Save money to Firebase
                    if "user_id" in st.session_state:
                        save_user_money(st.session_state.user_id, st.session_state.money)
                    st.success(f"{selected} trained! Stats improved.")
                    save_horse_data(st.session_state.get('user_id', 'default_user'), horses)
                else:
                    st.error("Not enough money for training.")
        else:
            st.info("Buy a horse first!")

    with st.expander("🐣 Breed Horses (Unlocks at 5 horses)"):
        if len(horses) < 5:
            st.warning("You need at least 5 horses to unlock breeding.")
        else:
            parent1 = st.selectbox("Select Parent 1", list(horses.keys()), key="breed1")
            parent2 = st.selectbox("Select Parent 2", list(horses.keys()), key="breed2")
            if parent1 == parent2:
                st.error("Choose two different parents.")
            else:
                if st.button("Breed Now ($100)"):
                    if st.session_state.money >= 100:
                        child_name = generate_fun_horse_name()
                        # Make sure name is unique in stable
                        counter = 1
                        original_name = child_name
                        while child_name in horses:
                            child_name = f"{original_name} {counter}"
                            counter += 1
                        
                        speed = round((horses[parent1]['speed'] + horses[parent2]['speed']) / 2 + random.uniform(-0.3, 0.3), 2)
                        stamina = round((horses[parent1]['stamina'] + horses[parent2]['stamina']) / 2 + random.uniform(-0.3, 0.3), 2)
                        breed = horses[parent1]['breed']
                        horses[child_name] = {
                            "breed": "Mixed",
                            "speed": max(speed, 3.0),
                            "stamina": max(stamina, 3.0),
                            "level": 1,
                            "training_count": 0,
                            "health": 100,
                            "wins": 0,
                            "races": 0
                        }
                        st.session_state.stable_horses = horses
                        st.session_state.money -= 100
                        # Save money to Firebase
                        if "user_id" in st.session_state:
                            save_user_money(st.session_state.user_id, st.session_state.money)
                        st.success(f"New foal born: {child_name}!")
                        save_horse_data(st.session_state.get('user_id', 'default_user'), horses)
                    else:
                        st.error("Not enough money to breed.")