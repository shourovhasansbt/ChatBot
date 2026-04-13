import telebot
import sqlite3
import requests
import random
import string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- কনফিগারেশন ---
BOT_TOKEN = "8283539194:AAErOtM0toRQR9ILvYvf-oLNDtsaFfa8_QM"
CHANNEL_USERNAME = "@teamgitgo" # যে চ্যানেলে জয়েন করতে হবে
LOG_CHAT_ID = "-1003625052786"  # যে গ্রুপে/চ্যানেলে লগ যাবে (আগের PHP ফাইলের আইডি)
ADMIN_ID = 7157240269 # এখানে আপনার নিজের টেলিগ্রাম ইউজার আইডি দিন (bot এ /myid লিখে আইডি পেতে পারেন)

# SMS API কনফিগারেশন
SMS_API_KEY = '$2y$10$SNO/yJjzH7CdEFup7c17mO01LTbOUNY83zaGNR5nZfhhANf6lckKC236'
SMS_SENDER_ID = '8809617612022'

bot = telebot.TeleBot(BOT_TOKEN)
bot_info = bot.get_me()
BOT_USERNAME = bot_info.username

# ডাটাবেস সেটআপ
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 5)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS redeem_codes (code TEXT PRIMARY KEY, amount INTEGER, uses_left INTEGER)''')
conn.commit()

# --- ফাংশন: ইউজারের ক্রেডিট চেক ও আপডেট ---
def get_credits(user_id):
    cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    if res:
        return res[0]
    return 0

def update_credits(user_id, amount):
    cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

# --- ফাংশন: চ্যানেল জয়েন করেছে কিনা চেক ---
def check_joined(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        if status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        return False # যদি বট চ্যানেলের এডমিন না হয় বা ইউজার না থাকে

# --- /start এবং Referral সিস্টেম ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    
    # নতুন ইউজার কিনা চেক
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("INSERT INTO users (user_id, credits) VALUES (?, ?)", (user_id, 5))
        conn.commit()
        
        # রেফারেল চেক
        args = message.text.split()
        if len(args) > 1 and args[1].startswith("ref_"):
            try:
                referrer_id = int(args[1].split("_")[1])
                if referrer_id != user_id:
                    update_credits(referrer_id, 5)
                    bot.send_message(referrer_id, f"🎉 আপনার রেফার লিংক দিয়ে একজন জয়েন করেছে! আপনি 5 ক্রেডিট পেয়েছেন।\nবর্তমান ক্রেডিট: {get_credits(referrer_id)}")
            except:
                pass
        
        bot.reply_to(message, "🎉 স্বাগতম! আপনি নতুন ইউজার হিসেবে 5 ফ্রি ক্রেডিট পেয়েছেন!")
    
    # জয়েন বাটন
    if not check_joined(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/boost/teamgitgo"))
        bot.send_message(user_id, "⚠️ বট ব্যবহার করতে হলে প্রথমে আমাদের চ্যানেলে জয়েন করুন। জয়েন করার পর আবার /start দিন।", reply_markup=markup)
        return

    bot.reply_to(message, f"👋 হ্যালো!\nআপনার বর্তমান ক্রেডিট: {get_credits(user_id)}\n\nকমান্ডসমূহ:\n/sms - SMS পাঠাতে\n/refer - রেফার করে ক্রেডিট আর্ন করতে\n/redeem - রিডিম কোড ব্যবহার করতে")

# --- /refer কমান্ড ---
@bot.message_handler(commands=['refer'])
def refer_system(message):
    user_id = message.chat.id
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    text = f"🎁 **Refer & Earn**\n\nআপনার বন্ধুদের ইনভাইট করুন এবং প্রতি রেফারে **5 ক্রেডিট** পান!\n\nআপনার রেফারেল লিংক:\n`{ref_link}`\n\nআপনার বর্তমান ক্রেডিট: {get_credits(user_id)}"
    bot.send_message(user_id, text, parse_mode="Markdown")

# --- /sms কমান্ড (SMS পাঠানো) ---
user_sms_data = {}

@bot.message_handler(commands=['sms'])
def ask_phone(message):
    user_id = message.chat.id
    if not check_joined(user_id):
        bot.send_message(user_id, "⚠️ বট ব্যবহার করতে হলে আগে চ্যানেলে জয়েন করুন: @teamgitgo")
        return
    
    if get_credits(user_id) <= 0:
        bot.send_message(user_id, "❌ আপনার পর্যাপ্ত ক্রেডিট নেই। রেফার করে বা রিডিম কোড দিয়ে ক্রেডিট বাড়ান।")
        return
    
    msg = bot.reply_to(message, "📱 যাকে মেসেজ পাঠাবেন তার নাম্বার দিন (যেমন: 017XXXXXXXX):")
    bot.register_next_step_handler(msg, ask_message)

def ask_message(message):
    user_id = message.chat.id
    phone = message.text
    user_sms_data[user_id] = {'phone': phone}
    
    msg = bot.reply_to(message, "✉️ আপনার মেসেজটি টাইপ করুন:")
    bot.register_next_step_handler(msg, send_final_sms)

def send_final_sms(message):
    user_id = message.chat.id
    sms_text = message.text
    phone = user_sms_data[user_id]['phone']
    
    bot.send_message(user_id, "⏳ মেসেজ পাঠানো হচ্ছে, অপেক্ষা করুন...")
    
    # API Call
    params = {
        'apiKey': SMS_API_KEY, 'senderId': SMS_SENDER_ID, 'transactionType': 'T',
        'mobileNo': phone, 'message': sms_text
    }
    url = "http://sms.greenheritageit.com/smsapi"
    
    try:
        response = requests.get(url, params=params)
        
        # ক্রেডিট কাটা
        update_credits(user_id, -1)
        
        bot.send_message(user_id, f"✅ মেসেজ সফলভাবে পাঠানো হয়েছে!\nবর্তমান ক্রেডিট: {get_credits(user_id)}")
        
        # লগ পাঠানো
        log_text = f"📡 **New SMS Log (Bot)**\n\n👤 **User ID:** {user_id}\n📞 **To:** {phone}\n✉️ **Msg:** {sms_text}"
        bot.send_message(LOG_CHAT_ID, log_text, parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(user_id, "❌ মেসেজ পাঠাতে সমস্যা হয়েছে। একটু পর আবার চেষ্টা করুন।")

# --- /redeem কমান্ড ---
@bot.message_handler(commands=['redeem'])
def redeem_code_start(message):
    msg = bot.reply_to(message, "🎟 আপনার রিডিম কোডটি দিন:")
    bot.register_next_step_handler(msg, process_redeem)

def process_redeem(message):
    user_id = message.chat.id
    code = message.text.strip()
    
    cursor.execute("SELECT amount, uses_left FROM redeem_codes WHERE code=?", (code,))
    res = cursor.fetchone()
    
    if res and res[1] > 0:
        amount = res[0]
        uses_left = res[1] - 1
        
        update_credits(user_id, amount)
        cursor.execute("UPDATE redeem_codes SET uses_left=? WHERE code=?", (uses_left, code))
        conn.commit()
        
        bot.reply_to(message, f"✅ অভিনন্দন! আপনি {amount} ক্রেডিট পেয়েছেন!\nবর্তমান ক্রেডিট: {get_credits(user_id)}")
    else:
        bot.reply_to(message, "❌ কোডটি ভুল বা ইতিমধ্যে ব্যবহার শেষ হয়ে গেছে।")

# --- Admin Command: /createcode (রিডিম কোড বানানো) ---
@bot.message_handler(commands=['createcode'])
def create_redeem_code(message):
    if message.chat.id != ADMIN_ID:
        bot.reply_to(message, "❌ আপনি এই কমান্ড ব্যবহার করতে পারবেন না।")
        return
    
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "ব্যবহারবিধি: /createcode <ক্রেডিট_অ্যামাউন্ট> <কতজন_ইউজ_করতে_পারবে>\nযেমন: /createcode 10 5")
        return
    
    amount = int(args[1])
    uses = int(args[2])
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    cursor.execute("INSERT INTO redeem_codes (code, amount, uses_left) VALUES (?, ?, ?)", (code, amount, uses))
    conn.commit()
    
    bot.reply_to(message, f"✅ **New Redeem Code Created!**\n\n🎟 Code: `{code}`\n💰 Credit: {amount}\n👥 Total Uses: {uses}", parse_mode="Markdown")

# বট রান করা
print("Bot is running...")
bot.infinity_polling()
