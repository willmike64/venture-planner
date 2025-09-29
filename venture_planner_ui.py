import smtplib
from email.mime.text import MIMEText
def send_password_reset(email, new_password=None):
    user_id = firebase_login(email, "irrelevant").get('localId')
    user_profile = get_user_data(user_id)
    if user_profile is None:
        st.error("No account found for this email.")
        return
    if new_password:
        # Actually reset password in Firebase
        if isinstance(user_profile, dict):
            user_profile['password'] = new_password  # Always set password field
            save_user_data(user_id, user_profile)
            st.success("Password has been reset. You can now log in with your new password.")
        else:
            st.error("User profile data is corrupted or not found. Contact support.")
        return
    # Otherwise, send email as before
    smtp_server = st.secrets["smtp"]["server"]
    smtp_port = st.secrets["smtp"]["port"]
    smtp_user = st.secrets["smtp"]["user"]
    smtp_password = st.secrets["smtp"]["password"]
    import random
    reset_code = str(random.randint(100000, 999999))
    if isinstance(user_profile, dict):
        user_profile['reset_code'] = reset_code
        save_user_data(user_id, user_profile)
    msg = MIMEText(f"Hello,\n\nA password reset was requested for your Venture Planner account. Your reset code is: {reset_code}\n\nEnter this code in the app to set a new password. If you did not request this, ignore this message.")
    msg["Subject"] = "Venture Planner Password Reset"
    msg["From"] = smtp_user
    msg["To"] = email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [email], msg.as_string())
        st.success("Password reset code sent. Check your inbox.")
    except Exception as e:
        st.error(f"Failed to send password reset email: {e}")
import streamlit as st
from firebase_utils import get_db, firebase_login, get_user_data, save_user_data
import json, datetime

st.set_page_config(page_title="Venture Creation Planner", layout="wide")

try:
    db_ref = get_db()
except Exception as e:
    st.warning("Firebase not configured. Running in demo mode without data persistence.")
    db_ref = None

# Helper function to write immutable records (blockchain-like ledger)
def write_ledger(user_email, data):
    if db_ref is None:
        st.warning("Demo mode: Data not saved (Firebase not configured)")
        return
    try:
        ref = db_ref.child("venture_plans").push()
        record = {
            "user": user_email,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "data": data
        }
        ref.set(record)
    except Exception as e:
        st.error(f"Failed to save data: {str(e)}")
        st.warning("Running in demo mode - data not persisted")

# --- LOGIN SYSTEM ---
if "user" not in st.session_state:
    st.session_state.user = None

def login(email, password):
    try:
        user_id = firebase_login(email, password).get('localId')
        st.info(f"Debug: user_id = {user_id}")
        if user_id:
            user_profile = get_user_data(user_id)
            st.info(f"Debug: user_profile = {user_profile}")
            if isinstance(user_profile, dict):
                stored_pw = user_profile.get('password')
                if stored_pw is None:
                    st.error("Account exists but no password is set. Please reset your password.")
                    return False
                if stored_pw == password:
                    st.session_state.user = user_profile
                    st.success(f"Welcome back, {user_profile.get('name', email)}")
                    st.session_state.login_success = True
                    return True
                else:
                    st.error("Invalid credentials. (Check user_profile and password field)")
                    return False
            else:
                st.error("User profile data is corrupted or not found. Contact support.")
                return False
        else:
            st.error("Invalid credentials. (Check user_id generation)")
            return False
    except Exception as e:
        st.error(f"Firebase authentication error: {str(e)}")
        st.error("Please check Firebase configuration in Streamlit Cloud secrets.")
        return False

def signup(email, password):
    user_id = firebase_login(email, password).get('localId')
    if user_id:
        user_profile = get_user_data(user_id)
        if user_profile is not None and isinstance(user_profile, dict):
            st.error("Account already exists.")
            return False
        else:
            profile = {
                "email": email,
                "password": password,
                "name": email.split('@')[0],
                "created": datetime.datetime.utcnow().isoformat()
            }
            save_user_data(user_id, profile)
            st.session_state.user = profile
            st.success("Account created. You are now logged in.")
            return True
    else:
        st.error("Signup failed.")
        return False

