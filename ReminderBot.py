#!/usr/bin/python3

import datetime
from pytz import timezone
import discord
import pickle
import asyncio
import os.path

token = open("TOKEN", "r").readline()
channel_id = int(open("CHANNEL_ID", "r").readline())
cet = timezone("CET")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

reminders = []

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    global reminders
    if os.path.isfile("reminders.p"):
        reminders = pickle.load(open("reminders.p", "rb"))
    else:
        reminders = []

    while True:
        for reminder in reminders:
            if reminder["timestamp"] < datetime.datetime.now().timestamp():
                channel = await client.fetch_channel(reminder["channel_id"])
                user = await client.fetch_user(reminder["user_id"])
                await channel.send("{} reminder: {}".format(user.mention, reminder["content"]))
                reminders.remove(reminder)
                pickle.dump(reminders, open("reminders.p", "wb"))
        await asyncio.sleep(30)

@client.event
async def on_message(message):
    content = message.content
    channel = message.channel

    if message.author == client.user:
        return

    if message.channel.id != channel_id:
        return
    
    if content.startswith("$close"):
        await client.close()
        return

    global reminders

    if content.startswith("$rl"):
        if len(reminders) == 0:
            new_content = "No reminders have been set."
        else:
            new_content = ""
            idx = 0
            for reminder in reminders:
                new_content = new_content + "{}: {} (at {})\n".format(str(idx), reminder["content"], str(datetime.datetime.fromtimestamp(reminder["timestamp"], tz=cet))[:-9])
                idx += 1
        await channel.send(content=new_content)
        return

    if content.startswith("$rd"):
        idx = int(content.split(" ")[1])
        reminders.pop(idx)
        pickle.dump(reminders, open("reminders.p", "wb"))
        await channel.send("Deleted reminder {}.".format(idx))
        return

    if content.startswith('$ra') or content.startswith('$rr'):
        if content.startswith("$ra"):
            reminder_time_str = content.split("; ")[0][4:]

            date_str = reminder_time_str.split(" ")[0]
            year = int(date_str.split("-")[0])
            month = int(date_str.split("-")[1])
            day = int(date_str.split("-")[2])

            time_str = reminder_time_str.split(" ")[1]
            hour = int(time_str.split(":")[0])
            minute = int(time_str.split(":")[1])

            datetime_utc = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0)
            datetime_cet = cet.localize(datetime_utc)
            reminder_timestamp = datetime_cet.timestamp()
            
        if content.startswith("$rr"):
            days = 0
            hours = 0
            minutes = 0
            diff_str = content.split("; ")[0][4:]
            for substr in diff_str.split(" "):
                if "w" in substr:
                    days += 7*int(substr[:-1])
                if "d" in substr:
                    days += int(substr[:-1])
                if "h" in substr:
                    hours += int(substr[:-1])
                if "m" in substr:
                    minutes += int(substr[:-1])
            reminder_time = datetime.datetime.now()+datetime.timedelta(days=days, hours=hours, minutes=minutes)
            reminder_time = datetime.datetime(year=reminder_time.year, month=reminder_time.month, day=reminder_time.day, hour=reminder_time.hour, minute=reminder_time.minute, second=0, microsecond=0)
            reminder_timestamp = reminder_time.timestamp()
        
        reminder_content = content.split("; ")[1]

        reminders.append({"content": reminder_content, 
                    "user_id": message.author.id,
                    "channel_id": channel.id,
                    "timestamp": reminder_timestamp})
        pickle.dump(reminders, open("reminders.p", "wb"))
        await channel.send("Set reminder for {}.".format(str(datetime.datetime.fromtimestamp(reminder_timestamp, tz=cet))[:-9]))
        return
    
    await channel.send("Not a command.")

client.run(token)
