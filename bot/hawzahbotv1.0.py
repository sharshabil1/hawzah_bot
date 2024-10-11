import telebot
from telebot import types
import itertools
import logging
from datetime import datetime

# Initialize bot and setup logging
TOKEN = '6638552024:AAFQ7lYbQIC1T_MOrGMce89cHo5bhvMOglg'
bot = telebot.TeleBot(TOKEN)
user_states = {}  # Dictionary to store user states and data
excuse_number_counter = itertools.count(start=1)  # Counter for generating unique excuse numbers

# Setup logging
logging.basicConfig(level=logging.INFO)

# Helper function to generate excuse number
def generate_excuse_number():
    return next(excuse_number_counter)

# Helper function to reset user state
def reset_user_state(user_id):
    user_states[user_id]['processing_excuse'] = False

# Helper function to send welcome message
def send_welcome(chat_id):
    welcome_message = "الرجاء اختيار أو كتابة أحد الخدمات التالية في المحادثة"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("خدمات الاعذار"),
        types.KeyboardButton("خدمات اعضاء هيئة التدريس"),
        types.KeyboardButton("خدمات اخرى")
    )
    bot.send_message(chat_id, welcome_message, reply_markup=markup)

# Command handler for /start and /help
@bot.message_handler(commands=['start', 'help'])
def send_welcome_message(message):
    send_welcome(message.chat.id)

# Service handler for all incoming messages
@bot.message_handler(func=lambda message: True)
def handle_services(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id not in user_states:
        user_states[user_id] = {'excuses_data': {}, 'processing_excuse': False}

    if message.text.lower() == "خدمات الاعذار" and not user_states[user_id]['processing_excuse']:
        user_states[user_id]['processing_excuse'] = True
        bot.send_message(chat_id, "ادخل الاسم الثلاثي")
        bot.register_next_step_handler(message, process_name_step, user_id)
    elif user_states[user_id]['processing_excuse']:
        bot.send_message(chat_id, "لديك بالفعل عذر قيد المعالجة. الرجاء انتظار اكتمال العملية الحالية.")
    elif message.text.lower() == "خدمات اعضاء هيئة التدريس":
        bot.send_message(chat_id, "هذه الخدمة غير متوفرة حالياً. الرجاء اختيار خدمة أخرى.")
    elif message.text.lower() == "خدمات اخرى":
        bot.send_message(chat_id, "هذه الخدمة غير متوفرة حالياً. الرجاء اختيار خدمة أخرى.")
    else:
        send_welcome(chat_id)

# Process each step of the excuse submission process
def process_name_step(message, user_id):
    chat_id = message.chat.id
    excuse_number = generate_excuse_number()
    user_states[user_id]['excuses_data'] = {'excuse_number': excuse_number, 'name': message.text}
    bot.send_message(chat_id, "تاريخ العذر (مثال: 2024-10-11)")
    bot.register_next_step_handler(message, process_excuse_details_step, user_id)

# Date validation function
def validate_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

def process_excuse_details_step(message, user_id):
    chat_id = message.chat.id
    date = validate_date(message.text)
    
    if date:
        user_states[user_id]['excuses_data']['excuse_details'] = message.text
        bot.send_message(chat_id, "اذكر السبب")
        bot.register_next_step_handler(message, process_reason_step, user_id)
    else:
        bot.send_message(chat_id, "التاريخ غير صحيح. الرجاء إدخال التاريخ بصيغة (YYYY-MM-DD)")
        bot.register_next_step_handler(message, process_excuse_details_step, user_id)

def process_reason_step(message, user_id):
    chat_id = message.chat.id
    user_states[user_id]['excuses_data']['reason'] = message.text
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("نعم"), types.KeyboardButton("لا"))
    bot.send_message(chat_id, "هل غبت كل اليوم؟", reply_markup=markup)
    bot.register_next_step_handler(message, process_class_details_step, user_id)

def process_class_details_step(message, user_id):
    chat_id = message.chat.id
    if message.text.lower() == 'لا':
        # If the user attended some classes, ask for class details
        bot.send_message(chat_id, "اذكر أرقام الحصص التي حضرتها في هذا اليوم (اكتب جميع الحصص في رسالة واحدة)")
        bot.register_next_step_handler(message, process_class_numbers, user_id)
    elif message.text.lower() == 'نعم':
        # If the user missed the entire day, proceed directly to ask about attachments
        user_states[user_id]['excuses_data']['Class_details'] = "كل اليوم"
        ask_for_attachment(chat_id, user_id)
    else:
        bot.send_message(chat_id, "الرجاء اختيار أو كتابة (نعم/لا) في المحادثة")
        bot.register_next_step_handler(message, process_class_details_step, user_id)

