import telebot
import sqlite3
import requests
import random
import string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- কনফিগারেশন ---
BOT_TOKEN = "8283539194:AAErOtM0toRQR9ILvYvf-oLNDtsaFfa8_QM"
CHANNEL_USERNAME = "@teamgitgo" # যে চ্যানেলে জয়েন করতে হবে
LOG_CHAT_ID = "-1003625052786"  # যে গ্রুপে/চ্যানেলে লগ যাবে
ADMIN_ID = 7157240269 # আপনার অ্যাডমিন আইডি

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

# --- ডাটাবেস ফাংশন ---
def get_user_credits(user_id):
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
        return False

# --- সিম্পল মেনু কীবোর্ড ---
def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🚀 Send SMS")) # বড় করে উপরে থাকবে
    markup.add(KeyboardButton("👥 Referral"), KeyboardButton("🎁 Redeem Code")) # নিচে দুইটা পাশাপাশি
    return markup

def get_join_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔔 Join Channel", url="https://t.me/teamgitgo"))
    markup.add(InlineKeyboardButton("🟢 Joined ✅", callback_data="check_join"))
    return markup

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
                    bot.send_message(referrer_id, f"🎉 আপনার রেফার লিংক দিয়ে একজন জয়েন করেছে! আপনি 5 ক্রেডিট পেয়েছেন।\nবর্তমান ক্রেডিট: {get_user_credits(referrer_id)}")
            except:
                pass
    
    if not check_joined(user_id):
        bot.send_message(user_id, "⚠️ Please join our channels to use the bot!", reply_markup=get_join_markup())
        return

    bot.reply_to(message, "✅ Welcome back!", reply_markup=get_main_menu())

# --- Joined Button Callback ---
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if check_joined(call.message.chat.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Thanks for joining!", reply_markup=get_main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি!", show_alert=True)


# ==========================================
# মেনু বাটনের কাজ 
# ==========================================

# ১. Referral
@bot.message_handler(func=lambda message: message.text == '👥 Referral')
def referral_btn(message):
    user_id = message.chat.id
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    text = f"🎁 <b>Refer & Earn</b>\n\nআপনার বন্ধুদের ইনভাইট করুন এবং প্রতি রেফারে <b>5 ক্রেডিট</b> পান!\n\nআপনার রেফারেল লিংক (ক্লিক করলেই কপি হবে):\n<code>{ref_link}</code>\n\n💰 বর্তমান ক্রেডিট: {get_user_credits(user_id)}"
    bot.send_message(user_id, text, parse_mode="HTML")

# ২. Redeem Code
@bot.message_handler(func=lambda message: message.text == '🎁 Redeem Code' or message.text == '/redeem')
def redeem_code_start(message):
    msg = bot.reply_to(message, "🎟 আপনার রিডিম কোডটি নিচে টাইপ করুন:")
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
        bot.reply_to(message, f"✅ অভিনন্দন! আপনি <b>{amount}</b> ক্রেডিট পেয়েছেন!\nবর্তমান ক্রেডিট: {get_user_credits(user_id)}", parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ কোডটি ভুল বা ইতিমধ্যে ব্যবহার শেষ হয়ে গেছে।")

# ৩. Send SMS (ক্লিক করলেই নাম্বার ও মেসেজ চাইবে)
user_sms_data = {}

@bot.message_handler(func=lambda message: message.text == '🚀 Send SMS' or message.text == '/sms')
def ask_phone(message):
    user_id = message.chat.id
    if not check_joined(user_id):
        bot.send_message(user_id, "⚠️ বট ব্যবহার করতে হলে আগে চ্যানেলে জয়েন করুন!", reply_markup=get_join_markup())
        return
    
    if get_user_credits(user_id) <= 0:
        bot.send_message(user_id, "❌ আপনার পর্যাপ্ত ক্রেডিট নেই। রেফার বা রিডিম কোড ব্যবহার করে ক্রেডিট বাড়ান।")
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
    
    params = {
        'apiKey': SMS_API_KEY, 'senderId': SMS_SENDER_ID, 'transactionType': 'T',
        'mobileNo': phone, 'message': sms_text
    }
    url = "http://sms.greenheritageit.com/smsapi"
    
    try:
        response = requests.get(url, params=params)
        update_credits(user_id, -1)
        bot.send_message(user_id, f"✅ মেসেজ সফলভাবে পাঠানো হয়েছে!\nবর্তমান ক্রেডিট: {get_user_credits(user_id)}")
        
        try:
            log_text = f"📡 <b>New SMS Log (Bot)</b>\n\n👤 <b>User ID:</b> <code>{user_id}</code>\n📞 <b>To:</b> <code>{phone}</code>\n✉️ <b>Msg:</b> {sms_text}"
            bot.send_message(LOG_CHAT_ID, log_text, parse_mode="HTML")
        except Exception as log_error:
            pass 
            
    except Exception as e:
        bot.send_message(user_id, "❌ মেসেজ পাঠাতে সমস্যা হয়েছে। একটু পর আবার চেষ্টা করুন।")


# --- Admin Command: /createcode (রিডিম কোড বানানো) ---
@bot.message_handler(commands=['createcode'])
def create_redeem_code(message):
    if message.chat.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "ব্যবহারবিধি: <code>/createcode <ক্রেডিট> <কতজন></code>", parse_mode="HTML")
        return
    
    amount = int(args[1])
    uses = int(args[2])
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    cursor.execute("INSERT INTO redeem_codes (code, amount, uses_left) VALUES (?, ?, ?)", (code, amount, uses))
    conn.commit()
    
    text = f"✅ <b>New Redeem Code Created!</b>\n\n🎟 Code:\n<code>{code}</code>\n\n💰 Credit: {amount}\n👥 Total Uses: {uses}"
    bot.reply_to(message, text, parse_mode="HTML")

# বট রান করা
print("Bot is running...")
bot.infinity_polling()
