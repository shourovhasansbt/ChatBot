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
FAILED_MODELS = []  # যেসব মডেল কাজ করবে না, সেগুলো এখানে জমা হবে

def get_best_model():
    """গুগল থেকে ভ্যালিড মডেল খুঁজে বের করবে, তবে ফেইল করা মডেল বাদ দেবে"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            model_list = data.get('models', [])
            
            # আমরা প্রেফার করব স্ট্যাবল মডেলগুলো
            preferred_order = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-pro"]
            
            # ১. প্রথমে পছন্দের লিস্ট চেক করি
            for pref in preferred_order:
                for model in model_list:
                    r_name = model['name'].replace("models/", "")
                    if r_name == pref and r_name not in FAILED_MODELS:
                        return r_name

            # ২. না পেলে যেকোনো 'flash' বা 'pro' মডেল খুঁজি যা ফেইল করেনি
            for model in model_list:
                r_name = model['name'].replace("models/", "")
                if ('generateContent' in model.get('supportedGenerationMethods', [])) and (r_name not in FAILED_MODELS):
                    if "flash" in r_name or "pro" in r_name:
                        return r_name
                        
    except Exception as e:
        print(f"Model search error: {e}")
    
    # কিছুই না পেলে ডিফল্ট
    return "gemini-1.5-flash"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_MODEL, FAILED_MODELS
    FAILED_MODELS = [] # নতুন করে শুরু
    ACTIVE_MODEL = None
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    # ব্যাকগ্রাউন্ডে মডেল সেটআপ
    if not ACTIVE_MODEL:
        ACTIVE_MODEL = get_best_model()
        print(f"Selected Model: {ACTIVE_MODEL}")

    await update.message.reply_text("Welcome To Chatbot by Shourov")

async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_MODEL, FAILED_MODELS
    
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    # সর্বোচ্চ ৩ বার চেষ্টা করবে (মডেল পাল্টে পাল্টে)
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
                    return # সফল হলে এখান থেকেই বেরিয়ে যাবে
                
            elif response.status_code == 429:
                await update.message.reply_text("একটু ধীরে মেসেজ দিন, সার্ভার বিজি।")
                return

            else:
                # যদি এরর খায়, বর্তমান মডেলকে কালো তালিকাভুক্ত করবে
                print(f"Model {ACTIVE_MODEL} failed with {response.status_code}. Switching...")
                FAILED_MODELS.append(ACTIVE_MODEL)
                ACTIVE_MODEL = None # পরের লুপে নতুন মডেল খুঁজবে
                
        except Exception as e:
            print(f"Connection failed: {e}")
            FAILED_MODELS.append(ACTIVE_MODEL)
            ACTIVE_MODEL = None
    
    # ৩ বার চেষ্টার পরও না হলে
    await update.message.reply_text("দুঃখিত, গুগল সার্ভারে বড় সমস্যা হচ্ছে। একটু পরে চেষ্টা করুন।")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_with_gemini))

        print("Bot is running with Auto-Healing...")
        application.run_polling()
    except Exception as e:
        print(f"Startup Error: {e}")
