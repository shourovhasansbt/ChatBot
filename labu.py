import telebot
import time

# আপনার দেওয়া টোকেন এবং চ্যাট আইডি
TOKEN = '8660571901:AAFGceCkYB6I8mnDXgZ4h-GjC8xdRFbIPZY'
CHAT_ID = '-1003764358112'

bot = telebot.TeleBot(TOKEN)

print("বট চালু হচ্ছে এবং মেসেজ পাঠানো শুরু করছে...")

while True:
    try:
        # গ্রুপে মেসেজ পাঠানো
        bot.send_message(CHAT_ID, "I love u labonno")
        print("মেসেজ সফলভাবে পাঠানো হয়েছে!")
        
        # ৫ সেকেন্ড অপেক্ষা করা
        time.sleep(5)
    except Exception as e:
        print(f"মেসেজ পাঠাতে সমস্যা হয়েছে: {e}")
        # এরর হলেও ৫ সেকেন্ড পর আবার চেষ্টা করবে
        time.sleep(5)
