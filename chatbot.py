import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8288219297:AAGCB3pxmy3DzXiVTpCRsgaIeJ9_rT1jfJ4"
GEMINI_API_KEY = "AIzaSyCzPdxKRJIWP1iKxSIOLZh5vlslxs_Fy3w"

# Google এর অফিসিয়াল লাইব্রেরি সেটআপ (Gemini 1.5 Flash)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# লগিং (ভুল ধরার জন্য)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is fixed and running! Ask me anything.")

async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # টাইপিং দেখানো
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    try:
        # সরাসরি লাইব্রেরি দিয়ে কল (সবচেয়ে নিরাপদ পদ্ধতি)
        response = model.generate_content(user_text)
        
        # টেক্সট বের করা
        if response.text:
            ai_reply = response.text
            
            # টেলিগ্রাম লিমিট চেক
            if len(ai_reply) > 4000:
                ai_reply = ai_reply[:4000] + "... (truncated)"
            
            await update.message.reply_text(ai_reply)
        else:
            await update.message.reply_text("AI কিছু বলতে পারেনি। আবার চেষ্টা করুন।")

    except Exception as e:
        # যদি কোনো কারণে এরর খায়
        await update.message.reply_text("সমস্যা হয়েছে। আবার চেষ্টা করুন।")
        print(f"Error: {e}")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        start_handler = CommandHandler('start', start)
        msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chat_with_gemini)

        application.add_handler(start_handler)
        application.add_handler(msg_handler)

        print("Bot Started Successfully...")
        application.run_polling()
    except Exception as e:
        print(f"Startup Error: {e}")
