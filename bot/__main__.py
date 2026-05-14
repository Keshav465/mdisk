import os
import asyncio
import sys

# Critical Patch for Python 3.10+ / 3.14 event loop issue
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from bot import Bot

if __name__ == '__main__':
    Bot().run()
