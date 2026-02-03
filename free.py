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

# গ্লোবাল ভেরিয়েবল যেখানে মডেলের নাম সেভ থাকবে
ACTIVE_MODEL = None

def get_available_model():
    """Google এর সার্ভার থেকে ভ্যালিড মডেল খুঁজে বের করবে"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # সব মডেল চেক করে দেখবে কোনটা দিয়ে কন্টেন্ট জেনারেট করা যায়
            for model in data.get('models', []):
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    model_name = model['name'].replace("models/", "")
                    # আমরা প্রেফার করব flash বা pro মডেল
                    if "flash" in model_name or "pro" in model_name:
                        return model_name
            # যদি স্পেসিফিক কিছু না পায়, তালিকার প্রথমটা ফেরত দেবে
            if data.get('models'):
                return data['models'][0]['name'].replace("models/", "")
    except Exception as e:
        print(f"Model search error: {e}")
    return "gemini-1.5-flash" # ফলব্যাক (যদি সব ফেইল করে)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_MODEL
    
    # ইউজার স্টার্ট দিলেই আমরা মডেল খুঁজব
    if not ACTIVE_MODEL:
        await update.message.reply_text("🔍 আপনার জন্য সঠিক মডেলটি খুঁজছি... একটু অপেক্ষা করুন।")
        found_model = get_available_model()
        ACTIVE_MODEL = found_model
        await update.message.reply_text(f"✅ মডেল পাওয়া গেছে: {ACTIVE_MODEL}\nএখন চ্যাট করতে পারেন!")
    else:
        await update.message.reply_text(f"Ready! Running on: {ACTIVE_MODEL}")

async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_MODEL
    
    # যদি মডেল সেট না থাকে, আবার খোঁজার চেষ্টা করবে
    if not ACTIVE_MODEL:
        ACTIVE_MODEL = get_available_model()

    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    # ডাইনামিক URL তৈরি
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
                await update.message.reply_text("AI উত্তর দিতে পারেনি (Safety Filter)।")
        elif response.status_code == 429:
            await update.message.reply_text("খুব দ্রুত মেসেজ দিচ্ছেন! একটু ধীরে মেসেজ দিন (Rate Limit)।")
        else:
            # যদি এই মডেলেও এরর দেয়, আমরা মডেল রিসেট করে দেব যাতে পরেরবার নতুন মডেল খোঁজে
            error_msg = response.text
            ACTIVE_MODEL = None 
            await update.message.reply_text(f"Error {response.status_code}. নতুন করে মডেল খোঁজা হবে। আবার /start চাপুন।")

    except Exception as e:
        await update.message.reply_text(f"System Error: {str(e)}")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_with_gemini))

        print("Bot running with Auto-Detect Mode...")
        application.run_polling()
    except Exception as e:
        print(f"Startup Error: {e}")
