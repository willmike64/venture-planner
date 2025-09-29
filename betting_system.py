# betting_system.py placeholder - replace with actual file if missing
import streamlit as st # type: ignore
from firebase_utils import save_bets, load_bets, save_user_money
from datetime import datetime

BET_POOL_KEY = "parimutuel_bet_pool"
MIN_BET = 25

def calculate_parimutuel_odds(bet_pool):
    total_pool = sum(bet_pool.values())
    odds = {}
    for horse, amount in bet_pool.items():
        if amount == 0:
            odds[horse] = 10.0
        else:
            odds[horse] = round(total_pool / amount, 2)
    return odds

def render_betting_interface():
    st.header("🎫 Racetrack Betting Windows")
    st.markdown("*Professional horse racing betting with Win, Place & Show options*")

    # Initialize betting session state
    if 'betting_tickets' not in st.session_state:
        st.session_state.betting_tickets = []
    if 'bet_pools' not in st.session_state:
        st.session_state.bet_pools = {
            'win': {},
            'place': {},
            'show': {}
        }

    # Load existing bets
    horses_data = st.session_state.get("horses", {})
    leaderboard = st.session_state.get("race_leaderboard", [])

    # Handle both old (dict) and new (list) horse data structures
    if isinstance(horses_data, list):
        # New format: list of horse dictionaries
        horse_names = [horse.get('name', '') for horse in horses_data if horse.get('name')]
    elif isinstance(horses_data, dict):
        # Old format: dictionary of horses
        horse_names = list(horses_data.keys())
    else:
        horse_names = []

    # Add stable horses to available horses
    stable_horses = st.session_state.get('stable_horses', {})
    all_horses = set(horse_names)
    for stable_horse in stable_horses.keys():
        all_horses.add(f"{stable_horse} (YOUR HORSE ⭐)")

    # Get horses from recent races
    for entry in leaderboard[:5]:
        if isinstance(entry, dict) and "winners" in entry:
            all_horses.update(entry["winners"])

    available_horses = sorted(list(all_horses))

    # --- Current Betting Pools Display ---
    st.markdown("### 🏁 Current Betting Pools & Odds")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🥇 WIN Pool** *(1st Place Only)*")
        win_pool = st.session_state.bet_pools['win']
        if win_pool:
            win_odds = calculate_parimutuel_odds(win_pool)
            for horse, amount in sorted(win_pool.items(), key=lambda x: x[1], reverse=True):
                st.text(f"{horse}: ${amount:.0f} (Odds: {win_odds[horse]:.1f}:1)")
        else:
            st.info("No WIN bets yet")
    
    with col2:
        st.markdown("**🥈 PLACE Pool** *(1st or 2nd)*")
        place_pool = st.session_state.bet_pools['place']
        if place_pool:
            place_odds = calculate_parimutuel_odds(place_pool)
            for horse, amount in sorted(place_pool.items(), key=lambda x: x[1], reverse=True):
                st.text(f"{horse}: ${amount:.0f} (Odds: {place_odds[horse]:.1f}:1)")
        else:
            st.info("No PLACE bets yet")
    
    with col3:
        st.markdown("**🥉 SHOW Pool** *(1st, 2nd, or 3rd)*")
        show_pool = st.session_state.bet_pools['show']
        if show_pool:
            show_odds = calculate_parimutuel_odds(show_pool)
            for horse, amount in sorted(show_pool.items(), key=lambda x: x[1], reverse=True):
                st.text(f"{horse}: ${amount:.0f} (Odds: {show_odds[horse]:.1f}:1)")
        else:
            st.info("No SHOW bets yet")

    # --- Stable Owner's Edge ---
    stable_horses = st.session_state.get('stable_horses', {})
    if stable_horses:
        st.markdown("### 🎯 Owner's Advantage")
        st.info("💡 As a stable owner, you have insider knowledge! Your horses get betting bonuses and you can make informed decisions.")
        
        with st.expander("📊 Your Horses' Racing Intel"):
            for horse_name, horse_data in stable_horses.items():
                wins = horse_data.get('wins', 0)
                races = horse_data.get('races', 0)
                win_rate = (wins/races*100) if races > 0 else 0
                training = horse_data.get('training_count', 0)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(f"🐎 {horse_name}", f"{win_rate:.1f}% win rate", f"{wins}/{races} races")
                with col2:
                    st.metric("Speed", f"{horse_data.get('speed', 5):.1f}", f"+{training} training")
                with col3:
                    confidence = "High" if win_rate > 60 else "Medium" if win_rate > 30 else "Building"
                    st.metric("Confidence", confidence, f"{horse_data.get('health', 100)}% health")

    # --- Racetrack Betting Window ---
    st.markdown("### � Place Your Bets")
    
    with st.container():
        st.markdown("**🏇 Racing Form & Betting Window**")
        
        if available_horses:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Betting Slip Interface
                st.markdown("#### 🎯 Betting Slip")
                
                bet_horse = st.selectbox("🐎 Choose Your Horse:", [""] + available_horses, key="bet_horse_select")
                
                if bet_horse:
                    # Show horse information if it's your horse
                    is_own_horse = bet_horse and "YOUR HORSE" in bet_horse
                    actual_name = bet_horse.split(" (YOUR HORSE")[0] if is_own_horse else bet_horse
                    
                    if is_own_horse and actual_name in stable_horses:
                        horse_data = stable_horses[actual_name]
                        st.info(f"🎯 **INSIDER INFO**: {actual_name} - Speed: {horse_data.get('speed', 5):.1f}, Training: {horse_data.get('training_count', 0)} sessions, Health: {horse_data.get('health', 100)}%")
                    
                    # Bet Type Selection
                    bet_type = st.selectbox("📋 Bet Type:", ["WIN", "PLACE", "SHOW"], key="bet_type_select")
                    
                    # Bet type explanations
                    if bet_type == "WIN":
                        st.caption("💡 **WIN**: Horse must finish 1st place to collect")
                    elif bet_type == "PLACE":
                        st.caption("💡 **PLACE**: Horse must finish 1st OR 2nd place to collect")
                    elif bet_type == "SHOW":
                        st.caption("💡 **SHOW**: Horse must finish 1st, 2nd, OR 3rd place to collect")
                    
                    # Betting Amount
                    base_min = MIN_BET
                    min_bet = base_min // 2 if is_own_horse else base_min
                    bet_amount = st.number_input(
                        f"💰 Wager Amount (${min_bet} min{' - Owner Discount!' if is_own_horse else ''}):", 
                        min_value=min_bet, 
                        step=5, 
                        key="bet_amount_input"
                    )
                    
                    # Calculate potential payout preview
                    pool_key = bet_type.lower()
                    current_pool = st.session_state.bet_pools[pool_key]
                    
                    if bet_horse in current_pool:
                        temp_pool = current_pool.copy()
                        temp_pool[bet_horse] = temp_pool.get(bet_horse, 0) + bet_amount
                        temp_odds = calculate_parimutuel_odds(temp_pool)
                        estimated_odds = temp_odds.get(bet_horse, 0)
                    else:
                        estimated_odds = 10.0  # Default odds for new bet
                    
                    potential_payout = bet_amount * estimated_odds
                    st.info(f"📊 **Estimated Odds**: {estimated_odds:.1f}:1 | **Potential Payout**: ${potential_payout:.2f}")
                    
                    # Place Bet Button
                    if st.button("🎫 ADD TO BETTING SLIP", type="primary", key="place_bet_btn"):
                        if st.session_state.money >= bet_amount:
                            # Deduct money
                            st.session_state.money -= bet_amount
                            if "user_id" in st.session_state:
                                save_user_money(st.session_state.user_id, st.session_state.money)
                            
                            # Apply owner bonus
                            effective_amount = bet_amount * 1.5 if is_own_horse else bet_amount
                            
                            # Add to appropriate pool
                            pool_key = bet_type.lower()
                            st.session_state.bet_pools[pool_key][actual_name] = st.session_state.bet_pools[pool_key].get(actual_name, 0) + effective_amount
                            
                            # Add to betting tickets
                            ticket = {
                                'horse': actual_name,
                                'bet_type': bet_type,
                                'amount': bet_amount,
                                'odds': estimated_odds,
                                'is_own_horse': is_own_horse,
                                'timestamp': datetime.now().strftime("%H:%M:%S")
                            }
                            st.session_state.betting_tickets.append(ticket)
                            
                            # Save bets to Firebase
                            save_bets(st.session_state.bet_pools)
                            
                            success_msg = f"✅ ${bet_amount} {bet_type} bet on {actual_name}"
                            if is_own_horse:
                                success_msg += " (Owner Bonus Applied!)"
                            st.success(success_msg)
                            st.rerun()
                        else:
                            st.error("💸 Insufficient funds!")
            
            with col2:
                # Current Betting Slip
                st.markdown("#### 🧾 Your Betting Slip")
                
                if st.session_state.betting_tickets:
                    total_wagered = 0
                    
                    for i, ticket in enumerate(st.session_state.betting_tickets):
                        with st.container():
                            st.markdown(f"**Ticket #{i+1}** *({ticket['timestamp']})*")
                            st.markdown(f"🐎 **{ticket['horse']}** {'⭐' if ticket['is_own_horse'] else ''}")
                            st.markdown(f"📋 **{ticket['bet_type']}** - ${ticket['amount']}")
                            st.markdown(f"📊 Est. Odds: {ticket['odds']:.1f}:1")
                            
                            if st.button("❌", key=f"remove_bet_{i}", help="Remove this bet"):
                                # Refund money
                                st.session_state.money += ticket['amount']
                                if "user_id" in st.session_state:
                                    save_user_money(st.session_state.user_id, st.session_state.money)
                                
                                # Remove from pool
                                pool_key = ticket['bet_type'].lower()
                                effective_amount = ticket['amount'] * 1.5 if ticket['is_own_horse'] else ticket['amount']
                                current_amount = st.session_state.bet_pools[pool_key].get(ticket['horse'], 0)
                                new_amount = max(0, current_amount - effective_amount)
                                if new_amount == 0:
                                    st.session_state.bet_pools[pool_key].pop(ticket['horse'], None)
                                else:
                                    st.session_state.bet_pools[pool_key][ticket['horse']] = new_amount
                                
                                # Remove ticket
                                st.session_state.betting_tickets.pop(i)
                                save_bets(st.session_state.bet_pools)
                                st.rerun()
                            
                            st.divider()
                            total_wagered += ticket['amount']
                    
                    st.metric("💰 Total Wagered", f"${total_wagered}")
                    
                    if st.button("🗑️ CLEAR ALL BETS", type="secondary"):
                        # Refund all money
                        total_refund = sum(t['amount'] for t in st.session_state.betting_tickets)
                        st.session_state.money += total_refund
                        if "user_id" in st.session_state:
                            save_user_money(st.session_state.user_id, st.session_state.money)
                        
                        # Clear all bets
                        st.session_state.betting_tickets = []
                        st.session_state.bet_pools = {'win': {}, 'place': {}, 'show': {}}
                        save_bets(st.session_state.bet_pools)
                        st.success(f"All bets cleared! ${total_refund} refunded.")
                        st.rerun()
                        
                else:
                    st.info("🎫 No bets placed yet.\nAdd bets to build your slip!")
                    
        else:
            st.warning("🐎 No horses available for betting. Enter a race first!")

    # --- Partnership Opportunities ---
    if stable_horses:
        st.markdown("### 🤝 Stable Partnership Deals")
        with st.expander("💼 Business Partnerships"):
            st.markdown("*Use your stable's reputation to negotiate better deals and sponsorships*")
            
            # Partnership based on stable performance
            total_wins = sum(h.get('wins', 0) for h in stable_horses.values())
            total_races = sum(h.get('races', 0) for h in stable_horses.values())
            stable_reputation = (total_wins / total_races * 100) if total_races > 0 else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🏆 Stable Reputation", f"{stable_reputation:.1f}%", f"{total_wins} wins")
            with col2:
                st.metric("💰 Partnership Level", 
                         "Elite" if stable_reputation > 70 else "Professional" if stable_reputation > 40 else "Amateur",
                         f"{len(stable_horses)} horses")
            
            # Available partnerships based on reputation
            if stable_reputation > 60:
                st.success("🌟 **Elite Partnership Available**: Premium betting multipliers and exclusive races!")
                if st.button("Activate Elite Partnership (+50% betting returns)"):
                    st.session_state['partnership_bonus'] = 1.5
                    st.success("Elite partnership activated! All betting returns increased by 50%!")
            elif stable_reputation > 30:
                st.info("⭐ **Professional Partnership Available**: Better odds and training discounts!")
                if st.button("Activate Professional Partnership (+25% betting returns)"):
                    st.session_state['partnership_bonus'] = 1.25
                    st.success("Professional partnership activated! All betting returns increased by 25%!")
            else:
                st.warning("� Build your stable's reputation to unlock partnership deals!")
                st.caption("Win more races to improve your partnership opportunities")

    # --- Betting Analytics ---
    if st.session_state.betting_tickets:
        st.markdown("### 📊 Betting Portfolio Analysis")
        with st.expander("📈 Your Betting Statistics"):
            
            # Analyze betting patterns
            total_bet = sum(ticket['amount'] for ticket in st.session_state.betting_tickets)
            bet_types = {}
            horse_bets = {}
            
            for ticket in st.session_state.betting_tickets:
                bet_types[ticket['bet_type']] = bet_types.get(ticket['bet_type'], 0) + ticket['amount']
                horse_bets[ticket['horse']] = horse_bets.get(ticket['horse'], 0) + ticket['amount']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💰 Total Wagered", f"${total_bet}")
                st.markdown("**Bet Type Distribution:**")
                for bet_type, amount in bet_types.items():
                    percentage = (amount / total_bet) * 100
                    st.write(f"• {bet_type}: ${amount} ({percentage:.1f}%)")
            
            with col2:
                st.metric("🎫 Total Tickets", len(st.session_state.betting_tickets))
                st.markdown("**Top Horses by Wagers:**")
                sorted_horses = sorted(horse_bets.items(), key=lambda x: x[1], reverse=True)
                for horse, amount in sorted_horses[:5]:
                    is_owned = horse in stable_horses
                    ownership_indicator = " ⭐" if is_owned else ""
                    st.write(f"• {horse}{ownership_indicator}: ${amount}")
            
            with col3:
                owned_bets = sum(ticket['amount'] for ticket in st.session_state.betting_tickets if ticket['is_own_horse'])
                if owned_bets > 0:
                    st.metric("🏠 Owner Bets", f"${owned_bets}")
                    owner_percentage = (owned_bets / total_bet) * 100
                    st.write(f"Owner bet ratio: {owner_percentage:.1f}%")
                else:
                    st.metric("🏠 Owner Bets", "$0")
                    st.write("No bets on owned horses")

