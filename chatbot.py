import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8288219297:AAGCB3pxmy3DzXiVTpCRsgaIeJ9_rT1jfJ4"
GEMINI_API_KEY = "AIzaSyCzPdxKRJIWP1iKxSIOLZh5vlslxs_Fy3w"

# সরাসরি Google API URL (Gemini 1.5 Flash)
# নোট: আমরা লাইব্রেরি ব্যবহার করছি না, তাই Python ভার্সন নিয়ে সমস্যা হবে না।
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is Ready! (Running on Raw API Mode)")

async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    # JSON ডাটা তৈরি
    payload = {
        "contents": [{
            "parts": [{"text": user_text}]
        }]
    }

    try:
        # সরাসরি রিকোয়েস্ট পাঠানো হচ্ছে
        response = requests.post(API_URL, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            # উত্তর বের করে আনা
            if 'candidates' in data and data['candidates']:
                ai_reply = data['candidates'][0]['content']['parts'][0]['text']
                
                if len(ai_reply) > 4000:
                    ai_reply = ai_reply[:4000] + "..."
                
                await update.message.reply_text(ai_reply)
            else:
                # যদি উত্তর না আসে তবে পুরো রেসপন্স দেখাবে (ডিবাগ করার জন্য)
                await update.message.reply_text(f"No response content found. Raw: {data}")
        else:
            # যদি এরর হয়, তবে স্ট্যাটাস কোড দেখাবে
            await update.message.reply_text(f"Server Error: {response.status_code}\nMessage: {response.text}")

    except Exception as e:
        await update.message.reply_text(f"Critical Error: {str(e)}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_with_gemini))

    print("Bot is running...")
    application.run_polling()
