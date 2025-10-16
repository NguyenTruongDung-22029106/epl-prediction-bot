Render deployment notes:

1. Push this repo to GitHub.
2. On Render, create a new Web Service and connect the repo.
3. Build Command: pip install -r requirements.txt
4. Start Command: python lol_bot.py
5. In Environment, add DISCORD_TOKEN and RIOT_API_KEY.
6. Select Free instance if appropriate.

Notes: If the bot requires persistent websocket connection, choose a Web Service; ensure your bot handles reconnections gracefully.
