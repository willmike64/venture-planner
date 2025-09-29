import streamlit as st # type: ignore
from streamlit_drawable_canvas import st_canvas

# Layout for Gold Creek Town Map
BUILDINGS = [
    {"name": "Stable", "x": 50, "y": 100, "tooltip": "Your horse stable"},
    {"name": "Race Track", "x": 200, "y": 80, "tooltip": "Enter a race"},
    {"name": "Betting Hall", "x": 350, "y": 120, "tooltip": "Place a bet"},
    {"name": "Auction House", "x": 100, "y": 250, "tooltip": "Buy or sell horses"},
    {"name": "Pete's Office", "x": 270, "y": 220, "tooltip": "Talk to Pete the AI Advisor"},
    {"name": "Business HQ", "x": 400, "y": 200, "tooltip": "Manage stable finances"},
    {"name": "Jockey Hall", "x": 180, "y": 300, "tooltip": "Meet your jockeys"}
]

# Simulated navigation keys (could be used to sync tab routing)
NAV_KEYS = {
    "Stable": 0,
    "Race Track": 1,
    "Business HQ": 2,
    "Jockey Hall": 3,
    "Betting Hall": 4,
    "Auction House": 5,
    "Pete's Office": 6
}

def render_town_map():
    st.header("🗺️ Gold Creek Town Map")

    st.markdown("Click on a building to navigate to that area.")

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # semi-transparent orange
        stroke_width=2,
        stroke_color="#000000",
        background_color="#f3e9dc",
        height=400,
        width=500,
        drawing_mode="transform",
        key="town_canvas",
        initial_drawing={
            "version": "4.4.0",
            "objects": [
                {
                    "type": "circle",
                    "left": b["x"],
                    "top": b["y"],
                    "radius": 20,
                    "fill": "#FFD700",
                    "stroke": "#8B4513",
                    "name": b["name"]
                } for b in BUILDINGS
            ]
        }
    )

    st.markdown("### 🏘️ Hover Tooltips")
    for b in BUILDINGS:
        st.markdown(f"- **{b['name']}**: {b['tooltip']}")

    if canvas_result.json_data and "objects" in canvas_result.json_data:
        clicked_obj = canvas_result.json_data.get("objects", [])[0]
        clicked_name = clicked_obj.get("name") if clicked_obj else None
        if clicked_name and clicked_name in NAV_KEYS:
            st.session_state["selected_tab"] = NAV_KEYS[clicked_name]
            st.success(f"Navigating to: {clicked_name}")