import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8288219297:AAGCB3pxmy3DzXiVTpCRsgaIeJ9_rT1jfJ4"
GEMINI_API_KEY = "AIzaSyCzPdxKRJIWP1iKxSIOLZh5vlslxs_Fy3w"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# গ্লোবাল ভেরিয়েবল
ACTIVE_MODEL = None

def get_available_model():
    """ব্যাকগ্রাউন্ডে গুগল থেকে ভ্যালিড মডেল খুঁজে বের করবে"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for model in data.get('models', []):
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    model_name = model['name'].replace("models/", "")
                    if "flash" in model_name or "pro" in model_name:
                        return model_name
            if data.get('models'):
                return data['models'][0]['name'].replace("models/", "")
    except Exception as e:
        print(f"Model search error: {e}")
    return "gemini-1.5-flash" # ফলব্যাক

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_MODEL
    
    # ইউজারকে টাইপিং দেখাবে, যাতে মনে হয় লোড হচ্ছে
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    # ব্যাকগ্রাউন্ডে মডেল সেট করে নেবে (কিন্তু ইউজারকে বলবে না)
    if not ACTIVE_MODEL:
        ACTIVE_MODEL = get_available_model()
        print(f"System selected model: {ACTIVE_MODEL}") # এটা শুধু কনসোলে দেখা যাবে

    # ইউজারের জন্য সুন্দর মেসেজ
    await update.message.reply_text("Welcome To Chatbot by Shourov")

async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_MODEL
    
    if not ACTIVE_MODEL:
        ACTIVE_MODEL = get_available_model()

    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": user_text}]}]
    }

    try:
        response = requests.post(api_url, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and data['candidates']:
                ai_reply = data['candidates'][0]['content']['parts'][0]['text']
                await update.message.reply_text(ai_reply)
            else:
                await update.message.reply_text("দুঃখিত, আমি উত্তরটি দিতে পারছি না।")
        elif response.status_code == 429:
            await update.message.reply_text("একটু ধীরে মেসেজ দিন, সার্ভার বিজি।")
        else:
            # যদি মডেল এরর দেয়, তখন রিসেট করবে
            ACTIVE_MODEL = None 
            await update.message.reply_text("সামান্য সমস্যা হয়েছে, আবার মেসেজ দিন ঠিক হয়ে যাবে।")

    except Exception as e:
        await update.message.reply_text("নেটওয়ার্ক সমস্যা।")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_with_gemini))

        print("Bot is running professionally...")
        application.run_polling()
    except Exception as e:
        print(f"Startup Error: {e}")
