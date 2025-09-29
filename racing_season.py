# racing_season.py - 15-Week Racing Season with Kentucky Derby Path
import streamlit as st
import random
from datetime import datetime, timedelta

# 15-Week Racing Season Structure
RACING_SEASON = {
    1: {"name": "Season Opener", "type": "maiden", "purse": 10000, "points": [10, 6, 4, 2]},
    2: {"name": "Allowance Stakes", "type": "allowance", "purse": 15000, "points": [15, 10, 6, 4]},
    3: {"name": "Golden Cup Prep", "type": "prep", "purse": 25000, "points": [25, 15, 10, 5]},
    4: {"name": "Winter Stakes", "type": "stakes", "purse": 50000, "points": [50, 30, 20, 10]},
    5: {"name": "Spring Maiden", "type": "maiden", "purse": 20000, "points": [20, 12, 8, 4]},
    6: {"name": "Derby Prep I", "type": "derby_prep", "purse": 100000, "points": [100, 60, 40, 20]},
    7: {"name": "Louisiana Derby", "type": "graded_stakes", "purse": 150000, "points": [150, 90, 60, 30]},
    8: {"name": "Florida Derby", "type": "graded_stakes", "purse": 200000, "points": [200, 120, 80, 40]},
    9: {"name": "Derby Prep II", "type": "derby_prep", "purse": 175000, "points": [175, 105, 70, 35]},
    10: {"name": "Wood Memorial", "type": "graded_stakes", "purse": 250000, "points": [250, 150, 100, 50]},
    11: {"name": "Blue Grass Stakes", "type": "graded_stakes", "purse": 300000, "points": [300, 180, 120, 60]},
    12: {"name": "Arkansas Derby", "type": "graded_stakes", "purse": 350000, "points": [350, 210, 140, 70]},
    13: {"name": "Derby Trial", "type": "derby_prep", "purse": 75000, "points": [75, 45, 30, 15]},
    14: {"name": "Kentucky Derby", "type": "triple_crown", "purse": 3000000, "points": [3000, 1800, 1200, 600]},
    15: {"name": "Preakness Stakes", "type": "triple_crown", "purse": 1500000, "points": [1500, 900, 600, 300]}
}

# Derby Qualification Requirements
DERBY_QUALIFICATION = {
    "points_required": 40,  # Need at least 40 points to qualify
    "max_field": 20,       # Maximum 20 horses in Derby field
    "graded_stakes_wins": 1,  # Need at least 1 graded stakes win recommended
}

# Achievement Badges for Racing Milestones
RACING_ACHIEVEMENTS = {
    "First Win": {"description": "Win your first race", "icon": "🏆", "points": 10},
    "Stakes Winner": {"description": "Win a stakes race", "icon": "⭐", "points": 50},
    "Graded Stakes Winner": {"description": "Win a graded stakes race", "icon": "🌟", "points": 100},
    "Derby Qualifier": {"description": "Qualify for the Kentucky Derby", "icon": "🎯", "points": 200},
    "Derby Winner": {"description": "Win the Kentucky Derby", "icon": "👑", "points": 1000},
    "Triple Crown Winner": {"description": "Win all three Triple Crown races", "icon": "💎", "points": 5000},
    "Hall of Fame": {"description": "Career earnings over $1,000,000", "icon": "🏛️", "points": 2000}
}

def get_current_race_week():
    """Get the current race week (1-15)"""
    if 'race_season_week' not in st.session_state:
        st.session_state.race_season_week = 1
    return st.session_state.race_season_week

def advance_race_week():
    """Advance to the next week in the racing season"""
    current_week = get_current_race_week()
    if current_week < 15:
        st.session_state.race_season_week = current_week + 1
        return True
    else:
        # Season complete, reset to week 1
        st.session_state.race_season_week = 1
        return False

def get_current_race():
    """Get information about the current race"""
    week = get_current_race_week()
    return RACING_SEASON.get(week, RACING_SEASON[1])

