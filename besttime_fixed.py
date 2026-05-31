import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from pyrogram import Client, filters

# =====================================
# CONFIG
# =====================================


# =====================================
# LOGGING
# =====================================

logging.basicConfig(level=logging.CRITICAL)

# =====================================
# CLIENT
# =====================================

import os

app = Client(
    "stable-userbot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    session_string=os.getenv("SESSION_STRING")
)

tasks = {}
paused = False

def convert_time(value, unit):
    unit = unit.lower()
    if unit == "sec":
        return value
    elif unit == "min":
        return value * 60
    elif unit == "hour":
        return value * 3600
    return None

async def repeat_loop(chat_id, text, total_time):
    global paused
    start_time = asyncio.get_event_loop().time()

    while True:
        try:
            if paused:
                await asyncio.sleep(1)
                continue

            if asyncio.get_event_loop().time() - start_time >= total_time:
                tasks.pop(chat_id, None)
                await app.send_message(chat_id, "✅ Repeat Finished")
                break

            await app.send_message(chat_id, text)
            await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Repeat Error: {e}")
            await asyncio.sleep(2)

@app.on_message(filters.me & filters.command("dm", prefixes="/"))
async def dm_sender(client, message):
    try:
        args = message.text.split(maxsplit=3)

        if len(args) < 4:
            return await message.reply("Usage:\n/dm HH:MM:SS username text")

        target_time = args[1]
        user_id = args[2]
        text = args[3]

        tz = ZoneInfo("Asia/Kolkata")
        now = datetime.now(tz)

        target = datetime.strptime(target_time, "%H:%M:%S").replace(
            year=now.year,
            month=now.month,
            day=now.day,
            tzinfo=tz
        )

        wait_time = (target - now).total_seconds()

        if wait_time <= 0:
            wait_time += 86400  # next day

        await message.reply(
            f"⏳ Scheduled\n\n👤 User: {user_id}\n🕒 Time: {target_time}\n💬 Message: {text}"
        )

        await asyncio.sleep(wait_time)
        await client.get_users(user_id)
        await client.send_message(user_id, text)

        await message.reply("✅ DM Sent")

    except Exception as e:
        await message.reply(f"Error:\n{e}")

print("🔥 Stable Userbot Started")
app.run()
