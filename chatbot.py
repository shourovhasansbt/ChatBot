import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8288219297:AAGCB3pxmy3DzXiVTpCRsgaIeJ9_rT1jfJ4"
GEMINI_API_KEY = "AIzaSyCzPdxKRJIWP1iKxSIOLZh5vlslxs_Fy3w"

# CHANGE: 'gemini-pro' মডেল ব্যবহার করা হচ্ছে (এটি সব ফ্রি অ্যাকাউন্টে কাজ করে)
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running perfectly on Free Tier (Gemini Pro)!")

async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # টাইপিং দেখানো
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    payload = {
        "contents": [{
            "parts": [{"text": user_text}]
        }]
    }

    try:
        response = requests.post(API_URL, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            # সেফটি চেকিং যাতে ক্র্যাশ না করে
            if 'candidates' in data and data['candidates']:
                ai_reply = data['candidates'][0]['content']['parts'][0]['text']
                await update.message.reply_text(ai_reply)
            else:
                await update.message.reply_text("AI উত্তর দিতে পারেনি (Safety Filter)। অন্য প্রশ্ন করুন।")
        else:
            # এরর আসলে সেটা পরিষ্কার দেখাবে
            await update.message.reply_text(f"Google Error: {response.status_code}")

    except Exception as e:
        await update.message.reply_text("Server Connection Error.")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_with_gemini))

        print("Bot is running...")
        application.run_polling()
    except Exception as e:
        print(f"Error: {e}")
