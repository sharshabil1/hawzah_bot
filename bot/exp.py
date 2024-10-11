import telebot
from telebot import types
import itertools

TOKEN = '6638552024:AAFQ7lYbQIC1T_MOrGMce89cHo5bhvMOglg'
bot = telebot.TeleBot(TOKEN)
user_states = {}  # Dictionary to store user states and data
excuse_number_counter = itertools.count(start=1)  # Counter for generating unique excuse numbers

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_message = "الرجاء اختيار او كتابت احد الخدمات التالية في المحادثة"

    bot.send_message(message.chat.id, "-خدمات الاعذار \n -خدمات اعضاء هيئة التدريس \n -خدمات اخرى \n")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("خدمات الاعذار")
    item2 = types.KeyboardButton("خدمات اعضاء هيئة التدريس")
    item3 = types.KeyboardButton("خدمات اخرى")
    markup.add(item1, item2, item3)
    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)

def generate_excuse_number():
    return next(excuse_number_counter)

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
        bot.send_message(chat_id, "هذه الخدمة غير متوفرة حاليا الرجاء اختيار خدمة اخرى")
    elif message.text.lower() == "خدمات اخرى":
        bot.send_message(chat_id, "هذه الخدمة غير متوفرة حاليا الرجاء اختيار خدمة اخرى")
    else:

        send_welcome(message)


def process_name_step(message, user_id):
    chat_id = message.chat.id
    excuse_number = generate_excuse_number()
    user_states[user_id]['excuses_data'] = {'excuse_number': excuse_number, 'name': message.text}
    bot.send_message(chat_id, "تاريخ العذر")
    bot.register_next_step_handler(message, process_excuse_details_step, user_id)

def process_excuse_details_step(message, user_id):
    chat_id = message.chat.id
    user_states[user_id]['excuses_data']['excuse_details'] = message.text
    bot.send_message(chat_id, "اذكر السبب")
    bot.register_next_step_handler(message, process_reason_step, user_id)

def process_reason_step(message, user_id):
    chat_id = message.chat.id
    user_states[user_id]['excuses_data']['reason'] = message.text
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("نعم"), types.KeyboardButton("لا"))
    bot.send_message(chat_id, "هل غبت كل اليوم؟", reply_markup=markup)
    bot.register_next_step_handler(message, process_Class_details_step, user_id)

def process_Class_details_step(message, user_id):
    chat_id = message.chat.id

    if message.text.lower() == 'لا':
        bot.send_message(chat_id, "اذكر ارقام الحصص التي حضرتها في هذا اليوم (اكتب جميع الحصص في رسالة واحدة)")
        bot.register_next_step_handler(message, process_Class, user_id)
    elif message.text.lower() == 'نعم':
        user_states[user_id]['excuses_data']['Class_details'] = "كل اليوم"
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton("نعم"), types.KeyboardButton("لا"))
        bot.send_message(chat_id, "هل لديك صورة أو مرفق؟ (نعم/لا)", reply_markup=markup)
        bot.register_next_step_handler(message, process_image_step, user_id)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton("نعم"), types.KeyboardButton("لا"))
        bot.send_message(chat_id, "الرجاء اختيار او كتابت (نعم\لا) في المحادثة")

def process_Class(message, user_id):
    chat_id = message.chat.id
    user_states[user_id]['excuses_data']['Class_details'] = message.text.lower()

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("نعم"), types.KeyboardButton("لا"))
    bot.send_message(chat_id, "هل لديك صورة أو مرفق؟ (نعم/لا)", reply_markup=markup)
    bot.register_next_step_handler(message, process_image_step, user_id)

def process_image_step(message, user_id):
    chat_id = message.chat.id

    if message.text.lower() == 'نعم':
        bot.send_message(chat_id, "الرجاء أرفق صورة أو أي ملف للعذر")
        bot.register_next_step_handler(message, process_upload_image_step, user_id)
    elif message.text.lower() == 'لا':
        send_excuse_to_manager(chat_id, user_id)
        send_welcome(message)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton("نعم"), types.KeyboardButton("لا"))
        bot.send_message(chat_id, "الرجاء اختيار او كتابت (نعم\لا) في المحادثة")



