# --- Revenue and Expense Tracking ---
def track_revenue(amount, source):
    """Track revenue from a specific source (e.g., 'race', 'betting', 'boarding', etc.)"""
    log = st.session_state.get(LOG_KEY, get_user_data("business_log") or [])
    today = datetime.now().strftime("%b %d")
    # Find today's log entry or create new
    entry = next((e for e in log if e["day"] == today), None)
    if not entry:
        # Initialize default values for new log entry
        revenue = 0
        total_cost = 0
        net = 0
        count = len(st.session_state.get("horses", {}))
        log_entry = {
            "day": datetime.now().strftime("%b %d"),
            "revenue": revenue,
            "cost": total_cost,
            "profit": net,
            "horses": count,
            "money": st.session_state.money,
            "sources": {}
        }
        log.append(log_entry)
        # Track daily revenue and costs for analytics
        try:
            track_revenue(revenue, "daily_ops")
            track_expense(total_cost, "daily_ops")
        except Exception:
            pass
    st.session_state[LOG_KEY] = log[-30:]
    save_user_data("business_log", log[-30:])

def track_expense(amount, category):
    """Track expense from a specific category (e.g., 'feed', 'vet', 'maintenance', etc.)"""
    log = st.session_state.get(LOG_KEY, get_user_data("business_log") or [])
    today = datetime.now().strftime("%b %d")
    entry = next((e for e in log if e["day"] == today), None)
    if not entry:
        entry = {
            "day": today,
            "revenue": 0,
            "cost": 0,
            "profit": 0,
            "horses": len(st.session_state.get("horses", {})),
            "money": st.session_state.get("money", 0),
            "sources": {}
        }
        log.append(entry)
    entry["cost"] += amount
    entry["profit"] -= amount
    entry["sources"][category] = entry["sources"].get(category, 0) - amount
    st.session_state[LOG_KEY] = log[-30:]
    save_user_data("business_log", log[-30:])
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from firebase_utils import save_user_data, get_user_data, save_user_money
import random

# --- Stable Business Definitions ---

def check_expansion_eligibility(current_money):
    """
    Determines if the player has enough money to expand their stable operations.
    This function mimics real-life investment decisions — expanding a stable requires capital and planning.
    """
    return current_money >= 2000


def calculate_daily_operating_costs(horse_count):
    """
    Calculates the daily fixed and variable costs of running a horse stable.
    Teaches the player how scale affects operations: more horses = more feed, vet bills, and maintenance.
    """
    variable_costs = horse_count * (DAILY_BASE_COSTS['feed_per_horse'] + DAILY_BASE_COSTS['veterinary_per_horse'])
    total_cost = variable_costs + DAILY_BASE_COSTS['stable_maintenance'] + DAILY_BASE_COSTS['insurance']
    return round(total_cost, 2)


DAILY_BASE_COSTS = {
    "feed_per_horse": 8.0,           # Daily oats, hay, supplements
    "veterinary_per_horse": 3.0,     # Checkups, hoof cleaning, preventive meds
    "stable_maintenance": 25.0,      # Cleaning, tools, infrastructure upkeep
    "insurance": 6.0                 # Safety & liability in case a horse gets injured
}


def handle_race_entry_fee(num_horses):
    """
    Deducts a race entry fee per horse.
    This introduces a cost-benefit decision: enter many horses and risk losses, or choose wisely.
    """
    fee_per_entry = 15
    total_fee = num_horses * fee_per_entry
    st.session_state.money -= total_fee
    # Save money to Firebase
    if "user_id" in st.session_state:
        save_user_money(st.session_state.user_id, st.session_state.money)
    return total_fee


# --- Logging and Revenue Simulation ---
LOG_KEY = "business_log"
LOAN_KEY = "loan_amount"

