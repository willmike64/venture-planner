# jockeys.py placeholder - replace with actual file if missing
import streamlit    # Safely extract stats with fallbacks
    speed = stats.get('speed', 5.0)
    stamina = stats.get('stamina', 5.0)
    breed = stats.get('breed', 'Mixed Breed')
    temperament = stats.get('temperament', 'calm')
    health = stats.get('health', 100)
    
    prompt = f"""
    You are {jockey_name}, a witty and skilled horse jockey from the Old West.
    The horse you are riding is named {horse_name}.
    Here are their stats:
    - Speed: {speed:.1f}/10
    - Stamina: {stamina:.1f}/10
    - Breed: {breed}
    - Temperament: {temperament}
    - Health: {health}%

    Give some smart, funny, and strategic commentary about how you'll train, race, or bond with {horse_name}.
    Make it sound like YOU (the jockey) are talking directly to the player.
    Keep it under 3 sentences and make it entertaining!
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a colorful and strategic horse jockey from the Wild West."},
                {"role": "user", "content": prompt}
            ]
        )
        content = completion.choices[0].message.content
        return content.strip() if content else f"{jockey_name} tips their hat silently."
    except Exception as e:
        # Fallback responses if OpenAI fails
        fallback_responses = [
            f"Well partner, {horse_name} and I got a good thing goin'. With that {speed:.1f} speed, we'll show 'em what real ridin' looks like!",
            f"{horse_name}'s got the heart of a champion and the spirit of the frontier. That {stamina:.1f} stamina ain't gonna let us down when it counts!",
            f"I've been ridin' {breed}s all my life, and {horse_name} here is somethin' special. Trust me on this one, partner!",
            f"See that {temperament} look in {horse_name}'s eyes? That's the fire we need to win big! Yeehaw!",
            f"Me and {horse_name} been practicin' our moves. With {health}% health, we're ready to take on any challenge!"
        ]
        return random.choice(fallback_responses)re
import random
import openai # type: ignore

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

JOCKEY_POOL = [
    "Lightning Lou",
    "Sassy Sadie",
    "Whiskey Jack",
    "Moonshine Molly",
    "Sheriff Stirrup",
    "Dusty Dan",
    "Crazy Colt Carter"
]

def get_available_jockey(horse_name):
    if "jockeys" not in st.session_state:
        st.session_state.jockeys = {}

    if horse_name not in st.session_state.jockeys:
        st.session_state.jockeys[horse_name] = random.choice(JOCKEY_POOL)

    return st.session_state.jockeys[horse_name]

def render_jockey_management():
    st.header("👨‍🌾 Jockey Assignments & Banter")
    
    # Handle both old (dict) and new (list) horse data structures
    horses_data = st.session_state.get("horses", {})
    owned_horses = st.session_state.get("owned_horses", [])
    
    # Convert different data structures to a consistent format
    if isinstance(horses_data, list):
        # New format: list of horse dictionaries
        horses = {}
        for horse in horses_data:
            if horse.get('name'):
                horses[horse['name']] = {
                    'speed': horse.get('base_speed', horse.get('speed', 5.0)),
                    'stamina': horse.get('endurance', horse.get('stamina', 5.0)),
                    'breed': horse.get('breed', 'Mixed Breed'),
                    'temperament': horse.get('temperament', 'calm')
                }
    elif isinstance(horses_data, dict) and horses_data:
        # Old format: dictionary of horses
        horses = horses_data
    else:
        # Use owned_horses if available
        horses = {}
        for horse in owned_horses:
            horses[horse['name']] = {
                'speed': horse.get('speed', 5.0),
                'stamina': horse.get('stamina', 5.0),
                'breed': horse.get('breed', 'Mixed Breed'),
                'health': horse.get('health', 100)
            }

    if not horses:
        st.info("You need to own horses before jockeys can be assigned.")
        if owned_horses:
            st.info("💡 Visit the Horse Stable to buy some horses first!")
        return

    st.markdown("### Assigned Jockeys:")
    for horse_name, horse_stats in horses.items():
        jockey = get_available_jockey(horse_name)
        st.markdown(f"- **{horse_name}** ➝ *{jockey}*")
        if st.button(f"🧠 Ask {jockey} about {horse_name}", key=f"ask_{horse_name}"):
            response = ask_jockey_about_horse(jockey, horse_name, horse_stats)
            st.success(f"💬 {jockey} says:")
            st.markdown(response)

def ask_jockey_about_horse(jockey_name, horse_name, stats):
    prompt = f"""
    You are {jockey_name}, a witty and skilled horse jockey.
    The horse you are riding is named {horse_name}.
    Here are their stats:
    - Speed: {stats['speed']}
    - Stamina: {stats['stamina']}
    - Breed: {stats['breed']}

    Give some smart, funny, and strategic commentary about how you'll train, race, or bond with {horse_name}.
    Make it sound like YOU (the jockey) are talking directly to the player.
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a colorful and strategic horse jockey."},
                {"role": "user", "content": prompt}
            ]
        )
        content = completion.choices[0].message.content
        return content.strip() if content else f"{jockey_name} tips their hat silently."
    except Exception as e:
        return f"{jockey_name} squints into the distance. 'Well, reckon I’ll save my wisdom for the next race…' (Error: {e})"