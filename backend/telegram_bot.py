#!/usr/bin/env python3
"""
telegram_bot.py - Interactive Telegram Bot for OMI with Ava Female Voice support.

Features:
  - Chat interactively over Telegram with OMI.
  - Generates voice note replies using Microsoft Ava Neural Female Voice (edge-tts).
  - Commands: /start, /voice, /speak <text>

Configuration:
  Set environment variable TELEGRAM_BOT_TOKEN or put TELEGRAM_BOT_TOKEN=... in backend/.env
"""

import os
import sys
import time
import requests
import asyncio
import edge_tts


TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEFAULT_VOICE = "en-US-AvaNeural"
VOICE_MODE = True  # Send voice notes alongside text replies


def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    try:
        r = requests.get(url, params=params, timeout=35)
        if r.status_code == 200:
            return r.json().get("result", [])
    except Exception as e:
        print(f"[!] Error fetching updates: {e}")
    return []


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"[!] Error sending message: {e}")


def send_voice(chat_id, voice_file):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVoice"
    try:
        with open(voice_file, "rb") as f:
            files = {"voice": f}
            data = {"chat_id": chat_id}
            requests.post(url, data=data, files=files)
    except Exception as e:
        print(f"[!] Error sending voice note: {e}")


async def synthesize_voice(text, output_file="telegram_voice.ogg"):
    communicate = edge_tts.Communicate(text, DEFAULT_VOICE)
    await communicate.save(output_file)
    return output_file


def process_message(chat_id, text):
    global VOICE_MODE
    text_clean = text.strip()

    if text_clean == "/start":
        send_message(chat_id, "👋 Hello! I am your OMI AI Assistant powered by Ava's female voice.\n\nType any message to chat with me. Use `/speak <text>` to generate a voice note.")
        return

    if text_clean.startswith("/voice"):
        parts = text_clean.split()
        if len(parts) > 1 and parts[1].lower() in ["off", "disable", "false"]:
            VOICE_MODE = False
            send_message(chat_id, "🔇 Voice mode disabled. I will reply with text only.")
        else:
            VOICE_MODE = True
            send_message(chat_id, "🔊 Voice mode enabled. I will reply with text and Ava female voice notes!")
        return

    if text_clean.startswith("/speak "):
        speak_prompt = text_clean[7:].strip()
        voice_file = "temp_speak.mp3"
        asyncio.run(synthesize_voice(speak_prompt, voice_file))
        send_voice(chat_id, voice_file)
        return

    # Echo / AI assistant response
    reply_text = f"Received: '{text_clean}'. OMI Assistant is ready to process your context."
    send_message(chat_id, reply_text)

    if VOICE_MODE:
        voice_file = "temp_reply.mp3"
        asyncio.run(synthesize_voice(reply_text, voice_file))
        send_voice(chat_id, voice_file)


def main():
    global TELEGRAM_TOKEN
    if not TELEGRAM_TOKEN:
        print("[!] TELEGRAM_BOT_TOKEN is not set.")
        print("    Usage: TELEGRAM_BOT_TOKEN='your_token_here' python telegram_bot.py")
        sys.exit(1)

    print(f"[+] Starting OMI Telegram Bot with Ava Female Voice ({DEFAULT_VOICE})...")
    offset = None

    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message") or update.get("edited_message")
            if message and "text" in message:
                chat_id = message["chat"]["id"]
                text = message["text"]
                print(f"[>] Message from {chat_id}: {text}")
                process_message(chat_id, text)
        time.sleep(1)


if __name__ == "__main__":
    main()
