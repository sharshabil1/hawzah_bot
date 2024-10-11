import telebot
from telebot import types

TOKEN = '6638552024:AAFQ7lYbQIC1T_MOrGMce89cHo5bhvMOglg'
bot = telebot.TeleBot(TOKEN)
user_states = {}  # Dictionary to store user states and data
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_message = "الرجاء اختيار احد الخدمات التالية"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("خدمات الاعذار")
    item2 = types.KeyboardButton("خدمات اعضاء هيئة التدريس")
    item3 = types.KeyboardButton("خدمات اخرى")
    markup.add(item1, item2, item3)
    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)
    
    
@bot.message_handler(func=lambda message: True)
def handle_services(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Initialize user state if not present
    if user_id not in user_states:
        user_states[user_id] = {'excuses_data': {}, 'processing_excuse': False}

    if message.text == "خدمات الاعذار" and not user_states[user_id]['processing_excuse']:
        user_states[user_id]['processing_excuse'] = True
        bot.send_message(chat_id, "ادخل الاسم الثلاثي")
        bot.register_next_step_handler(message, process_name_step, user_id)
    elif user_states[user_id]['processing_excuse']:
        bot.send_message(chat_id, "لديك بالفعل عذر قيد المعالجة. الرجاء انتظار اكتمال العملية الحالية.")

def process_name_step(message, user_id):
    chat_id = message.chat.id
    user_states[user_id]['excuses_data'] = {'name': message.text}
    bot.send_message(chat_id, "تاريخ العذر")
    bot.register_next_step_handler(message, process_excuse_details_step, user_id)

def process_excuse_details_step(message, user_id):
    chat_id = message.chat.id
    user_states[user_id]['excuses_data']['excuse_details'] = message.text
    bot.send_message(chat_id, "اذكر السبب")
    bot.register_next_step_handler(message, process_reason_step, user_id)

def process_Class_details_step(message, user_id):
    chat_id = message.chat.id

    if message.text.lower() == 'لا':
        bot.send_message(chat_id, "اذكر ارقام الحصص التي حضرتها في هذا اليوم(اكتب جميع الحصص في رسالة واحدة)")
        bot.register_next_step_handler(message, process_Class, user_id)
    else:
        user_states[user_id]['excuses_data']['Class_details'] = "كل اليوم"
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton("نعم"), types.KeyboardButton("لا"))
        bot.send_message(chat_id, "هل لديك صورة او مرفق؟(نعم\لا)", reply_markup=markup)
        bot.register_next_step_handler(message, process_image_step, user_id)

def process_Class(message, user_id):
    chat_id = message.chat.id
    user_states[user_id]['excuses_data']['Class_details'] = message.text.lower()

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("نعم"), types.KeyboardButton("لا"))
    bot.send_message(chat_id, "هل لديك صورة او مرفق؟(نعم\لا)", reply_markup=markup)
    bot.register_next_step_handler(message, process_image_step, user_id)

def process_reason_step(message, user_id):
    chat_id = message.chat.id
    user_states[user_id]['excuses_data']['reason'] = message.text
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("نعم"), types.KeyboardButton("لا"))
    bot.send_message(chat_id, "هل غبت كل اليوم؟", reply_markup=markup)
    bot.register_next_step_handler(message, process_Class_details_step, user_id)

def process_image_step(message, user_id):
    chat_id = message.chat.id

    if message.text.lower() == 'نعم':
        bot.send_message(chat_id, "الرجاء أرفق صورة أو أي ملف للعذر")
        bot.register_next_step_handler(message, process_upload_image_step, user_id)
    else:
        send_excuse_to_manager(chat_id, user_id)
        send_welcome(message)
        reset_user_state(user_id)  # Reset user state for a new excuse

