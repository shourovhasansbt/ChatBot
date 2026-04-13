import telebot
import time
import threading
import requests

# আপনার দেওয়া বটের টোকেন
BOT_TOKEN = '7965067274:AAHL0qWdfci9bD0HwsjNocjTX3K0O4XnBjg'
bot = telebot.TeleBot(BOT_TOKEN)

# আনলিমিটেড টাস্ক ট্র্যাক করার জন্য ডিকশনারি
active_tasks = {}

# API কল করার মূল ফাংশন
def make_api_call(number):
    url = f"https://rakabro.nanobd.shop/api.php?key=3e68b4800c5c1cd8d07a21e8bc8464b1&number={number}"
    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception:
        return False

# লিমিটেড কলের জন্য ফাংশন (যেমন: ১০ বার)
def run_limited(chat_id, number, count):
    bot.send_message(chat_id, f"✅ {number} নম্বরে {count} বার কল শুরু হলো...")
    success_count = 0
    for i in range(count):
        if make_api_call(number):
            success_count += 1
        # সার্ভার ব্লক এড়াতে প্রতি কলের পর ২ সেকেন্ড বিরতি
        time.sleep(2) 
    bot.send_message(chat_id, f"🏁 {number} নম্বরে {count} বার কল সম্পন্ন হয়েছে! (সফল: {success_count})")

# আনলিমিটেড কলের জন্য ফাংশন (প্রতি ১ মিনিট পর পর)
def run_unlimited(chat_id, number):
    bot.send_message(chat_id, f"🚀 {number} নম্বরে আনলিমিটেড আপডেট শুরু হলো (১ মিনিট পর পর)।\nবন্ধ করতে কমান্ড দিন: /stop {number}")
    while active_tasks.get(number, False):
        make_api_call(number)
        # পরবর্তী কলের আগে ৬০ সেকেন্ড (১ মিনিট) অপেক্ষা করবে
        time.sleep(60)

# /call কমান্ড হ্যান্ডেলার
@bot.message_handler(commands=['call'])
def handle_call(message):
    chat_id = message.chat.id
    args = message.text.split()

    # কমান্ডের ফরম্যাট যাচাই করা
    if len(args) != 3:
        bot.reply_to(message, "⚠️ ভুল ফরম্যাট!\n\n**লিমিটেড কলের জন্য:**\n`/call 017XXXXXXXX 10`\n\n**আনলিমিটেড কলের জন্য:**\n`/call 017XXXXXXXX unlimited`", parse_mode="Markdown")
        return
    
    number = args[1]
    mode = args[2].lower()

    if mode == 'unlimited':
        # যদি এই নম্বরে আগে থেকেই আনলিমিটেড টাস্ক চলতে থাকে
        if active_tasks.get(number, False):
            bot.reply_to(message, f"⚠️ {number} নম্বরে ইতিমধ্যেই আনলিমিটেড প্রসেস চলছে।")
            return
        
        # আনলিমিটেড লুপ চালু করা
        active_tasks[number] = True
        thread = threading.Thread(target=run_unlimited, args=(chat_id, number))
        thread.start()
    else:
        try:
            count = int(mode)
            if count <= 0:
                bot.reply_to(message, "কাউন্ট অবশ্যই ১ বা তার বেশি হতে হবে।")
                return
            # লিমিটেড লুপ চালু করা
            thread = threading.Thread(target=run_limited, args=(chat_id, number, count))
            thread.start()
        except ValueError:
            bot.reply_to(message, "⚠️ কলের পরিমাণ অবশ্যই একটি সংখ্যা (যেমন: 10) অথবা 'unlimited' হতে হবে।")

# আনলিমিটেড লুপ বন্ধ করার কমান্ড
@bot.message_handler(commands=['stop'])
def handle_stop(message):
    args = message.text.split()
    
    if len(args) != 2:
        bot.reply_to(message, "⚠️ সঠিক নিয়ম: `/stop 017XXXXXXXX`", parse_mode="Markdown")
        return
        
    number = args[1]
    
    if active_tasks.get(number, False):
        active_tasks[number] = False
        bot.reply_to(message, f"🛑 {number} নম্বরের আনলিমিটেড প্রসেস সফলভাবে বন্ধ করা হয়েছে।")
    else:
        bot.reply_to(message, "⚠️ এই নম্বরে বর্তমানে কোনো আনলিমিটেড প্রসেস চলছে না।")

# বট চালু রাখা
print("বট সফলভাবে রান করছে...")
bot.polling(none_stop=True)
