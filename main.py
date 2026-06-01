import asyncio

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
    
import logging

from pyrogram import Client, filters

from datetime import datetime
from zoneinfo import ZoneInfo


# =====================================
# CONFIG
# =====================================

import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# =====================================
# LOGGING
# =====================================

logging.basicConfig(level=logging.CRITICAL)

# =====================================
# CLIENT
# =====================================

app = Client(
    "stable-userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# =====================================
# STORAGE
# =====================================

tasks = {}
paused = False

# =====================================
# TIME CONVERTER
# =====================================

def convert_time(value, unit):

    unit = unit.lower()

    if unit == "sec":
        return value

    elif unit == "min":
        return value * 60

    elif unit == "hour":
        return value * 3600

    else:
        return None

# =====================================
# REPEAT LOOP
# =====================================

async def repeat_loop(chat_id, text, total_time):

    global paused

    start_time = asyncio.get_event_loop().time()

    while True:

        try:

            if paused:
                await asyncio.sleep(1)
                continue

            current_time = asyncio.get_event_loop().time()

            # stop after total duration
            if current_time - start_time >= total_time:

                if chat_id in tasks:
                    del tasks[chat_id]

                await app.send_message(
                    chat_id,
                    "✅ Repeat Finished"
                )

                break

            # send message
            await app.send_message(chat_id, text)

            # 0.5 sec delay
            await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            break

        except Exception as e:
            print(f"Repeat Error: {e}")
            await asyncio.sleep(2)

# =====================================
# REPEAT COMMAND
# =====================================

@app.on_message(filters.me & filters.command("repeat", prefixes="."))
async def repeat_cmd(client, message):

    try:

        # Example:
        # .repeat 10 min hello

        args = message.text.split(maxsplit=3)

        if len(args) < 4:
            return await message.reply(
                "Usage:\n.repeat 10 min hello"
            )

        time_value = int(args[1])
        time_unit = args[2]
        text = args[3]

        total_time = convert_time(time_value, time_unit)

        if total_time is None:
            return await message.reply(
                "❌ Use: sec / min / hour"
            )

        chat_id = message.chat.id

        # stop old task
        if chat_id in tasks:
            tasks[chat_id].cancel()

        # create new task
        task = asyncio.create_task(
            repeat_loop(chat_id, text, total_time)
        )

        tasks[chat_id] = task

        await message.reply(
            f"✅ Repeat Started\n\n"
            f"⏱ Duration: {time_value} {time_unit}\n"
            f"⚡ Delay: 0.5 sec\n"
            f"💬 Text: {text}"
        )

    except Exception as e:
        await message.reply(f"Error:\n{e}")

# =====================================
# STOP
# =====================================

@app.on_message(filters.me & filters.command("stop", prefixes="."))
async def stop_cmd(client, message):

    stopped = 0

    for chat_id in list(tasks.keys()):

        tasks[chat_id].cancel()
        del tasks[chat_id]

        stopped += 1

    await message.reply(
        f"🛑 Stopped {stopped} tasks"
    )

# =====================================
# STATUS
# =====================================

@app.on_message(filters.me & filters.command("status", prefixes="."))
async def status_cmd(client, message):

    txt = (
        f"📊 STATUS\n\n"
        f"🔁 Active Tasks: {len(tasks)}\n"
        f"⏸ Paused: {paused}"
    )

    await message.reply(txt)

# =====================================
# PAUSE
# =====================================

@app.on_message(filters.me & filters.command("pause", prefixes="."))
async def pause_cmd(client, message):

    global paused

    paused = True

    await message.reply("⏸ Paused")

# =====================================
# RESUME
# =====================================

@app.on_message(filters.me & filters.command("resume", prefixes="."))
async def resume_cmd(client, message):

    global paused

    paused = False

    await message.reply("▶️ Resumed")

# =====================================
# PRECISE DM
# =====================================

@app.on_message(filters.me & filters.command("dm", prefixes="/"))
async def dm_sender(client, message):

    try:

        # Example:
        # /dm 15:40:30 @username hello

        args = message.text.split(maxsplit=3)

        if len(args) < 4:
            return await message.reply(
                "Usage:\n/dm HH:MM:SS username text"
            )

        target_time = args[1]
        user_id = args[2]
        text = args[3]

        # Indian Time
        tz = ZoneInfo("Asia/Kolkata")
        now = datetime.now(tz)

        target = datetime.strptime(
            target_time,
            "%H:%M:%S"
        )
        
        target = target.replace(
            year=now.year,
            month=now.month,
            day=now.day,
            tzinfo=tz
        )

        wait_time = (target - now).total_seconds()

        if wait_time <= 0:
            wait_time += 86400
            

        await message.reply(
            f"⏳ Scheduled\n\n"
            f"👤 User: {user_id}\n"
            f"🕒 Time: {target_time}\n"
            f"💬 Message: {text}"
        )

        # exact sleep
        await asyncio.sleep(wait_time)

        # resolve peer
        await client.get_users(user_id)

        # send message
        await client.send_message(
            user_id,
            text
        )

        await message.reply("✅ DM Sent")

    except Exception as e:

        await message.reply(
            f"Error:\n{e}"
        )
        
# =====================================
# HELP
# =====================================

@app.on_message(filters.me & filters.command("help", prefixes="."))
async def help_cmd(client, message):

    txt = """
🔥 USERBOT COMMANDS

.repeat 10 min hello
.repeat 30 sec hi
.repeat 1 hour gm

.stop
.status
.pause
.resume

24-hour format only

Example:
/dm 15:30:00 @user hello
"""

    await message.reply(txt)

# =====================================
# START
# =====================================

print("🔥 Stable Userbot Started")

try:
    app.run()

except Exception as e:
    print(e)
 