def process_daily_log():
    horses = st.session_state.get("horses", {})
    count = len(horses)
    total_cost = calculate_daily_operating_costs(count)
    revenue = round(100 + random.uniform(0, 1) * 150, 2)
    net = revenue - total_cost
    st.session_state.money += net
    
    # Save money to Firebase
    if "user_id" in st.session_state:
        save_user_money(st.session_state.user_id, st.session_state.money)

    log = st.session_state.get(LOG_KEY, get_user_data("business_log") or [])
    log.append({
        "day": datetime.now().strftime("%b %d"),
        "revenue": revenue,
        "cost": total_cost,
        "profit": net,
        "horses": count,
        "money": st.session_state.money
    })
    log = log[-30:]
    st.session_state[LOG_KEY] = log
    save_user_data("business_log", log)
    # Track daily revenue and costs for analytics
    try:
        track_revenue(revenue, "daily_ops")
        track_expense(total_cost, "daily_ops")
    except Exception:
        pass
    return revenue, total_cost, net


# --- Main UI ---
def render_financial_dashboard():
    st.header("📈 Gold Creek Stables - Business Intelligence Dashboard")

    # Current Financial Status
    money = st.session_state.get("money", 0)
    current_loan = st.session_state.get(LOAN_KEY, 0)
    net_worth = money - current_loan
    
    # Get current business metrics
    horse_count = len(st.session_state.get("horses", {}))
    daily_costs = calculate_daily_operating_costs(horse_count)
    
    # Financial Overview Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Cash on Hand", 
            value=f"${money:,.2f}",
            delta=f"${money - 1000:.2f}" if money > 1000 else None
        )
    
    with col2:
        st.metric(
            label="🏦 Outstanding Debt", 
            value=f"${current_loan:,.2f}",
            delta=f"-${current_loan * 0.05:.2f}" if current_loan > 0 else "Debt Free!"
        )
    
    with col3:
        st.metric(
            label="📊 Net Worth", 
            value=f"${net_worth:,.2f}",
            delta="💎" if net_worth > 5000 else "📈" if net_worth > 0 else "⚠️"
        )
    
    with col4:
        st.metric(
            label="🐎 Stable Size", 
            value=f"{horse_count} horses",
            delta="Growing!" if horse_count > 3 else "Expanding..." if horse_count > 0 else "Start Here"
        )

    # Daily Operations Button with Enhanced Feedback
    st.write("---")
    col_run, col_info = st.columns([2, 3])
    
    with col_run:
        if st.button("🏃 Run Daily Operations", type="primary", use_container_width=True):
            revenue, cost, profit = process_daily_log()
            
            # Enhanced success display with breakdown
            if profit > 0:
                st.success(f"✅ **Daily Operations Complete!**")
                st.balloons()
            elif profit < -20:
                st.error(f"📉 **Tough Day at the Stable**")
            else:
                st.warning(f"😐 **Break-Even Day**")
            
            # Detailed financial breakdown
            st.write("### 📋 Today's Financial Summary")
            
            # Revenue breakdown
            st.write("**💰 Revenue Sources:**")
            col_rev1, col_rev2 = st.columns(2)
            with col_rev1:
                boarding_revenue = revenue * 0.4
                training_revenue = revenue * 0.3
                st.write(f"🏠 Boarding Fees: ${boarding_revenue:.2f}")
                st.write(f"🎯 Training Services: ${training_revenue:.2f}")
            with col_rev2:
                misc_revenue = revenue * 0.2
                breeding_revenue = revenue * 0.1
                st.write(f"🛠️ Miscellaneous: ${misc_revenue:.2f}")
                st.write(f"🍀 Breeding Income: ${breeding_revenue:.2f}")
            
            st.write(f"**💸 Total Revenue: ${revenue:.2f}**")
            
            # Cost breakdown
            st.write("**📊 Operating Expenses:**")
            col_cost1, col_cost2 = st.columns(2)
            with col_cost1:
                feed_cost = horse_count * DAILY_BASE_COSTS['feed_per_horse']
                vet_cost = horse_count * DAILY_BASE_COSTS['veterinary_per_horse']
                st.write(f"🌾 Feed & Nutrition: ${feed_cost:.2f}")
                st.write(f"🩺 Veterinary Care: ${vet_cost:.2f}")
            with col_cost2:
                maintenance_cost = DAILY_BASE_COSTS['stable_maintenance']
                insurance_cost = DAILY_BASE_COSTS['insurance']
                st.write(f"🔧 Stable Maintenance: ${maintenance_cost:.2f}")
                st.write(f"🛡️ Insurance & Safety: ${insurance_cost:.2f}")
            
            st.write(f"**💳 Total Expenses: ${cost:.2f}**")
            
            # Profit analysis with recommendations
            st.write("---")
            profit_margin = (profit / revenue * 100) if revenue > 0 else 0
            
            if profit > 50:
                st.success(f"🎉 **Excellent Profit: ${profit:.2f}** (Margin: {profit_margin:.1f}%)")
                st.write("💡 **Recommendation:** Consider expanding your stable or investing in premium horses!")
            elif profit > 20:
                st.info(f"👍 **Good Profit: ${profit:.2f}** (Margin: {profit_margin:.1f}%)")
                st.write("💡 **Recommendation:** You're on track! Maybe hire a premium jockey?")
            elif profit > 0:
                st.warning(f"😐 **Small Profit: ${profit:.2f}** (Margin: {profit_margin:.1f}%)")
                st.write("💡 **Recommendation:** Look for ways to increase revenue or reduce costs.")
            else:
                st.error(f"📉 **Loss: ${profit:.2f}** (Margin: {profit_margin:.1f}%)")
                st.write("💡 **Recommendation:** Consider reducing costs or taking a loan to invest in growth.")

    with col_info:
        st.write("**📈 Daily Operations Include:**")
        st.write("• 🌾 Feeding and caring for horses")
        st.write("• 🩺 Veterinary checkups")
        st.write("• 🏠 Stable maintenance")
        st.write("• 💰 Customer boarding fees")
        st.write("• 🎯 Training service revenue")
        st.write("• 🛡️ Insurance and safety costs")

    # Business Performance Analytics
    log = st.session_state.get(LOG_KEY, get_user_data("business_log") or [])
    if log:
        st.write("---")
        st.write("### 📊 Business Performance Analytics")
        
        df = pd.DataFrame(log)
        
        # Performance metrics
        col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
        
        avg_daily_profit = df['profit'].mean()
        total_revenue = df['revenue'].sum()
        best_day_profit = df['profit'].max()
        days_profitable = len(df[df['profit'] > 0])
        
        with col_metric1:
            st.metric("📅 Avg Daily Profit", f"${avg_daily_profit:.2f}")
        with col_metric2:
            st.metric("💰 Total Revenue", f"${total_revenue:.2f}")
        with col_metric3:
            st.metric("🏆 Best Day Profit", f"${best_day_profit:.2f}")
        with col_metric4:
            success_rate = (days_profitable / len(df) * 100) if len(df) > 0 else 0
            st.metric("✅ Success Rate", f"{success_rate:.1f}%")
        
        # Enhanced chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['day'], 
            y=df['revenue'], 
            name='💰 Revenue', 
            line=dict(color='#2E8B57', width=3),
            fill='tonexty'
        ))
        fig.add_trace(go.Scatter(
            x=df['day'], 
            y=df['cost'], 
            name='💸 Costs', 
            line=dict(color='#DC143C', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=df['day'], 
            y=df['profit'], 
            name='📈 Profit', 
            line=dict(color='#4169E1', width=4)
        ))
        
        fig.update_layout(
            title="📈 30-Day Business Performance Trend",
            xaxis_title="Business Day",
            yaxis_title="Amount ($)",
            template="plotly_white",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Business insights
        if len(df) >= 7:
            recent_trend = df['profit'].tail(7).mean()
            older_trend = df['profit'].head(7).mean() if len(df) >= 14 else avg_daily_profit
            
            st.write("### 🔍 Business Insights")
            if recent_trend > older_trend * 1.1:
                st.success("📈 **Trending Up!** Your business is growing stronger!")
            elif recent_trend < older_trend * 0.9:
                st.warning("📉 **Attention Needed** - Recent performance is declining")
            else:
                st.info("➡️ **Steady Performance** - Business is stable")

    # Financial Status Assessment
    st.write("---")
    if money < -500:
        st.error("🚨 **BANKRUPTCY WARNING!** You're deep in debt! Consider Uncle Mike's emergency loans!")
    elif money < 0:
        st.warning("⚠️ **Cash Flow Alert** - You're operating at a deficit. Time for strategic decisions!")
    elif check_expansion_eligibility(money):
        st.success("🏗️ **🎉 EXPANSION OPPORTUNITY!** 🎉")
        st.write(f"💎 With ${money:,.2f} in cash, you're eligible to:")
        st.write("• � Build additional stable wings")
        st.write("• 🐎 Invest in premium breeding stock") 
        st.write("• 🎯 Hire world-class trainers")
        st.write("• 🏆 Enter exclusive racing competitions")
        if money > 10000:
            st.write("• 🌟 **Elite Status** - Consider franchise opportunities!")
    else:
        needed = 2000 - money
        st.info(f"💼 **Growing Business** - You need ${needed:,.2f} more for major expansion opportunities")

    # --- Uncle Mike's Escalating Loan Terms ---
    st.subheader("🏦 Uncle Mike's Generous Loan Emporium")
    current_loan = st.session_state.get(LOAN_KEY, 0)
    st.write(f"💸 Outstanding Loan: ${current_loan:,}")
    
    # Initialize loan agreements tracker
    if 'loan_agreements' not in st.session_state:
        st.session_state.loan_agreements = []
    
    def get_loan_terms(amount):
        """Return escalating funny terms based on loan amount"""
        if amount <= 1000:
            return {
                "terms": ["🎯 Must high-five Uncle Mike every Tuesday", "🐸 Agree to croak like a frog when greeting customers"],
                "backing": "Uncle Mike's pocket change",
                "interest": "0% (Uncle Mike is feeling generous!)",
                "collateral": "Your dignity (minimal risk)"
            }
        elif amount <= 5000:
            return {
                "terms": ["🦄 Must refer to all horses as 'unicorns' for a week", "🍕 Deliver Uncle Mike's favorite pizza every Friday", "🎪 Perform a cartwheel before each race"],
                "backing": "Uncle Mike's emergency fund",
                "interest": "1% monthly (paid in compliments)",
                "collateral": "Your right to choose horse names"
            }
        elif amount <= 10000:
            return {
                "terms": ["🎭 Wear a clown nose during all business meetings", "🦆 Quack instead of saying 'yes' for 30 days", "🎨 Paint Uncle Mike's portrait on your stable wall", "🕺 Do the chicken dance every time you win a race"],
                "backing": "Uncle Mike's vacation fund (goodbye Bahamas!)",
                "interest": "2% monthly (paid in horse puns)",
                "collateral": "Your naming rights to all future horses"
            }
        elif amount <= 25000:
            return {
                "terms": ["👑 Crown Uncle Mike 'Honorary Stable King'", "🎪 Host a weekly variety show starring Uncle Mike", "🦸 Wear a superhero costume during all races", "🍰 Bake Uncle Mike a birthday cake every month (even if it's not his birthday)", "🎺 Learn to play 'Happy Birthday' on the kazoo"],
                "backing": "Uncle Mike's retirement fund",
                "interest": "3% monthly (paid in interpretive dance)",
                "collateral": "Your stable naming rights (it's now 'Mike's Magnificent Stable')"
            }
        elif amount <= 50000:
            return {
                "terms": ["🏰 Build Uncle Mike a throne in your office", "🎭 Hire Uncle Mike as your 'Executive Fun Officer'", "🦜 Speak only in pirate voice for 60 days", "🎪 Organize Uncle Mike's birthday party every month", "🍔 Name a burger after Uncle Mike at the local diner", "🎨 Commission a 10-foot statue of Uncle Mike"],
                "backing": "Uncle Mike's house mortgage",
                "interest": "4% monthly (paid in limerick poems)",
                "collateral": "Your stable becomes 'Uncle Mike's Wacky Horse Emporium'"
            }
        elif amount <= 100000:
            return {
                "terms": ["👔 Uncle Mike becomes your business partner", "🎪 Transform stable into Uncle Mike's theme park", "🦄 All horses must wear tutus", "🎭 Daily puppet shows featuring Uncle Mike", "🍕 Free pizza for Uncle Mike's friends (he has many)", "🎺 Marching band performance every race day", "📺 Star in Uncle Mike's reality TV show 'Stable Drama'"],
                "backing": "Uncle Mike's life savings + his mother's jewelry",
                "interest": "5% monthly (paid in country music performances)",
                "collateral": "Uncle Mike owns 49% of your stable"
            }
        elif amount <= 500000:
            return {
                "terms": ["🏛️ Rename the town after Uncle Mike", "🎪 Annual Uncle Mike Day celebration", "🦸 Uncle Mike's face on all horse blankets", "🎭 Weekly Shakespeare plays starring Uncle Mike", "🍰 Uncle Mike's face on a birthday cake every day", "🎺 Uncle Mike's personal marching band", "📺 24/7 Uncle Mike TV channel", "🏰 Build Uncle Mike's castle next to your stable", "🦜 All jockeys must speak in Uncle Mike impressions"],
                "backing": "Uncle Mike sold his kidney (don't ask which one)",
                "interest": "10% monthly (paid in full musical productions)",
                "collateral": "Uncle Mike owns 75% of everything you own"
            }
        else:  # Up to 1,000,000
            return {
                "terms": ["👑 Uncle Mike becomes Emperor of All Horses", "🌍 Establish 'Uncle Mike Land' - a sovereign nation", "🎪 All horses must worship Uncle Mike daily", "🦄 Genetic engineering to create Uncle Mike centaurs", "🎭 Uncle Mike's autobiography becomes required reading", "🍕 Uncle Mike gets his own pizza planet", "🎺 Symphony orchestra plays Uncle Mike's theme song 24/7", "📺 All TV shows now feature Uncle Mike", "🏰 Mount Rushmore now includes Uncle Mike's face", "🦸 Uncle Mike becomes your legal guardian", "🎨 All currency features Uncle Mike's portrait"],
                "backing": "Uncle Mike sold EVERYTHING (including his soul to a very confused demon)",
                "interest": "25% monthly (paid in your firstborn child's allowance)",
                "collateral": "Uncle Mike legally owns you, your stable, your town, and your dreams"
            }
    
    st.write("💰 **Loan Amount (backed by Uncle Mike's questionable financial decisions):**")
    loan_request = st.number_input("Request loan amount", min_value=0, max_value=1000000, step=100, format="%d")
    
    if loan_request > 0:
        terms_data = get_loan_terms(loan_request)
        
        st.write("---")
        st.write(f"### 📋 Loan Terms for ${loan_request:,}")
        st.write(f"**🏦 Backed by:** {terms_data['backing']}")
        st.write(f"**💸 Interest Rate:** {terms_data['interest']}")
        st.write(f"**🔒 Collateral:** {terms_data['collateral']}")
        
        st.write("**📜 You must agree to the following terms:**")
        for i, term in enumerate(terms_data['terms'], 1):
            st.write(f"{i}. {term}")
        
        st.write("---")
        
        # Escalating agreement checkboxes
        agreement_key = f"loan_agreement_{loan_request}"
        
        if loan_request <= 1000:
            agree = st.checkbox("✅ I agree to these reasonable and dignified terms")
        elif loan_request <= 5000:
            agree = st.checkbox("🤡 I agree to these mildly embarrassing terms")
        elif loan_request <= 10000:
            agree = st.checkbox("🎪 I agree to these ridiculous terms (my dignity is optional)")
        elif loan_request <= 25000:
            agree = st.checkbox("👑 I bow down to Uncle Mike and agree to these absurd terms")
        elif loan_request <= 50000:
            agree = st.checkbox("🦜 Arrr! I agree to these completely bonkers terms, matey!")
        elif loan_request <= 100000:
            agree = st.checkbox("🎭 I have lost all sense of reality and agree to these insane terms")
        elif loan_request <= 500000:
            agree = st.checkbox("🌪️ I have descended into madness and gleefully accept these terms")
        else:
            agree = st.checkbox("🤯 I have transcended human understanding and embrace the chaos of these terms")
        
        if agree and st.button(f"💰 GET MY ${loan_request:,} FROM UNCLE MIKE!", type="primary"):
            # Add the loan
            st.session_state.money += loan_request
            st.session_state[LOAN_KEY] = st.session_state.get(LOAN_KEY, 0) + loan_request
            
            # Save the agreement terms
            agreement = {
                "amount": loan_request,
                "terms": terms_data['terms'],
                "backing": terms_data['backing'],
                "date": "Today"
            }
            st.session_state.loan_agreements.append(agreement)
            
            # Save money to Firebase
            if "user_id" in st.session_state:
                save_user_money(st.session_state.user_id, st.session_state.money)
            
            # Celebratory message based on loan amount
            if loan_request >= 500000:
                st.balloons()
                st.success(f"🎉 CONGRATULATIONS! Uncle Mike has mortgaged his entire existence for your ${loan_request:,} loan! He's now living in a cardboard box but he's very proud of you!")
                st.write("🎪 Uncle Mike says: 'This is either the best or worst decision of my life! Probably both!'")
            elif loan_request >= 100000:
                st.success(f"🎭 AMAZING! Uncle Mike sold his house and is now living in your stable! Your ${loan_request:,} loan is approved!")
                st.write("🏠 Uncle Mike says: 'Who needs a house when you have DREAMS!'")
            elif loan_request >= 25000:
                st.success(f"🎪 FANTASTIC! Uncle Mike cancelled his retirement for your ${loan_request:,} loan!")
                st.write("👴 Uncle Mike says: 'Retirement is overrated anyway!'")
            elif loan_request >= 5000:
                st.success(f"🦄 WONDERFUL! Uncle Mike believes in unicorns now! Your ${loan_request:,} loan is approved!")
            else:
                st.success(f"🎯 APPROVED! Uncle Mike high-fived himself in excitement! Your ${loan_request:,} loan is ready!")
    
    # Show active agreements
    if st.session_state.loan_agreements:
        st.write("---")
        st.write("### 📜 Your Active Loan Agreements with Uncle Mike")
        for agreement in st.session_state.loan_agreements:
            with st.expander(f"💰 ${agreement['amount']:,} Loan Terms"):
                st.write(f"**🏦 Backed by:** {agreement['backing']}")
                st.write("**📋 Your binding agreements:**")
                for term in agreement['terms']:
                    st.write(f"• {term}")
    
    # Loan repayment
    st.write("---")
    if current_loan > 0:
        repay_amt = st.number_input("💸 Repay loan to Uncle Mike", min_value=0, max_value=int(current_loan), step=100)
        if st.button("💳 Repay Uncle Mike"):
            if st.session_state.money >= repay_amt:
                st.session_state.money -= repay_amt
                st.session_state[LOAN_KEY] = st.session_state.get(LOAN_KEY, 0) - repay_amt
                # Save money to Firebase
                if "user_id" in st.session_state:
                    save_user_money(st.session_state.user_id, st.session_state.money)
                
                # Remove agreements proportionally
                remaining_loan = st.session_state.get(LOAN_KEY, 0)
                if remaining_loan == 0:
                    st.session_state.loan_agreements = []
                    st.success(f"🎉 Fully repaid ${repay_amt:,} to Uncle Mike! You are FREE from all agreements!")
                    st.write("🕺 Uncle Mike says: 'You can stop doing the chicken dance now!'")
                else:
                    st.success(f"💰 Repaid ${repay_amt:,} to Uncle Mike! Still owe ${remaining_loan:,}")
                    st.write("🤹 Uncle Mike says: 'Keep those cartwheels coming!'")
            else:
                st.error("💸 Not enough funds to repay Uncle Mike! He's very disappointed and is doing sad puppet shows.")

    # --- Achievements ---
    st.subheader("🏅 Achievements")
    if len(st.session_state.get("horses", {})) >= 5:
        st.success("🐴 Horse Whisperer: Own 5+ horses")
    if st.session_state.money >= 5000:
        st.success("💰 Mogul Status: Reach $5000+")
    if any(entry['profit'] > 200 for entry in log):
        st.success("🚀 Big Day: Earn $200+ profit in a day")