def calculate_derby_points(horse_name, finishing_position, race_week):
    """Calculate derby points earned for a finishing position"""
    from firebase_utils import save_user_data, get_user_data
    
    race_info = RACING_SEASON.get(race_week, {})
    points_distribution = race_info.get('points', [0, 0, 0, 0])
    
    if finishing_position <= len(points_distribution):
        points = points_distribution[finishing_position - 1]
        
        # Get current user ID
        user_id = st.session_state.get('user_id', 'default_user')
        
        # Load existing derby points from Firebase
        user_data = get_user_data(user_id) or {}
        if not isinstance(user_data, dict):
            user_data = {}
        
        derby_points = user_data.get('derby_points', {})
        if not isinstance(derby_points, dict):
            derby_points = {}
        
        # Update horse's derby points
        if horse_name not in derby_points:
            derby_points[horse_name] = 0
        
        derby_points[horse_name] += points
        
        # Save back to Firebase
        user_data['derby_points'] = derby_points
        save_user_data(user_id, user_data)
        
        # Also update session state for immediate use
        if 'derby_points' not in st.session_state:
            st.session_state.derby_points = {}
        st.session_state.derby_points[horse_name] = derby_points[horse_name]
        
        return points
    
    return 0

def get_derby_leaderboard():
    """Get current Derby points leaderboard"""
    from firebase_utils import get_user_data
    
    # Load derby points from Firebase for current user
    user_id = st.session_state.get('user_id', 'default_user')
    user_data = get_user_data(user_id) or {}
    if not isinstance(user_data, dict):
        user_data = {}
    if not isinstance(user_data, dict):
        user_data = {}
    points = user_data.get('derby_points', {})
    if not isinstance(points, dict):
        points = {}
    
    # Update session state with loaded points
    st.session_state.derby_points = points
    
    # Sort by points (highest first)
    leaderboard = sorted(points.items(), key=lambda x: x[1], reverse=True)
    return leaderboard

def is_derby_qualified(horse_name):
    """Check if a horse is qualified for the Kentucky Derby"""
    from firebase_utils import get_user_data
    
    # Load derby points from Firebase
    user_id = st.session_state.get('user_id', 'default_user')
    user_data = get_user_data(user_id) or {}
    
    # Ensure user_data is a dictionary and derby_points is a dictionary
    if not isinstance(user_data, dict):
        user_data = {}
    
    derby_points_data = user_data.get('derby_points', {})
    if not isinstance(derby_points_data, dict):
        derby_points_data = {}
    
    points = derby_points_data.get(horse_name, 0)
    return points >= DERBY_QUALIFICATION['points_required']

def get_qualified_horses():
    """Get list of horses qualified for Kentucky Derby"""
    from firebase_utils import get_user_data
    
    # Load derby points from Firebase
    user_id = st.session_state.get('user_id', 'default_user')
    user_data = get_user_data(user_id) or {}
    if not isinstance(user_data, dict):
        user_data = {}
    points = user_data.get('derby_points', {})
    if not isinstance(points, dict):
        points = {}
    qualified = []
    
    for horse_name, pts in points.items():
        if pts >= DERBY_QUALIFICATION['points_required']:
            qualified.append((horse_name, pts))
    
    # Sort by points (highest first) and limit to field size
    qualified.sort(key=lambda x: x[1], reverse=True)
    return qualified[:DERBY_QUALIFICATION['max_field']]

def check_racing_achievements(horse_name, finishing_position, race_type, career_earnings=0):
    """Check and award racing achievements"""
    if 'racing_achievements' not in st.session_state:
        st.session_state.racing_achievements = {}
    
    if horse_name not in st.session_state.racing_achievements:
        st.session_state.racing_achievements[horse_name] = []
    
    achievements = st.session_state.racing_achievements[horse_name]
    new_achievements = []
    
    # First Win
    if finishing_position == 1 and "First Win" not in achievements:
        achievements.append("First Win")
        new_achievements.append("First Win")
    
    # Stakes Winner
    if finishing_position == 1 and race_type in ["stakes", "graded_stakes", "derby_prep"] and "Stakes Winner" not in achievements:
        achievements.append("Stakes Winner")
        new_achievements.append("Stakes Winner")
    
    # Graded Stakes Winner
    if finishing_position == 1 and race_type == "graded_stakes" and "Graded Stakes Winner" not in achievements:
        achievements.append("Graded Stakes Winner")
        new_achievements.append("Graded Stakes Winner")
    
    # Derby Qualifier
    if is_derby_qualified(horse_name) and "Derby Qualifier" not in achievements:
        achievements.append("Derby Qualifier")
        new_achievements.append("Derby Qualifier")
    
    # Derby Winner
    if finishing_position == 1 and race_type == "triple_crown" and get_current_race()['name'] == "Kentucky Derby" and "Derby Winner" not in achievements:
        achievements.append("Derby Winner")
        new_achievements.append("Derby Winner")
    
    # Hall of Fame (career earnings)
    if career_earnings >= 1000000 and "Hall of Fame" not in achievements:
        achievements.append("Hall of Fame")
        new_achievements.append("Hall of Fame")
    
    return new_achievements