def process_upload_image_step(message, user_id):
    chat_id = message.chat.id

    if message.document:
        if message.document.mime_type.startswith('image/') or message.document.mime_type == 'application/pdf':
            file_id = message.document.file_id
            user_states[user_id]['excuses_data']['file'] = file_id
            send_excuse_to_manager(chat_id, user_id)
            send_welcome(message)

    elif message.photo:
        file_id = message.photo[-1].file_id
        user_states[user_id]['excuses_data']['image'] = file_id
        send_excuse_to_manager(chat_id, user_id)
        send_welcome(message)

    else:
        send_excuse_to_manager(chat_id, user_id)
        send_welcome(message)

def send_excuse_to_manager(chat_id, user_id):
    manager_chat_id = 1396310289  # Replace with the actual manager's chat ID
    excuse_number = user_states[user_id]['excuses_data']['excuse_number']

    manager_message = f"عذر جديد برقم: {excuse_number}:\nالاسم: {user_states[user_id]['excuses_data']['name']}\nتاريخ العذر: {user_states[user_id]['excuses_data']['excuse_details']}\nالمحاضرات: {user_states[user_id]['excuses_data']['Class_details']}\nالسبب: {user_states[user_id]['excuses_data']['reason']}"

    keyboard = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton("قبول", callback_data=f"accept_{excuse_number}")
    refuse_button = types.InlineKeyboardButton("رفض", callback_data=f"refuse_{excuse_number}")
    keyboard.row(accept_button, refuse_button)

    sent_message = None

    if 'image' in user_states[user_id]['excuses_data']:
        image_file_id = user_states[user_id]['excuses_data']['image']
        sent_message = bot.send_photo(manager_chat_id, image_file_id, caption=manager_message, reply_markup=keyboard)

    elif 'file' in user_states[user_id]['excuses_data']:
        file_id = user_states[user_id]['excuses_data']['file']
        sent_message = bot.send_document(manager_chat_id, file_id, caption=manager_message, reply_markup=keyboard)

    else:
        sent_message = bot.send_message(manager_chat_id, manager_message, reply_markup=keyboard)

    if sent_message:
        user_states[user_id]['excuses_data']['manager_message_id'] = sent_message.message_id

    bot.send_message(chat_id, f"تم ارسال العذر برقم: {excuse_number} وسيتم مراجعته من قبل اللجنة")
    
    

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    excuse_number = int(call.data.split('_')[-1])

    for user_id, user_data in user_states.items():
        if 'excuses_data' in user_data and user_data['excuses_data'].get('excuse_number') == excuse_number:
            break
    else:
        return

    manager_message_id = user_states[user_id]['excuses_data'].get('manager_message_id')

    if manager_message_id:
        original_caption = call.message.caption or ""
        original_text = call.message.text or ""

        if call.data.startswith("accept"):
            updated_content = "عذر مقبول!🟩"
            reset_user_state(user_id)
        elif call.data.startswith("refuse"):
            updated_content = "العذر مرفوض!🟥"
            reset_user_state(user_id)

        if updated_content and updated_content != original_caption + original_text:
            if original_caption:
                updated_caption = f"{original_caption}\n{updated_content}"
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=manager_message_id, caption=updated_caption)
            elif original_text:
                updated_text = f"{original_text}\n{updated_content}"
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=manager_message_id, text=updated_text)

            confirmation_message = f"تم قبول العذر برقم: {excuse_number}!" if call.data.startswith("accept") else f"تم رفض العذر برقم: {excuse_number}🟥"
            bot.send_message(user_id, confirmation_message)


def reset_user_state(user_id):
    # Reset only the processing_excuse flag for the user
    user_states[user_id]['processing_excuse'] = False


if __name__ == "__main__":
    bot.polling(none_stop=True)