def process_class_numbers(message, user_id):
    chat_id = message.chat.id
    # Store the classes attended by the user
    user_states[user_id]['excuses_data']['Class_details'] = message.text.lower()
    # After providing class details, ask for attachments
    ask_for_attachment(chat_id, user_id)

# New function to ask for attachments
def ask_for_attachment(chat_id, user_id):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("نعم"), types.KeyboardButton("لا"))
    bot.send_message(chat_id, "هل لديك صورة أو مرفق؟ (نعم/لا)", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_image_step, user_id)

def process_image_step(message, user_id):
    chat_id = message.chat.id
    if message.text.lower() == 'نعم':
        bot.send_message(chat_id, "الرجاء أرفق صورة أو أي ملف للعذر")
        bot.register_next_step_handler(message, process_upload_image_step, user_id)
    elif message.text.lower() == 'لا':
        # If the user has no file or image, proceed to the excuse review
        review_excuse(chat_id, user_id)
    else:
        bot.send_message(chat_id, "الرجاء اختيار أو كتابة (نعم/لا) في المحادثة")
        bot.register_next_step_handler(message, process_image_step, user_id)

def process_upload_image_step(message, user_id):
    chat_id = message.chat.id
    if message.document:
        if message.document.mime_type.startswith('image/') or message.document.mime_type == 'application/pdf':
            file_id = message.document.file_id
            user_states[user_id]['excuses_data']['file'] = file_id
            review_excuse(chat_id, user_id)  # After uploading the file, proceed to review
        else:
            bot.send_message(chat_id, "الرجاء تحميل ملف صورة أو PDF.")
            bot.register_next_step_handler(message, process_upload_image_step, user_id)
    elif message.photo:
        file_id = message.photo[-1].file_id
        user_states[user_id]['excuses_data']['image'] = file_id
        review_excuse(chat_id, user_id)  # After uploading the image, proceed to review
    else:
        bot.send_message(chat_id, "الرجاء إرسال صورة أو ملف صالح.")
        bot.register_next_step_handler(message, process_upload_image_step, user_id)

# Function to present a review of the excuse to the user
def review_excuse(chat_id, user_id):
    excuse_data = user_states[user_id]['excuses_data']
    review_message = (f"مراجعة العذر الخاص بك:\n"
                      f"الاسم: {excuse_data['name']}\n"
                      f"تاريخ العذر: {excuse_data['excuse_details']}\n"
                      f"المحاضرات: {excuse_data['Class_details']}\n"
                      f"السبب: {excuse_data['reason']}\n"
                      "هل تريد تعديل أي شيء؟")

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("إرسال العذر"),
        types.KeyboardButton("تعديل العذر"),
        types.KeyboardButton("إلغاء العذر")
    )
    bot.send_message(chat_id, review_message, reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_review_decision, user_id)

def process_review_decision(message, user_id):
    chat_id = message.chat.id

    if message.text.lower() == 'إرسال العذر':
        send_excuse_to_manager(chat_id, user_id)
    elif message.text.lower() == 'تعديل العذر':
        modify_excuse(chat_id, user_id)
    elif message.text.lower() == 'إلغاء العذر':
        bot.send_message(chat_id, "تم إلغاء العذر.")
        reset_user_state(user_id)
        send_welcome(chat_id)
    else:
        bot.send_message(chat_id, "الرجاء اختيار (إرسال العذر/تعديل العذر/إلغاء العذر).")
        bot.register_next_step_handler(message, process_review_decision, user_id)

# Function to modify the excuse
def modify_excuse(chat_id, user_id):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("تعديل الاسم"),
        types.KeyboardButton("تعديل التاريخ"),
        types.KeyboardButton("تعديل السبب"),
        types.KeyboardButton("تعديل المحاضرات"),
        types.KeyboardButton("العودة")
    )
    bot.send_message(chat_id, "ما الذي ترغب في تعديله؟", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_modification_choice, user_id)

def process_modification_choice(message, user_id):
    chat_id = message.chat.id

    if message.text.lower() == 'تعديل الاسم':
        bot.send_message(chat_id, "ادخل الاسم الجديد:")
        bot.register_next_step_handler(message, modify_name, user_id)
    elif message.text.lower() == 'تعديل التاريخ':
        bot.send_message(chat_id, "ادخل التاريخ الجديد (YYYY-MM-DD):")
        bot.register_next_step_handler(message, modify_date, user_id)
    elif message.text.lower() == 'تعديل السبب':
        bot.send_message(chat_id, "ادخل السبب الجديد:")
        bot.register_next_step_handler(message, modify_reason, user_id)
    elif message.text.lower() == 'تعديل المحاضرات':
        bot.send_message(chat_id, "ادخل التفاصيل الجديدة للمحاضرات:")
        bot.register_next_step_handler(message, modify_class_details, user_id)
    elif message.text.lower() == 'العودة':
        review_excuse(chat_id, user_id)
    else:
        bot.send_message(chat_id, "الرجاء اختيار عنصر صحيح.")
        bot.register_next_step_handler(message, process_modification_choice, user_id)