def render_racing_season_sidebar():
    """Render the racing season information in sidebar"""
    st.markdown("## 🏁 **Racing Season**")
    
    current_week = get_current_race_week()
    current_race = get_current_race()
    
    # Current race info
    st.write(f"**Week {current_week}/15**")
    st.write(f"🏆 **{current_race['name']}**")
    st.write(f"💰 **Purse:** ${current_race['purse']:,}")
    
    # Race type indicator
    race_types = {
        "maiden": "🔰 Maiden",
        "allowance": "📈 Allowance", 
        "stakes": "⭐ Stakes",
        "prep": "🎯 Prep Race",
        "derby_prep": "🏇 Derby Prep",
        "graded_stakes": "🌟 Graded Stakes",
        "triple_crown": "👑 Triple Crown"
    }
    race_type_display = race_types.get(current_race['type'], current_race['type'])
    st.write(f"**Type:** {race_type_display}")
    
    # Derby points for top 4
    points = current_race.get('points', [0, 0, 0, 0])
    st.write(f"**Derby Points:** {points[0]}-{points[1]}-{points[2]}-{points[3]}")
    
    # Next race button
    if st.button("⏭️ Next Week", key="advance_week"):
        advance_race_week()
        st.rerun()

def calculate_derby_points_from_race_history():
    """Calculate Derby points for all horses from the complete race history"""
    from firebase_utils import load_race_records
    
    # Load all race records
    race_records = load_race_records(limit=200)  # Get more races for comprehensive analysis
    
    # Track points for each horse
    horse_derby_points = {}
    
    # Process each race
    for race_id, race_data in race_records.items():
        if not isinstance(race_data, dict):
            continue
            
        # Get race week and results
        race_week = race_data.get('race_week', 1)
        race_results = race_data.get('results', [])  # Fixed: use 'results' not 'race_results'
        
        # Get points distribution for this race week
        race_info = RACING_SEASON.get(race_week, {})
        points_distribution = race_info.get('points', [0, 0, 0, 0])
        
        # Award points based on finishing positions
        for horse_result in race_results:
            if isinstance(horse_result, dict):
                # Get position and horse name from the result
                position = horse_result.get('position', 999)
                horse_name = horse_result.get('name', '')  # Fixed: use 'name' not 'horse_name'
                
                if horse_name and position <= len(points_distribution):
                    # Clean horse name (remove owner suffixes)
                    clean_name = horse_name.replace(' (Your Horse)', '').strip()
                    
                    # Get points for this position
                    points = points_distribution[position - 1]
                    
                    if clean_name not in horse_derby_points:
                        horse_derby_points[clean_name] = 0
                    horse_derby_points[clean_name] += points
    
    return horse_derby_points

def get_global_derby_leaderboard():
    """Get comprehensive Derby points leaderboard from race history"""
    
    # Calculate points from all race records
    all_derby_points = calculate_derby_points_from_race_history()
    
    # Sort by points (highest first)
    leaderboard = sorted(all_derby_points.items(), key=lambda x: x[1], reverse=True)
    
    return leaderboard

