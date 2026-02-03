import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8288219297:AAGCB3pxmy3DzXiVTpCRsgaIeJ9_rT1jfJ4"
GEMINI_API_KEY = "AIzaSyCzPdxKRJIWP1iKxSIOLZh5vlslxs_Fy3w"

# আমরা ৫টি মডেলের লিস্ট দিচ্ছি। কোড একে একে সব ট্রাই করবে।
MODELS_TO_TRY = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-pro",
    "gemini-1.0-pro",
    "gemini-pro"
]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is checking available models... Send me a message!")

async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    success = False
    last_error = ""

    # লুপ চালিয়ে একটার পর একটা মডেল ট্রাই করবে
    for model_name in MODELS_TO_TRY:
        if success: break # কাজ হয়ে গেলে লুপ থামবে
        
        # v1beta এবং v1 দুটোই চেক করার জন্য URL
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": user_text}]}]
        }
        
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and data['candidates']:
                    ai_reply = data['candidates'][0]['content']['parts'][0]['text']
                    await update.message.reply_text(ai_reply)
                    success = True # কাজ হয়েছে!
                    print(f"Success with model: {model_name}")
            else:
                last_error = f"{model_name} Error: {response.status_code}"
                print(f"Failed with {model_name}: {response.status_code}")
                
        except Exception as e:
            last_error = str(e)

    # যদি ৫টি মডেলের কোনোটিই কাজ না করে
    if not success:
        await update.message.reply_text(f"সবগুলো মডেল ফেইল করেছে। শেষ এরর: {last_error}")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_with_gemini))

        print("Bot is running with Multi-Model Support...")
        application.run_polling()
    except Exception as e:
        print(f"Startup Error: {e}")