def modify_name(message, user_id):
    chat_id = message.chat.id
    user_states[user_id]['excuses_data']['name'] = message.text
    review_excuse(chat_id, user_id)

def modify_date(message, user_id):
    chat_id = message.chat.id
    date = validate_date(message.text)
    if date:
        user_states[user_id]['excuses_data']['excuse_details'] = message.text
        review_excuse(chat_id, user_id)
    else:
        bot.send_message(chat_id, "التاريخ غير صحيح. الرجاء إدخال التاريخ بصيغة (YYYY-MM-DD)")
        bot.register_next_step_handler(message, modify_date, user_id)

def modify_reason(message, user_id):
    chat_id = message.chat.id
    user_states[user_id]['excuses_data']['reason'] = message.text
    review_excuse(chat_id, user_id)

def modify_class_details(message, user_id):
    chat_id = message.chat.id
    user_states[user_id]['excuses_data']['Class_details'] = message.text
    review_excuse(chat_id, user_id)

# Send excuse data to the manager
def send_excuse_to_manager(chat_id, user_id):
    manager_chat_id = 1396310289  # Replace with the actual manager's chat ID
    excuse_data = user_states[user_id]['excuses_data']
    excuse_number = excuse_data['excuse_number']

    manager_message = (
        f"عذر جديد برقم: {excuse_number}:\n"
        f"الاسم: {excuse_data['name']}\n"
        f"تاريخ العذر: {excuse_data['excuse_details']}\n"
        f"المحاضرات: {excuse_data['Class_details']}\n"
        f"السبب: {excuse_data['reason']}"
    )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("قبول", callback_data=f"accept_{excuse_number}"),
        types.InlineKeyboardButton("رفض", callback_data=f"refuse_{excuse_number}")
    )

    sent_message = None

    if 'image' in excuse_data:
        sent_message = bot.send_photo(
            manager_chat_id,
            excuse_data['image'],
            caption=manager_message,
            reply_markup=keyboard
        )
    elif 'file' in excuse_data:
        sent_message = bot.send_document(
            manager_chat_id,
            excuse_data['file'],
            caption=manager_message,
            reply_markup=keyboard
        )
    else:
        sent_message = bot.send_message(
            manager_chat_id,
            manager_message,
            reply_markup=keyboard
        )

    # Store the manager's message ID
    if sent_message:
        user_states[user_id]['excuses_data']['manager_message_id'] = sent_message.message_id

    bot.send_message(chat_id, f"تم إرسال العذر برقم: {excuse_number} وسيتم مراجعته من قبل اللجنة")
    reset_user_state(user_id)  # Reset the user's processing state

# Callback handler for accept/reject actions
@bot.callback_query_handler(func=lambda call: call.data.startswith('accept') or call.data.startswith('refuse'))
def handle_callback_query(call):
    excuse_number = int(call.data.split('_')[-1])
    user_id = None

    # Find the user ID associated with the excuse number
    for uid, user_data in user_states.items():
        if user_data['excuses_data'].get('excuse_number') == excuse_number:
            user_id = uid
            break
    else:
        return  # No matching user found

    manager_message_id = call.message.message_id
    action = "عذر مقبول!🟩" if call.data.startswith("accept") else "العذر مرفوض!🟥"

    # Edit the manager's message to include the action
    if call.message.content_type == 'photo':
        updated_caption = f"{call.message.caption}\n{action}"
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=manager_message_id,
            caption=updated_caption,
            reply_markup=None  # Remove the inline keyboard
        )
    elif call.message.content_type == 'document':
        updated_caption = f"{call.message.caption}\n{action}"
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=manager_message_id,
            caption=updated_caption,
            reply_markup=None
        )
    else:
        updated_text = f"{call.message.text}\n{action}"
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=manager_message_id,
            text=updated_text,
            reply_markup=None
        )

    # Notify the user about the action taken
    bot.send_message(user_id, f"تم {'قبول' if call.data.startswith('accept') else 'رفض'} العذر برقم: {excuse_number}")

if __name__ == "__main__":
    bot.polling(none_stop=True)
