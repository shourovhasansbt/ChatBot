import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8288219297:AAGCB3pxmy3DzXiVTpCRsgaIeJ9_rT1jfJ4"
GEMINI_API_KEY = "AIzaSyCzPdxKRJIWP1iKxSIOLZh5vlslxs_Fy3w"

# CHANGE: আমরা 'gemini-pro' মডেল ব্যবহার করছি যা আপনার API তে নিশ্চিতভাবে আছে
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is finally fixed! Running on Gemini Pro.")

async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
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
            # উত্তর বের করা
            if 'candidates' in data and data['candidates']:
                ai_reply = data['candidates'][0]['content']['parts'][0]['text']
                await update.message.reply_text(ai_reply)
            else:
                await update.message.reply_text("AI উত্তর দিতে পারেনি। অন্য প্রশ্ন করুন।")
        else:
            # যদি আর কোনো সমস্যা হয়, এটা দেখাবে
            await update.message.reply_text(f"Google Error: {response.status_code}\n{response.text}")

    except Exception as e:
        await update.message.reply_text(f"Bot Error: {str(e)}")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_with_gemini))

        print("Bot is running...")
        application.run_polling()
    except Exception as e:
        print(f"Startup Error: {e}")
