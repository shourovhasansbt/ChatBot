import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
# আপনার টেলিগ্রাম টোকেন (আগেরটাই আছে)
TELEGRAM_TOKEN = "8288219297:AAGCB3pxmy3DzXiVTpCRsgaIeJ9_rT1jfJ4"

# আপনার দেওয়া নতুন Gemini API Key
GEMINI_API_KEY = "AIzaSyCNmF9d10Pbm4TfhsZlcKaU9Pj4ut1phlE"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# গ্লোবাল ভেরিয়েবল
ACTIVE_MODEL = None
FAILED_MODELS = []

def get_best_model():
    """গুগল থেকে ভ্যালিড মডেল খুঁজে বের করবে এবং ফেইল করা মডেল বাদ দেবে"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            model_list = data.get('models', [])
            
            # আপনার CURL অনুযায়ী gemini-2.0-flash সবার আগে রাখা হলো
            preferred_order = [
                "gemini-2.0-flash", 
                "gemini-1.5-flash", 
                "gemini-1.5-pro", 
                "gemini-pro"
            ]
            
            # ১. পছন্দের লিস্ট চেক
            for pref in preferred_order:
                for model in model_list:
                    r_name = model['name'].replace("models/", "")
                    if r_name == pref and r_name not in FAILED_MODELS:
                        return r_name

            # ২. না পেলে যেকোনো flash/pro মডেল
            for model in model_list:
                r_name = model['name'].replace("models/", "")
                if ('generateContent' in model.get('supportedGenerationMethods', [])) and (r_name not in FAILED_MODELS):
                    if "flash" in r_name or "pro" in r_name:
                        return r_name
                        
    except Exception as e:
        print(f"Model search error: {e}")
    
    return "gemini-1.5-flash" # ফলব্যাক

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_MODEL, FAILED_MODELS
    FAILED_MODELS = [] 
    ACTIVE_MODEL = None
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    if not ACTIVE_MODEL:
        ACTIVE_MODEL = get_best_model()
        print(f"Selected Model: {ACTIVE_MODEL}")

    await update.message.reply_text("Welcome To Chatbot by Shourov")

async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_MODEL, FAILED_MODELS
    
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    # ৩ বার চেষ্টা করবে অটোমেটিক মডেল পরিবর্তন করে
    for attempt in range(3):
        if not ACTIVE_MODEL:
            ACTIVE_MODEL = get_best_model()

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": user_text}]}]}

        try:
            response = requests.post(api_url, json=payload, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and data['candidates']:
                    ai_reply = data['candidates'][0]['content']['parts'][0]['text']
                    await update.message.reply_text(ai_reply)
                    return 
                
            elif response.status_code == 429:
                await update.message.reply_text("সার্ভার বিজি, একটু পরে মেসেজ দিন।")
                return

            else:
                # মডেল কাজ না করলে অন্য মডেলে সুইচ করবে
                print(f"Model {ACTIVE_MODEL} failed. Switching...")
                FAILED_MODELS.append(ACTIVE_MODEL)
                ACTIVE_MODEL = None
                
        except Exception as e:
            FAILED_MODELS.append(ACTIVE_MODEL)
            ACTIVE_MODEL = None
    
    await update.message.reply_text("গুগল সার্ভারে সমস্যা হচ্ছে। একটু পর চেষ্টা করুন।")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_with_gemini))

        print("Bot updated with new API...")
        application.run_polling()
    except Exception as e:
        print(f"Startup Error: {e}")