def process_upload_image_step(message, user_id):
    chat_id = message.chat.id

    if message.document:
        # Check if the uploaded file is an image or a PDF
        if message.document.mime_type.startswith('image/') or message.document.mime_type == 'application/pdf':
            file_id = message.document.file_id
            user_states[user_id]['excuses_data']['file'] = file_id
            send_excuse_to_manager(chat_id, user_id)
            send_welcome(message)
        else:
            bot.send_message(chat_id, "يرجى إرسال ملف صورة أو ملف PDF فقط. سيتم إرسال العذر بدون ملف.")
            send_excuse_to_manager(chat_id, user_id)
            send_welcome(message)

        reset_user_state(user_id)  # Reset user state for a new excuse

    elif message.photo:
        # Check if the uploaded file is an image (JPG, PNG, etc.)
        file_id = message.photo[-1].file_id
        user_states[user_id]['excuses_data']['image'] = file_id
        send_excuse_to_manager(chat_id, user_id)
        send_welcome(message)
        reset_user_state(user_id)  # Reset user state for a new excuse

    else:
        bot.send_message(chat_id, "لم يتم تحميل ملف صالح. سيتم إرسال العذر بدون ملف.")
        send_excuse_to_manager(chat_id, user_id)
        send_welcome(message)
        reset_user_state(user_id)  # Reset user state for a new excuse
        

def send_excuse_to_manager(chat_id, user_id):
    manager_chat_id = 1137824925  # Replace with the actual manager's chat ID
    manager_message = f"عذر جديد من قبل المعرف: {user_id}:\nالاسم: {user_states[user_id]['excuses_data']['name']}\nتاريخ العذر: {user_states[user_id]['excuses_data']['excuse_details']}\nالمحاضرات: {user_states[user_id]['excuses_data']['Class_details']}\nالسبب: {user_states[user_id]['excuses_data']['reason']}"

    # Create the inline keyboard with accept and refuse buttons
    keyboard = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton("قبول", callback_data=f"accept_{user_id}")
    refuse_button = types.InlineKeyboardButton("رفض", callback_data=f"refuse_{user_id}")
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

    # Store the manager_message_id in user_states
    if sent_message:
        user_states[user_id]['excuses_data']['manager_message_id'] = sent_message.message_id
    else:
        bot.send_message(chat_id, "Error: Unable to send excuse to the manager. Please try again.")

    bot.send_message(chat_id, "تم ارسال العذر و سيتم مراجعته من قبل اللجنة")

    
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    user_id = int(call.data.split('_')[-1])

    if user_id in user_states and 'excuses_data' in user_states[user_id]:
        manager_message_id = user_states[user_id]['excuses_data'].get('manager_message_id')

        if manager_message_id:
            original_caption = call.message.caption or ""
            original_text = call.message.text or ""

            if call.data.startswith("accept"):
                original_caption = call.message.caption or ""
                original_text = call.message.text or ""

                if original_caption:
                    updated_caption = f"{original_caption}\nعذر مقبول!🟩"
                    bot.edit_message_caption(chat_id=call.message.chat.id, message_id=manager_message_id, caption=updated_caption)
                elif original_text:
                    updated_text = f"{original_text}\nعذر مقبول!🟩"
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=manager_message_id, text=updated_text)

                # Send a confirmation to the student
                bot.send_message(user_id, "تم قبول العذر!")

            elif call.data.startswith("refuse"):
                # Get the manager's original message text
                original_caption = call.message.caption or ""
                original_text = call.message.text or ""

                if original_caption:
                    updated_caption = f"{original_caption}\nالعذر مرفوض!🟥"
                    bot.edit_message_caption(chat_id=call.message.chat.id, message_id=manager_message_id, caption=updated_caption)
                elif original_text:
                    updated_text = f"{original_text}\nالعذر مرفوض!🟥"
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=manager_message_id, text=updated_text)

                # Send a refusal message to the student
                bot.send_message(user_id, "تم رفض العذر🟥")

            


def reset_user_state(user_id):
    # Reset only the processing_excuse flag for the user
    user_states[user_id]['processing_excuse'] = False


if __name__ == "__main__":
    bot.polling(none_stop=True)
