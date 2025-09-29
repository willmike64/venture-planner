🎮 Gold Creek Stables & Horse Racing Game

🏁 FEATURES:
- Stable management (buy, train, breed, sell)
- Horse races with AI jockeys, live results, betting system
- Auction house for player-to-player trading
- Business dashboard (P&L, loans, achievements)
- Pete the AI Advisor (5 personalities)
- Parimutuel betting with auto-payout
- Firebase for persistence
- OpenAI for NPC intelligence

📦 INSTALLATION
1. Create a virtual environment:
  sour
   source venv/bin/activate  # or venv\Scripts\activate on Windows

2. Install dependencies:
   pip install streamlit openai firebase-admin plotly pandas

3. Add `secrets.toml` in `.streamlit/` folder:
   ```
   [general]
   email = "your@email.com"

   [firebase]
   type = "service_account"
   project_id = "..."
   private_key = "..."
   ...
   OPENAI_API_KEY = "your-openai-key"
   ```

4. Run the app:
   streamlit run app.py

💡 Optional:
- Add sample data to Firebase for races and auctions
- Customize personalities or achievements in code