def calculate_win_place_show_payouts(race_results, bet_pools):
    """Calculate payouts for Win, Place, Show bets based on race results"""
    payouts = {'win': {}, 'place': {}, 'show': {}}
    
    if not race_results or len(race_results) < 1:
        return payouts
    
    # Get finishing positions (assuming race_results is list of (horse, speed) tuples sorted by position)
    first_place = race_results[0][0]['name'] if isinstance(race_results[0][0], dict) else race_results[0][0]
    second_place = race_results[1][0]['name'] if len(race_results) > 1 and isinstance(race_results[1][0], dict) else (race_results[1][0] if len(race_results) > 1 else None)
    third_place = race_results[2][0]['name'] if len(race_results) > 2 and isinstance(race_results[2][0], dict) else (race_results[2][0] if len(race_results) > 2 else None)
    
    # Calculate WIN payouts (only first place wins)
    win_pool = bet_pools.get('win', {})
    if win_pool and first_place in win_pool:
        total_win_pool = sum(win_pool.values())
        winner_bets = win_pool[first_place]
        if winner_bets > 0:
            payouts['win'][first_place] = total_win_pool / winner_bets
    
    # Calculate PLACE payouts (first or second place wins)
    place_pool = bet_pools.get('place', {})
    if place_pool:
        total_place_pool = sum(place_pool.values())
        place_winners = [first_place]
        if second_place and second_place != first_place:
            place_winners.append(second_place)
        
        place_winner_bets = sum(place_pool.get(horse, 0) for horse in place_winners)
        if place_winner_bets > 0:
            for horse in place_winners:
                if horse in place_pool:
                    payouts['place'][horse] = total_place_pool / place_winner_bets
    
    # Calculate SHOW payouts (first, second, or third place wins)
    show_pool = bet_pools.get('show', {})
    if show_pool:
        total_show_pool = sum(show_pool.values())
        show_winners = [first_place]
        if second_place and second_place != first_place:
            show_winners.append(second_place)
        if third_place and third_place not in show_winners:
            show_winners.append(third_place)
        
        show_winner_bets = sum(show_pool.get(horse, 0) for horse in show_winners)
        if show_winner_bets > 0:
            for horse in show_winners:
                if horse in show_pool:
                    payouts['show'][horse] = total_show_pool / show_winner_bets
    
    return payouts