def render_derby_qualification_status():
    """Render Derby qualification status"""
    st.markdown("### 🎯 Derby Qualification Leaderboard")
    
    # Show user's horses first
    leaderboard = get_derby_leaderboard()
    qualified_horses = get_qualified_horses()
    
    # Get global leaderboard
    global_leaderboard = get_global_derby_leaderboard()
    global_qualified = [horse for horse, points in global_leaderboard if points >= DERBY_QUALIFICATION['points_required']]
    
    st.write(f"**Qualification Requirement:** {DERBY_QUALIFICATION['points_required']} points")
    st.write(f"**Global Derby Field Size:** {len(global_qualified)}/{DERBY_QUALIFICATION['max_field']}")
    
    # Show comprehensive Derby standings
    if global_leaderboard:
        st.write(f"**Derby Field Status:** {len(global_qualified)}/{DERBY_QUALIFICATION['max_field']} horses qualified")
        
        # Get current user's horses for highlighting
        user_stable_horses = st.session_state.get('stable_horses', {})
        user_horse_names = set(user_stable_horses.keys())
        
        st.markdown("#### 🏆 Top 20 Derby Contenders")
        st.markdown("*Based on complete race history analysis*")
        
        # Show top 20 horses with detailed info
        for i, (horse_name, points) in enumerate(global_leaderboard[:20], 1):
            status = "✅ QUALIFIED" if points >= DERBY_QUALIFICATION['points_required'] else "❌"
            
            # Check if this is the current user's horse
            is_user_horse = horse_name in user_horse_names
            
            if is_user_horse:
                # Highlight user's horses
                st.markdown(f"**{i}. 🌟 {horse_name} (YOUR HORSE)** - {points} pts {status}")
            else:
                # Regular formatting for other horses
                if points >= DERBY_QUALIFICATION['points_required']:
                    st.markdown(f"**{i}. {horse_name}** - {points} pts {status}")
                else:
                    st.write(f"{i}. {horse_name} - {points} pts {status}")
        
        # Show summary stats
        if global_leaderboard:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_horses = len(global_leaderboard)
                st.metric("🐎 Total Horses Racing", total_horses)
            
            with col2:
                qualified_count = len(global_qualified)
                st.metric("✅ Qualified for Derby", qualified_count)
                
            with col3:
                user_qualified = sum(1 for horse_name, points in global_leaderboard 
                                   if horse_name in user_horse_names and points >= DERBY_QUALIFICATION['points_required'])
                st.metric("🌟 Your Qualified Horses", user_qualified)
        
        # Show cutoff info
        if len(global_leaderboard) > DERBY_QUALIFICATION['max_field']:
            cutoff_points = global_leaderboard[DERBY_QUALIFICATION['max_field'] - 1][1]
            st.info(f"💡 **Derby Field Cutoff**: Currently {cutoff_points} points needed to make the field")
        
    else:
        st.info("No race history found yet. Complete some races to build the Derby leaderboard!")

def render_racing_achievements():
    """Render racing achievements"""
    st.markdown("### 🏅 Racing Achievements")
    
    achievements = st.session_state.get('racing_achievements', {})
    
    if achievements:
        for horse_name, horse_achievements in achievements.items():
            if horse_achievements:  # Only show horses with achievements
                st.write(f"**{horse_name}:**")
                for achievement in horse_achievements:
                    achievement_info = RACING_ACHIEVEMENTS.get(achievement, {})
                    icon = achievement_info.get('icon', '🏆')
                    description = achievement_info.get('description', achievement)
                    st.write(f"  {icon} {description}")
    else:
        st.info("No racing achievements earned yet. Win races to earn achievements!")

def get_season_progress_percentage():
    """Get the current season progress as a percentage"""
    current_week = get_current_race_week()
    return min((current_week / 15) * 100, 100)

def is_derby_week():
    """Check if current week is Kentucky Derby week"""
    current_race = get_current_race()
    return current_race['name'] == "Kentucky Derby"

def is_triple_crown_race():
    """Check if current race is a Triple Crown race"""
    current_race = get_current_race()
    return current_race['type'] == "triple_crown"

# Entry point for testing
if __name__ == "__main__":
    st.title("🏁 Racing Season System")
    render_racing_season_sidebar()
    render_derby_qualification_status()
    render_racing_achievements()