if not st.session_state.user:
    st.markdown("""
        <style>
        .mil-login {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 2rem 2.5rem;
            box-shadow: 0 0 24px #222, 0 2px 8px #333;
            max-width: 400px;
            margin: 3rem auto;
            color: #e0e0e0;
        }
        .mil-title {
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: 2px;
            color: #00ff99;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .mil-label {
            font-weight: 600;
            color: #00ff99;
        }
        .mil-btn {
            background: linear-gradient(90deg, #00ff99 0%, #0077ff 100%);
            color: #fff;
            font-weight: 700;
            border: none;
            border-radius: 6px;
            padding: 0.7rem 1.5rem;
            margin-top: 1rem;
            width: 100%;
            box-shadow: 0 2px 8px #0077ff44;
        }
        .mil-radio label {
            color: #e0e0e0 !important;
        }
        .mil-link {
            color: #00ff99;
            text-decoration: underline;
            cursor: pointer;
            display: block;
            margin-top: 1rem;
            text-align: right;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="mil-login">', unsafe_allow_html=True)
    st.markdown('<div class="mil-title">🏆 GoldRush Adventures</div>', unsafe_allow_html=True)
    option = st.radio("Select action", ["Login", "Sign Up"], key="mil_radio")
    email = st.text_input("Email", key="mil_email")
    password = st.text_input("Password", type="password", key="mil_password")
    if option == "Login":
        if st.button("Login", key="mil_login_btn"):
            login(email, password)
        # Move Forgot Password button below Login
        forgot = st.button("Forgot Password?", key="mil_forgot_btn")
        if forgot and email:
            user_id = firebase_login(email, "irrelevant").get('localId')
            user_profile = get_user_data(user_id)
            if isinstance(user_profile, dict):
                send_password_reset(email)
                st.session_state.show_code_reset = True
                st.info("Check your email for a password reset code.")
            else:
                st.error("No account found for this email.")
        # Only show code entry if reset requested
        if st.session_state.get("show_code_reset"):
            code_entered = st.text_input("Enter the 6-digit code from your email:", max_chars=6, key="mil_code")
            if code_entered and email:
                user_id = firebase_login(email, "irrelevant").get('localId')
                user_profile = get_user_data(user_id)
                if isinstance(user_profile, dict):
                    reset_code_value = user_profile.get('reset_code')
                    if isinstance(reset_code_value, str) and reset_code_value == code_entered:
                        new_password = st.text_input("Enter new password:", type="password", key="mil_newpw")
                        if st.button("Reset Password", key="mil_resetpw_btn") and new_password:
                            user_profile['password'] = new_password
                            user_profile.pop('reset_code', None)
                            save_user_data(user_id, user_profile)
                            st.success("Password has been reset. You can now log in with your new password.")
                            st.session_state.show_code_reset = False
                    else:
                        st.error("Invalid or expired reset code. Please request a new password reset.")
                else:
                    st.error("User profile error. Contact support.")
    else:
        if st.button("Create Account", key="mil_signup_btn"):
            signup(email, password)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state.get("login_success"):
        st.rerun()
    st.stop()

# --- MAIN APP CONTENT ---
st.title("🚀 Venture Creation Planner")
st.markdown("""
### Welcome to the Gold Rush Adventure Series!
This guided tool will help you **craft your value proposition**, **identify resources**, and **design a 10-step action plan** for your venture idea.

---
""")
st.markdown("""
                ### 🎯 Goals for This Week
By next week, you will:
1. Have a **clear value proposition** using research and testing.
2. Identify your **resources and gaps** (skills, money, partnerships, tech).
3. Outline **10 concrete next steps** to test and grow your idea.
   If you've responded to the 3 Next Steps emailed to you last week, incorporate that feedback here.
4. Save your plan into your **blockchain-like ledger** for accountability and reflection.
""")

# --- SIDEBAR ---
with st.sidebar:
    # User info - check both user object and user_id
    if st.session_state.user and isinstance(st.session_state.user, dict):
        user_email = st.session_state.user.get('email', 'No email found')
        st.info(f"👤 Logged in as: {user_email}")
    else:
        user_id = st.session_state.get('user_id', 'Not logged in')
        st.info(f"👤 User ID: {user_id}")
    
    # Logout button
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.login_success = False
        st.success("Logged out successfully!")
        st.rerun()
    
    st.markdown("---")
    
    # Research Links
    st.markdown("### 📚 Research Resources")
    st.markdown("[📊 Market Research - Statista](https://www.statista.com)")
    st.markdown("[🏢 Industry Reports - IBISWorld](https://www.ibisworld.com)")
    st.markdown("[💡 Startup Ideas - Y Combinator](https://www.ycombinator.com/library)")
    st.markdown("[📈 Business Model Canvas](https://www.strategyzer.com/canvas)")
    st.markdown("[🎯 Customer Development - Steve Blank](https://steveblank.com)")
    
    st.markdown("---")
    
    # AI Consultation
    st.markdown("### 🤖 AI Consultation")
    
    if st.button("💡 Get Idea Feedback", key="ai_feedback"):
        st.info("AI consultation feature coming soon! This will analyze your venture idea and provide feedback.")
    
    if st.button("🎯 Market Analysis", key="ai_market"):
        st.info("AI market analysis coming soon! This will research your target market and competition.")
    
    if st.button("📋 Business Plan Help", key="ai_plan"):
        st.info("AI business plan assistance coming soon! This will help structure your business plan.")
    
    if st.button("💰 Funding Advice", key="ai_funding"):
        st.info("AI funding guidance coming soon! This will suggest funding options for your venture.")


st.markdown("""
### 🎯 Goals for Today
1. Go through this guided planner to start drafting a **clear value proposition**.
2. Use the tool to start identifying your **resources and gaps** (skills, money, partnerships, tech).
3. Use the tool to start outlining your**10 concrete next steps** to test and grow your idea.
4. Save your plan into your **blockchain-like ledger** for accountability and reflection.
""")

with st.expander("📘 TL;DR: Chapter 3 & 4 Recap", expanded=False):
    st.markdown("""

**Chapter 3: Value & Business Models (Gold Creek Lessons)**【71†Chapter3】
- **Value = Benefits – Costs/Risks/Friction.** Customers only buy when they feel the net benefit is worth it.
- **Value Propositions:** Your clear promise to solve a pain or deliver a gain. Examples:
- Zaptoes Mercantile: *“Whatever you need, we’ll make it right—every time.”*
- Iron Mule Express: *“Your goods on time, or your money back.”*
- Black Gold Bakery: *“Fresh bread at quitting time — right where you are.”*
- **Business Models:** How you create, deliver, and capture value. Patterns include direct sales, subscription, platform, freemium, premium, etc.
- **Unit Economics:** CAC (customer acquisition cost), LTV (lifetime value), and payback period are your money math.
- **Defensibility:** Protect your “gold claim” with trust, brand, switching costs, or network effects.
- **Takeaway:** Promise real value, pick a model that fits, and protect your edge.

**Chapter 4: Financial Planning & Break-Even (Gold Creek Ledger Stories)**【70†Chapter4】
- **Financial Planning:** Budget wisely, plan for boom and bust. Don’t be Jed “Boom-or-Bust” Barker (rich in July, broke by December).
- **Key Financial Terms:** Revenue (sales), expenses, profit, assets, liabilities, equity, and cash flow. Profit ≠ cash!
- **Three Essential Statements:**
- Balance Sheet = Snapshot of what you own/owe.
- Income Statement = Movie of revenue, costs, and profit over time.
- Cash Flow Statement = Where cash actually moved.
- **Break-Even Analysis:** Know how many units you must sell before profit begins. Formula:
`Break-even units = Fixed Costs ÷ (Price – Variable Cost)`
- **Interdependence:** Businesses rely on each other (Penelope’s store depends on Doc Boone’s saloon paying bills). Build resilience by diversifying and supporting your ecosystem.
- **Takeaway:** Numbers are your compass. Plan, forecast, and always know your break-even.


""")

# st.markdown("---")

# --- SAVE BUTTON AT TOP ---
st.markdown('---')
if st.button("Save Progress Now", key="save_top"):
    data = {
        "name": st.session_state.get("idea_name", ""),
        "value": st.session_state.get("auto_save_value", {}),
        "value_prop": st.session_state.get("vp_template", ""),
        "resources": st.session_state.get("auto_save_resources", {}),
        "plan": st.session_state.get("auto_save_plan", [])
    }
    if st.session_state.user:
        # Use user_id from session state as identifier since email isn't available
        user_id = st.session_state.get('user_id', 'anonymous_user')
        write_ledger(user_id, data)
        st.success("Progress saved!")
    else:
        st.error("Please log in to save your progress.")

# --- PREPOPULATE & IDEA DROPDOWN ---
idea_options = []
idea_data_map = {}
if st.session_state.user and db_ref is not None:
    try:
        ref = db_ref.child("venture_plans")
        entries = ref.get()
    except Exception as e:
        st.warning("Could not load saved ideas (Firebase error)")
        entries = None
    if entries:
        if isinstance(entries, dict):
            iterable = entries.items()
        elif isinstance(entries, tuple) and len(entries) == 2:
            iterable = [entries]
        else:
            iterable = []
        user_id = st.session_state.get('user_id', 'anonymous_user')
        user_entries = [(key, entry) for key, entry in iterable if entry.get("user") == user_id]
        for key, entry in user_entries:
            label = entry.get("data", {}).get("value_prop", "Idea") or f"Idea {key}"
            idea_options.append(label)
            idea_data_map[label] = entry.get("data", {})
    selected_idea = None
    if idea_options:
        selected_label = st.selectbox("Select a saved idea to view or edit:", idea_options)
        selected_idea = idea_data_map[selected_label]
    else:
        selected_idea = None
else:
    selected_idea = None

# --- IDEA NAME AT TOP ---
idea_name = selected_idea["name"] if selected_idea and "name" in selected_idea else ""
idea_name = st.text_input("Name of Your Idea (for instructor review):", value=idea_name, key="idea_name")

# Utility: clickable bullet choices + optional text input
def question_with_choices(question, options, default_val=""):
    st.markdown(f"**{question}**")
    # Use checkboxes for multi-select, radio for single-select
    # If 'Other (add below)' is present, allow multi-select
    if "Other (add below)" in options or len(options) > 4:
        selected = st.multiselect("Select any that apply:", options, key=question)
    else:
        selected = [st.radio("Select one:", options, key=question)]
    custom = st.text_input("Or add your own:", value=default_val, key=f"{question}_custom")
    return selected, custom

# --- SECTION 1: VALUE & VALUE PROPOSITION ---
st.header("1. Clarify Value & Your Value Proposition")

value_qs = {
    "What problem are you solving?": [
        "High cost of current options",
        "Lack of convenience",
        "Health/safety risks",
        "Time wasted on tasks",
        "Poor quality alternatives",
        "Lack of access/availability",
        "Environmental issues",
        "Unmet emotional needs",
        "Inefficient processes",
        "Other (add below)"
    ],
    "Who exactly experiences this problem (your primary customer segment)?": [
        "College students",
        "Busy professionals",
        "Parents",
        "Small business owners",
        "Tech-savvy early adopters",
        "Low-income households",
        "Rural residents",
        "Specific industry workers",
        "Community organizations",
        "Other (add below)"
    ],
    "What job are they trying to get done (Jobs-to-Be-Done)?": [
        "Save time",
        "Save money",
        "Reduce risk",
        "Feel secure",
        "Gain status",
        "Increase comfort",
        "Improve health",
        "Enjoy entertainment",
        "Build relationships",
        "Other (add below)"
    ]
}

responses_value = {}
for q, opts in value_qs.items():
    # Prepopulate if available
    default_val = selected_idea["value"].get(q) if selected_idea and "value" in selected_idea else ""
    responses_value[q] = question_with_choices(q, opts, default_val=default_val)
    # Auto-save after each question
    st.session_state["auto_save_value"] = responses_value
    if st.session_state.user:
        data = {
            "name": st.session_state.get("idea_name", ""),
            "value": responses_value,
            "value_prop": st.session_state.get("vp_template", ""),
            "resources": st.session_state.get("auto_save_resources", {}),
            "plan": st.session_state.get("auto_save_plan", [])
        }

vp_template = st.text_area(
    "Draft Value Proposition (For [segment] who [problem], [solution] provides [benefit] unlike [alternative] because [proof].)",
    value=selected_idea["value_prop"] if selected_idea and "value_prop" in selected_idea else ""
)
st.session_state["vp_template"] = vp_template

# --- SECTION 2: RESOURCES ---
st.header("2. Identify & Allocate Resources")

resource_qs = {
    "What skills do you (and your team) bring?": [
        "Marketing",
        "Engineering",
        "Sales",
        "Finance",
        "Design",
        "Operations",
        "Networking",
        "Industry expertise",
        "Customer support",
        "Other (add below)"
    ],
    "What physical resources do you already have access to?": [
        "Office space",
        "Equipment/tools",
        "Prototyping materials",
        "Transportation",
        "Technology devices",
        "Distribution network",
        "Supplier contracts",
        "Other (add below)"
    ],
    "What financial resources do you have?": [
        "Personal savings",
        "Friends/family support",
        "Angel investors",
        "Venture capital",
        "Bank loan",
        "Crowdfunding",
        "Grants",
        "Revenue already coming in",
        "Other (add below)"
    ]
}

responses_resources = {}
for q, opts in resource_qs.items():
    default_val = selected_idea["resources"].get(q) if selected_idea and "resources" in selected_idea else ""
    responses_resources[q] = question_with_choices(q, opts, default_val=default_val)
    st.session_state["auto_save_resources"] = responses_resources
    if st.session_state.user:
        data = {
            "name": st.session_state.get("idea_name", ""),
            "value": st.session_state.get("auto_save_value", {}),
            "value_prop": st.session_state.get("vp_template", ""),
            "resources": responses_resources,
            "plan": st.session_state.get("auto_save_plan", [])
        }

# --- SECTION 3: ACTION PLAN ---
st.header("3. Build Your 10 Next Steps")

plan_steps = []
common_steps = [
    "Validate customer need",
    "Build MVP (prototype)",
    "Test with early adopters",
    "Gather customer feedback",
    "Adjust product/service",
    "Develop marketing plan",
    "Secure funding",
    "Assemble team",
    "Launch pilot program",
    "Scale operations"
]
for i in range(1, 11):
    step_default = common_steps[i-1] if i-1 < len(common_steps) else ""
    step_choice = st.selectbox(f"Step {i}", common_steps, index=i-1 if i-1 < len(common_steps) else 0, key=f"step_{i}")
    step_custom = st.text_input(f"Custom Step {i}", value=step_default, key=f"step_custom_{i}")
    plan_steps.append((step_choice, step_custom))
    st.session_state["auto_save_plan"] = plan_steps
    if st.session_state.user:
        data = {
            "name": st.session_state.get("idea_name", ""),
            "value": st.session_state.get("auto_save_value", {}),
            "value_prop": st.session_state.get("vp_template", ""),
            "resources": st.session_state.get("auto_save_resources", {}),
            "plan": plan_steps
        }

# --- SUBMIT & LEDGER ---
st.header("📑 Save Your Venture Plan")
if st.button("Save to Blockchain-like Ledger"):
    data = {
        "name": st.session_state.get("idea_name", ""),
        "value": responses_value,
        "value_prop": vp_template,
        "resources": responses_resources,
        "plan": plan_steps
    }

st.subheader("🔗 Your Saved Blockchain Ledger")
ref = db_ref.child("venture_plans")
entries = ref.get()
if entries:
    # Firebase returns a dict, but sometimes a tuple if only one entry exists
    if isinstance(entries, dict):
        iterable = entries.items()
    elif isinstance(entries, tuple) and len(entries) == 2:
        # Single entry as (key, value)
        iterable = [entries]
    else:
        iterable = []
    for key, entry in iterable:
        entry_user = entry.get("user")
        session_user_id = st.session_state.get('user_id', 'anonymous_user')
        if entry_user == session_user_id:
            st.markdown(f"**Saved on {entry['timestamp']}**")
            st.json(entry["data"])
