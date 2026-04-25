import telebot
from telebot import types
import requests
import os
import threading
import time
import re

# --- CONFIG ---
API_TOKEN = os.environ.get('API_TOKEN')
CLAUDE_KEY = os.environ.get('CLAUDE_KEY')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
GAME_URL = 'https://13l.buzz/register?inviteCode=HZAJL3N&from=web'
NETLIFY_TOOL = 'https://bright-cascaron-1ca231.netlify.app/'

bot = telebot.TeleBot(API_TOKEN)
user_referrals = {}

# --- Bad Words List ---
BAD_WORDS = [
    'bc', 'mc', 'bsdk', 'chutiya', 'madarchod', 'behenchod',
    'randi', 'harami', 'kamina', 'gandu', 'bhosdi', 'sala',
    'saala', 'ullu', 'bakwaas', 'ch*t', 'bh*d', 'lund', 'gaand'
]

# --- Link Detect ---
def has_link(text):
    pattern = r'(https?://|www\.|t\.me/|@\w+)'
    return bool(re.search(pattern, text, re.IGNORECASE))

# --- Bad Word Detect ---
def has_bad_word(text):
    text_lower = text.lower()
    return any(word in text_lower for word in BAD_WORDS)

# --- Smart AI Reply ---
def get_ai_reply(user_text, username="User"):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 300,
        "messages": [{
            "role": "user",
            "content": f"""Tu ek smart aur helpful Telegram assistant hai.
User ka naam: {username}
User ka sawaal: {user_text}

Rules:
- Hinglish mein jawab do (Hindi + English mix)
- Smart aur helpful reply do
- Agar koi problem hai toh solution bhi do
- Short aur clear rakho (max 3-4 lines)
- Friendly aur positive tone rakho
- Agar koi personal ya sensitive sawaal ho toh politely avoid karo"""
        }]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['content'][0]['text']
    except:
        return "⚠️ Abhi thodi dikkat hai bhai, thodi der baad try karo! 🙏"

# --- Scheduled Channel Posts ---
def scheduled_posts():
    messages = [
        "🌅 Good Morning sabko! Aaj ka din productive aur acha banao! 💪✨",
        "💡 Smart Tip: Mehnat ke saath dimaag bhi lagao — success zaroor milegi! 🎯",
        "☀️ Dopahar ho gayi! Thoda break lo, paani piyo aur fresh ho jao! 💧",
        "🔥 Yaad rakho: Har problem ka solution hota hai — bas himmat mat haro! 💪",
        "🌙 Good Night sabko! Aaj jo kiya achha kiya, kal aur behtar karenge! ⭐",
        "🤖 Koi bhi sawaal ho? Bot se poochho — hamesha ready hoon madad ke liye! 😊"
    ]
    i = 0
    while True:
        try:
            if CHANNEL_ID:
                bot.send_message(CHANNEL_ID, messages[i % len(messages)])
                print(f"✅ Channel post sent: {i+1}")
            i += 1
        except Exception as e:
            print(f"❌ Channel error: {e}")
        time.sleep(14400)  # Har 4 ghante mein

# --- /start Command ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) > 1:
        try:
            ref_by = int(args[1])
            if user_id not in user_referrals and ref_by != user_id:
                user_referrals[ref_by] = user_referrals.get(ref_by, 0) + 1
        except:
            pass

    user_referrals.setdefault(user_id, 0)

    try:
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
    except:
        ref_link = "Link load ho raha hai..."

    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(
        types.InlineKeyboardButton("🔗 Mera Referral Link Share Karo", url=ref_link),
        types.InlineKeyboardButton("✅ Tool Unlock Karo", callback_data="check"),
        types.InlineKeyboardButton("📊 Meri Status Check Karo", callback_data="status")
    )

    bot.send_message(
        message.chat.id,
        f"👋 *Namaste {message.from_user.first_name}!*\n\n"
        f"🤖 Main ek Smart AI Assistant hoon!\n\n"
        f"📊 *Tumhare Referrals:* {user_referrals[user_id]}/3\n\n"
        f"🎯 *Kaise kaam karta hoon:*\n"
        f"• Koi bhi sawaal poochho — smart jawab dunga\n"
        f"• 3 dosto ko refer karo — special tool unlock hoga\n\n"
        f"🔗 *Tumhara Referral Link:*\n`{ref_link}`",
        reply_markup=mk,
        parse_mode='Markdown'
    )

# --- Status Check ---
@bot.callback_query_handler(func=lambda call: call.data == "status")
def status(call):
    count = user_referrals.get(call.from_user.id, 0)
    remaining = max(0, 3 - count)
    bot.answer_callback_query(
        call.id,
        f"📊 Tumhare referrals: {count}/3\n"
        f"Aur {remaining} chahiye tool ke liye!",
        show_alert=True
    )

# --- Tool Check ---
@bot.callback_query_handler(func=lambda call: call.data == "check")
def check(call):
    count = user_referrals.get(call.from_user.id, 0)
    if count >= 3:
        bot.send_message(
            call.message.chat.id,
            f"🎉 *Congratulations {call.from_user.first_name}!*\n\n"
            f"✅ 3 referrals complete!\n"
            f"🚀 *Tumhara Special Tool:*\n{NETLIFY_TOOL}",
            parse_mode='Markdown'
        )
    else:
        bot.answer_callback_query(
            call.id,
            f"❌ Abhi sirf {count}/3 referrals hain!\n"
            f"Aur {3-count} dosto ko refer karo! 🙏",
            show_alert=True
        )

# --- Group/Channel Message Handler ---
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def group_message(message):
    if not message.text:
        return

    text = message.text
    user = message.from_user.first_name if message.from_user else "User"

    # Gali detect → turant delete
    if has_bad_word(text):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(
                message.chat.id,
                f"⚠️ *{user}* bhai, yahan gali dena allowed nahi hai!\n"
                f"Theek se baat karo — sabka respect karo! 🙏",
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Delete error: {e}")
        return

    # Link detect → turant delete
    if has_link(text):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(
                message.chat.id,
                f"🚫 *{user}* bhai, group mein links share karna allowed nahi!\n"
                f"Admin se permission lo pehle. 🙏",
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Delete error: {e}")
        return

    # Normal sawaal → AI smart reply
    reply = get_ai_reply(text, user)
    bot.reply_to(message, reply)

# --- Private Message Handler ---
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def private_chat(message):
    if not message.text:
        return
    username = message.from_user.first_name or "User"
    bot.reply_to(message, get_ai_reply(message.text, username))

# --- Main ---
if __name__ == '__main__':
    print("🚀 Bot start ho raha hai...")

    # Scheduled posts thread
    t = threading.Thread(target=scheduled_posts, daemon=True)
    t.start()
    print("✅ Scheduled posts active!")

    print("✅ SMART BOT LIVE! Sab ready hai!")
    bot.polling(none_stop=True, interval=1)
