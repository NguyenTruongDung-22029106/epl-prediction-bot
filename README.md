# LOL Discord Bot (Python)

Project scaffold for a Discord bot that fetches League of Legends data from Riot API.

Files:
- `lol_bot.py` - main bot file with commands: `!profile`, `!livegame`, `!matchhistory`
- `requirements.txt` - dependencies
- `.env.example` - example environment variables file

Quickstart:
1. Create virtualenv and install deps:
   python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt
2. Copy `.env.example` to `.env` and fill your tokens.
3. Run:
   python lol_bot.py

Notes:
- Do not commit `.env` to version control.
- Ensure your Riot API key has allowed access.