def process_race_payouts(race_results):
    """Process payouts after a race completes"""
    if 'betting_tickets' not in st.session_state or not st.session_state.betting_tickets:
        return
    
    payouts = calculate_win_place_show_payouts(race_results, st.session_state.bet_pools)
    total_winnings = 0
    winning_tickets = []
    
    for ticket in st.session_state.betting_tickets:
        horse = ticket['horse']
        bet_type = ticket['bet_type'].lower()
        amount = ticket['amount']
        
        if horse in payouts.get(bet_type, {}):
            payout_multiplier = payouts[bet_type][horse]
            winnings = amount * payout_multiplier
            total_winnings += winnings
            winning_tickets.append({
                'horse': horse,
                'bet_type': bet_type.upper(),
                'amount': amount,
                'winnings': winnings,
                'multiplier': payout_multiplier
            })
    
    if total_winnings > 0:
        st.session_state.money += total_winnings
        if "user_id" in st.session_state:
            save_user_money(st.session_state.user_id, st.session_state.money)
        
        # Show winnings
        st.success(f"🎉 **BETTING PAYOUTS**: ${total_winnings:.2f} total winnings!")
        for ticket in winning_tickets:
            st.write(f"• {ticket['bet_type']} bet on {ticket['horse']}: ${ticket['amount']} → ${ticket['winnings']:.2f} ({ticket['multiplier']:.1f}:1)")
    
    # Clear betting tickets after race
    st.session_state.betting_tickets = []
    st.session_state.bet_pools = {'win': {}, 'place': {}, 'show': {}}
    save_bets(st.session_state.bet_pools)

    # --- Global Horse Hall of Fame ---
    st.markdown("### 🏆 Racing Hall of Fame")
    st.markdown("*See the legendary horses and their career achievements from all stables worldwide*")
    
    with st.expander("🌟 View Global Horse Legends"):
        from firebase_utils import load_global_horse_history
        
        try:
            global_history = load_global_horse_history()
            
            if global_history is not None and isinstance(global_history, dict):
                # Sort horses by various criteria
                sort_option = st.selectbox("Sort by:", [
                    "Win Percentage", "Total Wins", "Total Earnings", "Total Races", "Recent Activity"
                ])
                
                # Filter and sort horses
                qualified_horses = {}
                for horse_name, record in global_history.items():
                    if isinstance(record, dict) and record.get('total_races', 0) >= 3:  # At least 3 races
                        qualified_horses[horse_name] = record
                
                if qualified_horses:
                    # Sort based on selected criteria
                    if sort_option == "Win Percentage":
                        sorted_horses = sorted(qualified_horses.items(), 
                                             key=lambda x: (x[1].get('total_wins', 0) / max(x[1].get('total_races', 1), 1)) * 100, 
                                             reverse=True)
                    elif sort_option == "Total Wins":
                        sorted_horses = sorted(qualified_horses.items(), 
                                             key=lambda x: x[1].get('total_wins', 0), reverse=True)
                    elif sort_option == "Total Earnings":
                        sorted_horses = sorted(qualified_horses.items(), 
                                             key=lambda x: x[1].get('total_earnings', 0), reverse=True)
                    elif sort_option == "Total Races":
                        sorted_horses = sorted(qualified_horses.items(), 
                                             key=lambda x: x[1].get('total_races', 0), reverse=True)
                    else:  # Recent Activity
                        sorted_horses = sorted(qualified_horses.items(), 
                                             key=lambda x: x[1].get('last_race_date', ''), reverse=True)
                    
                    # Display top horses
                    st.markdown("**🏆 Top Racing Legends:**")
                    for i, (horse_name, record) in enumerate(sorted_horses[:10]):
                        wins = record.get('total_wins', 0)
                        races = record.get('total_races', 0)
                        earnings = record.get('total_earnings', 0)
                        win_pct = (wins / max(races, 1)) * 100
                        
                        # Special highlighting for exceptional horses
                        if win_pct >= 75:
                            rank_emoji = "👑"
                        elif win_pct >= 60:
                            rank_emoji = "🌟"
                        elif wins >= 10:
                            rank_emoji = "🏆"
                        else:
                            rank_emoji = "🐎"
                        
                        # Career highlights
                        highlights = record.get('career_highlights', [])
                        highlight_text = f" {''.join(['⭐' for _ in highlights])}" if highlights else ""
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.markdown(f"**{i+1}. {rank_emoji} {horse_name}**{highlight_text}")
                        with col2:
                            st.metric("Record", f"{wins}-{races-wins}-0", f"{win_pct:.1f}% wins")
                        with col3:
                            st.metric("Earnings", f"${earnings:,}")
                        
                        # Show recent form for top 3
                        if i < 3 and record.get('race_history'):
                            recent_races = record['race_history'][-5:]  # Last 5 races
                            form = []
                            for race in recent_races:
                                if race.get('position', 10) == 1:
                                    form.append("🥇")
                                elif race.get('position', 10) <= 3:
                                    form.append("🥉")
                                else:
                                    form.append("❌")
                            st.caption(f"Recent Form: {''.join(form)}")
                        
                        st.divider()
                
                else:
                    st.info("No horses have completed enough races yet. Race more to build the Hall of Fame!")
            else:
                st.info("No global racing history available yet. Start racing to create the Hall of Fame!")
        
        except Exception as e:
            st.error(f"Unable to load Hall of Fame: {e}")
    
    # --- Search Specific Horse ---
    with st.expander("🔍 Search Horse History"):
        search_horse = st.text_input("Enter horse name to view detailed history:")
        if search_horse and st.button("Search History"):
            try:
                global_history = load_global_horse_history()
                if global_history is not None and isinstance(global_history, dict) and search_horse in global_history:
                    record = global_history[search_horse]
                    
                    # Ensure record is a dictionary before proceeding
                    if not isinstance(record, dict):
                        st.error(f"Invalid data format for horse '{search_horse}'.")
                    else:
                        st.success(f"Found **{search_horse}**!")

                    # Detailed stats with safe type checking
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        total_races = record.get('total_races', 0) if isinstance(record, dict) else 0
                        if isinstance(total_races, (int, float)):
                            st.metric("Total Races", int(total_races))
                        else:
                            st.metric("Total Races", 0)
                    with col2:
                        total_wins = record.get('total_wins', 0) if isinstance(record, dict) else 0
                        if isinstance(total_wins, (int, float)):
                            st.metric("Total Wins", int(total_wins))
                        else:
                            st.metric("Total Wins", 0)
                    with col3:
                        if isinstance(record, dict):
                            wins = record.get('total_wins', 0) if isinstance(record.get('total_wins', 0), (int, float)) else 0
                            races = record.get('total_races', 1) if isinstance(record.get('total_races', 1), (int, float)) else 1
                        else:
                            wins = 0
                            races = 1
                        win_pct = (wins / max(races, 1)) * 100
                        st.metric("Win Rate", f"{win_pct:.1f}%")
                    with col4:
                        total_earnings = record.get('total_earnings', 0) if isinstance(record, dict) else 0
                        if isinstance(total_earnings, (int, float)):
                            st.metric("Total Earnings", f"${int(total_earnings):,}")
                        else:
                            st.metric("Total Earnings", "$0")
                    
                    # Career info
                    if isinstance(record, dict):
                        st.markdown(f"**Breed:** {record.get('breed', 'Unknown')}")
                        st.markdown(f"**Owner:** {record.get('owner_id', 'Unknown')}")
                        if record.get('career_highlights'):
                            st.markdown(f"**Achievements:** {', '.join(record.get('career_highlights', []))}")
                    else:
                        st.markdown("**Breed:** Unknown")
                        st.markdown("**Owner:** Unknown")
                    
                    # Race history
                    if isinstance(record, dict) and record.get('race_history'):
                        st.markdown("**Recent Race History:**")
                        for race in record['race_history'][-10:]:  # Last 10 races
                            position = race.get('position', 'Unknown')
                            earnings = race.get('earnings', 0)
                            date = race.get('date', 'Unknown')[:10]  # Just the date part
                            
                            pos_emoji = "🥇" if position == 1 else "🥈" if position == 2 else "🥉" if position == 3 else f"{position}th"
                            st.markdown(f"• {date}: {pos_emoji} place, ${earnings} earned")
                else:
                    st.warning(f"No horse named '{search_horse}' found in racing records.")
            except Exception as e:
                st.error(f"Search failed: {e}")