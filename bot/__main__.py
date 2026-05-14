# Dummy Flask server for Render
import os
import asyncio
import sys

# Critical Patch for Python 3.10+ / 3.14 event loop issue
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running fine."

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Start Flask in background
threading.Thread(target=run).start()

# Now import and run the bot
from bot import Bot

if __name__ == '__main__':
    Bot().run()
