# auction_house.py placeholder - replace with actual file if missing
import streamlit as st # type: ignore
from firebase_utils import save_user_data, get_user_data, save_user_money
from datetime import datetime

AUCTION_KEY = "auction_market"

def render_auction_house():
    # --- Ranches and Stables for Sale ---
    st.markdown("## 🏜️ Ranches & Successful Stables for Sale")
    from firebase_utils import get_db, serialize_data, deserialize_data
    ref = get_db()
    # Load global ranches and stables from Firebase
    default_ranches = [
        {
            "name": "Big Sky Ranch",
            "horses": 120,
            "thoroughbreds": 8,
            "price": 1200000,
            "owner": "Tex McGraw",
            "desc": "A sprawling ranch with 120 horses, only 8 are thoroughbreds. Includes barns, training tracks, and staff."
        },
        {
            "name": "Sunset Valley Ranch",
            "horses": 200,
            "thoroughbreds": 12,
            "price": 2200000,
            "owner": "Sally Star",
            "desc": "Premium ranch with 200 horses, 12 thoroughbreds, and a reputation for producing champions."
        }
    ]
    default_stables = [
        {
            "name": "Champion's Stable",
            "wins": 34,
            "horses": 15,
            "thoroughbreds": 6,
            "price": 950000,
            "owner": "Rick Races",
            "desc": "A successful stable with 34 wins, 15 horses, and 6 top-tier thoroughbreds."
        },
        {
            "name": "Legacy Stable",
            "wins": 21,
            "horses": 10,
            "thoroughbreds": 4,
            "price": 650000,
            "owner": "Maggie Miles",
            "desc": "Well-managed stable with a strong win record and quality horses."
        }
    ]
    if ref is not None:
        ranches_data = ref.child('global_ranches').get()
        ranches = deserialize_data(ranches_data) if ranches_data else default_ranches
        if not isinstance(ranches, list) or not ranches:
            ranches = default_ranches
        stables_data = ref.child('global_stables').get()
        stables = deserialize_data(stables_data) if stables_data else default_stables
        if not isinstance(stables, list) or not stables:
            stables = default_stables
    else:
        st.error("Could not connect to Firebase. Ranches and stables unavailable.")
        ranches = default_ranches
        stables = default_stables

    with st.expander("🏜️ Ranches for Sale"):
        for i, ranch in enumerate(ranches):
            if not isinstance(ranch, dict):
                continue
            st.markdown(f"### {ranch.get('name', 'Unknown Ranch')} — ${ranch.get('price', 'N/A'):,}")
            st.caption(f"Owner: {ranch.get('owner', 'N/A')} | Horses: {ranch.get('horses', 'N/A')} | Thoroughbreds: {ranch.get('thoroughbreds', 'N/A')}")
            st.write(ranch.get('desc', 'No description available.'))
            if st.button(f"Negotiate for {ranch.get('name', 'Unknown Ranch')}", key=f"negotiate_ranch_{i}"):
                price = ranch.get('price', 0)
                try:
                    if isinstance(price, (int, float, str)):
                        price_val = float(price)
                    else:
                        price_val = 0.0
                except Exception:
                    price_val = 0.0
                user_offer = st.number_input("Your Offer ($)", min_value=100000.0, value=price_val, step=10000.0, key=f"offer_ranch_{i}")
                if st.button("Submit Offer", key=f"submit_offer_ranch_{i}"):
                    # Accept offer if it meets or exceeds price
                    if user_offer >= price_val:
                        st.success(f"Offer accepted! {ranch.get('owner', 'N/A')} has agreed to sell {ranch.get('name', 'Unknown Ranch')} for ${user_offer:,}.")
                    else:
                        # OpenAI negotiation simulation for lower offers
                        import openai
                        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                        prompt = (
                            f"You are {ranch.get('owner', 'N/A')}, owner of {ranch.get('name', 'Unknown Ranch')}. The user offers ${user_offer:,} for your ranch. "
                            f"Your asking price is ${price:,}. Respond as a tough negotiator: do not accept the offer, but make a counter-offer or explain why you want more. Always negotiate and never accept less than your asking price unless the user increases their offer."
                        )
                        completion = client.chat.completions.create(
                            model="gpt-4",
                            messages=[{"role": "system", "content": "You are a ranch owner negotiating a sale."}, {"role": "user", "content": prompt}]
                        )
                        st.write(completion.choices[0].message.content)

    with st.expander("🏆 Successful Stables for Sale"):
        for i, stable in enumerate(stables):
            if not isinstance(stable, dict):
                continue
            st.markdown(f"### {stable.get('name', 'Unknown Stable')} — ${stable.get('price', 'N/A'):,}")
            st.caption(f"Owner: {stable.get('owner', 'N/A')} | Horses: {stable.get('horses', 'N/A')} | Thoroughbreds: {stable.get('thoroughbreds', 'N/A')} | Wins: {stable.get('wins', 'N/A')}")
            st.write(stable.get('desc', 'No description available.'))
            if st.button(f"Negotiate for {stable.get('name', 'Unknown Stable')}", key=f"negotiate_stable_{i}"):
                price = stable.get('price', 0)
                try:
                    if isinstance(price, (int, float, str)):
                        price_val = float(price)
                    else:
                        price_val = 0.0
                except Exception:
                    price_val = 0.0
                user_offer = st.number_input("Your Offer ($)", min_value=100000.0, value=price_val, step=10000.0, key=f"offer_stable_{i}")
                if st.button("Submit Offer", key=f"submit_offer_stable_{i}"):
                    # Accept offer if it meets or exceeds price
                    if user_offer >= price_val:
                        st.success(f"Offer accepted! {stable.get('owner', 'N/A')} has agreed to sell {stable.get('name', 'Unknown Stable')} for ${user_offer:,}.")
                    else:
                        # OpenAI negotiation simulation for lower offers
                        import openai
                        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                        prompt = (
                            f"You are {stable.get('owner', 'N/A')}, owner of {stable.get('name', 'Unknown Stable')}. The user offers ${user_offer:,} for your stable. "
                            f"Your asking price is ${price:,}. Respond as a tough negotiator: do not accept the offer, but make a counter-offer or explain why you want more. Always negotiate and never accept less than your asking price unless the user increases their offer."
                        )
                        completion = client.chat.completions.create(
                            model="gpt-4",
                            messages=[{"role": "system", "content": "You are a stable owner negotiating a sale."}, {"role": "user", "content": prompt}]
                        )
                        st.write(completion.choices[0].message.content)
    st.header("🏦 Horse Auction Marketplace")

    horses = st.session_state.get("stable_horses", {})
    # Load global market from Firebase
    from firebase_utils import get_db, serialize_data, deserialize_data, save_user_money
    ref = get_db()
    if ref is not None:
        market_data = ref.child('auction_market').get()
        market = deserialize_data(market_data) if market_data else []
        if not isinstance(market, list):
            market = []
    else:
        st.error("Could not connect to Firebase. Auction marketplace unavailable.")
        market = []

    # --- List Your Horse for Sale ---
    with st.expander("📤 List Horse for Sale"):
        if not horses:
            st.info("You have no horses to list.")
        else:
            horse = st.selectbox("Choose horse to list", list(horses.keys()))
            price = st.number_input("Set listing price", min_value=0, step=50)

            if st.button("List Horse"):
                listing = {
                    "seller": st.session_state.get("stable_name", "Anonymous Stable"),
                    "name": horse,
                    "price": price,
                    "details": horses[horse],
                    "time": str(datetime.now())
                }
                if not isinstance(market, list):
                    market = []
                market.append(listing)
                del horses[horse]
                st.success(f"{horse} listed for ${price}")
                if ref is not None:
                    ref.child('auction_market').set(serialize_data(market))
                else:
                    st.error("Could not save to Firebase. Listing not persisted globally.")
                st.session_state.stable_horses = horses

    # --- Buy from Marketplace ---
    with st.expander("🛒 Buy From Marketplace"):
        # Always reload market from Firebase for global visibility
        if ref is not None:
            market_data = ref.child('auction_market').get()
            market = deserialize_data(market_data) if market_data else []
            if not isinstance(market, list):
                market = []
            if not market:
                st.info("No horses listed yet.")
            else:
                for i, item in enumerate(market):
                    if not isinstance(item, dict):
                        continue
                    st.markdown(f"**{item['name']}** — ${item['price']} from {item['seller']}")
                    details = item.get('details', {})
                    if isinstance(details, dict):
                        speed = details.get('speed', 'N/A')
                        stamina = details.get('stamina', 'N/A')
                        breed = details.get('breed', 'N/A')
                        st.caption(f"Speed: {speed} | Stamina: {stamina} | Breed: {breed}")
                    else:
                        st.caption("Horse details unavailable.")

                    if st.button(f"Buy {item['name']}", key=f"buy_{i}"):
                        if st.session_state.money >= item['price']:
                            st.session_state.money -= item['price']
                            # Save money to Firebase
                            if "user_id" in st.session_state:
                                save_user_money(st.session_state.user_id, st.session_state.money)
                            st.session_state.stable_horses[item['name']] = details
                            del market[i]
                            st.success(f"You bought {item['name']}!")
                            ref.child('auction_market').set(serialize_data(market))
                            break
                        else:
                            st.error("Not enough funds.")
        else:
            st.error("Could not connect to Firebase. Auction marketplace unavailable.")