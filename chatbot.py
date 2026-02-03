import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---

# আপনার টেলিগ্রাম বটের টোকেন
TELEGRAM_TOKEN = "8288219297:AAGCB3pxmy3DzXiVTpCRsgaIeJ9_rT1jfJ4"

# আপনার দেওয়া Gemini API Key
GEMINI_API_KEY = "AIzaSyCzPdxKRJIWP1iKxSIOLZh5vlslxs_Fy3w"

# CHANGE: আমরা মডেল পরিবর্তন করে 1.5-flash ব্যবহার করছি (এটি বেশি স্টেবল)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am ready with Gemini 1.5 Flash. Ask me anything!")

async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # টাইপিং স্ট্যাটাস দেখানো
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    # Data Payload
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": user_text}
                ]
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': GEMINI_API_KEY
    }

    try:
        # Google Server-এ রিকোয়েস্ট পাঠানো
        response = requests.post(API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            try:
                # উত্তর বের করা
                ai_reply = data['candidates'][0]['content']['parts'][0]['text']
                
                # টেলিগ্রাম মেসেজ লিমিট চেক
                if len(ai_reply) > 4000:
                    ai_reply = ai_reply[:4000] + "... (বাকি অংশ কাটা হয়েছে)"
                
                await update.message.reply_text(ai_reply)
            except KeyError:
                await update.message.reply_text("AI কোনো উত্তর দিতে পারেনি।")
        elif response.status_code == 429:
             await update.message.reply_text("খুব বেশি রিকোয়েস্ট করা হয়েছে। ১ মিনিট অপেক্ষা করে আবার চেষ্টা করুন।")
        else:
            await update.message.reply_text(f"API Error: {response.status_code}")

    except Exception as e:
        await update.message.reply_text("সার্ভারে সমস্যা হচ্ছে।")
        print(f"Error: {e}")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        start_handler = CommandHandler('start', start)
        msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chat_with_gemini)

        application.add_handler(start_handler)
        application.add_handler(msg_handler)

        print("Bot is running...")
        application.run_polling()
    except Exception as e:
        print(f"Critical Error: {e}")
