import telebot
import pandas as pd
import requests
import io
import re

# توکن بات تلگرام
TOKEN = '7607658073:AAEvZqEN6oQORDAlROhk217Z4CvafpGrmvM'
bot = telebot.TeleBot(TOKEN)

# لینک فایل CSV از Google Sheets
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1yqjbZvvTBOJuV7eDKRJfTA1_PzmjC2jI3rwdTWj3CSo/export?format=csv'

# تابع برای بارگذاری داده‌ها از فایل CSV
def load_data():
    try:
        response = requests.get(SHEET_URL)
        response.raise_for_status()

        # خواندن داده‌های CSV با مدیریت کاماهای داخل سلول‌ها
        csv_data = response.content.decode('utf-8-sig')
        data = pd.read_csv(
            io.StringIO(csv_data),
            quotechar='"',         # تشخیص نقل‌قول‌ها برای جلوگیری از تفسیر کاماهای داخل سلول
            skipinitialspace=True  # حذف فاصله‌های اضافی بعد از کاما
        )

        # حذف ستون اضافی `Unnamed: 8`
        data = data.drop(columns=['Unnamed: 8'], errors='ignore')

        # حذف فاصله‌های اضافی از نام ستون‌ها
        data.columns = data.columns.str.strip()

        # چاپ نام ستون‌ها و پنج خط اول داده‌ها برای اشکال‌زدایی
        print("ستون‌های فایل CSV:", data.columns)
        print("پنج خط اول داده‌ها:")
        print(data.head())

        return data
    except Exception as e:
        print(f"❌ خطای بارگذاری داده‌ها: {e}")
        return None

# تابع برای نرمال‌سازی رشته‌ها (حذف فاصله‌های اضافی و تبدیل به حروف کوچک)
def normalize_string(s):
    if isinstance(s, str):
        # تبدیل تمام نیم فاصله‌ها (non-breaking space) به فاصله معمولی
        s = s.replace(u'\u200b', ' ')  # non-breaking space
        s = s.replace(u'\u200c', ' ')  # 'Zero Width Non-Joiner' or similar chars
        s = re.sub(r'\s+', ' ', s.strip())  # حذف فاصله‌های اضافی
        return s.lower()  # تبدیل به حروف کوچک
    return ""  # اگر داده NaN یا از نوع دیگر باشد، آن را به رشته خالی تبدیل می‌کنیم

# پیام خوشامدگویی
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! به بات کتابخانه خوش آمدید. لطفاً نام کتاب، نویسنده، یا ناشر را جستجو کنید.")

# جستجوی کتاب
@bot.message_handler(func=lambda message: True)
def search_books(message):
    query = message.text.strip()

    # بارگذاری داده‌ها از Google Sheets
    data = load_data()
    if data is None:
        bot.reply_to(message, "❌ خطایی در بارگذاری داده‌ها رخ داد. لطفاً دوباره تلاش کنید.")
        return

    # نرمال‌سازی ورودی کاربر
    normalized_query = normalize_string(query)

    # جستجو در داده‌ها (نرمال‌سازی شده)
    try:
        result = data[
            data['کتاب'].apply(lambda x: normalized_query in normalize_string(x)) |
            data['نویسنده'].apply(lambda x: normalized_query in normalize_string(x)) |
            data['مترجم'].apply(lambda x: normalized_query in normalize_string(x)) |
            data['نشر'].apply(lambda x: normalized_query in normalize_string(x))
        ]

        if not result.empty:
            response = f"📚 نتایج یافت شده برای '{query}':\n"
            for idx, row in result.iterrows():
                وضعیت = "🟢 موجود" if row['وضعیت'] == "موجود" else "🔴 قرض گرفته شده"
                response += f"\n📖 شماره {idx + 1}:"
                response += f"\n📘 کتاب: {row['کتاب']}"
                response += f"\n✍️ نویسنده: {row['نویسنده']}"
                response += f"\n📝 مترجم: {row['مترجم']}"
                response += f"\n🏢 نشر: {row['نشر']}"
                response += f"\n📚 موضوع: {row['موضوع']}"
                response += f"\n👶 گروه سنی: {row['گروه سنی']}"
                response += f"\n📌 وضعیت: {وضعیت}\n"
            bot.reply_to(message, response)
        else:
            bot.reply_to(message, "❌ کتابی با مشخصات وارد شده یافت نشد.")
    except Exception as e:
        print(f"❌ خطای جستجو: {e}")
        bot.reply_to(message, "❌ مشکلی در پردازش داده‌ها رخ داد.")

# اجرای بات
print("🤖 بات در حال اجرا است...")
bot.polling()
