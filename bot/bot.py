import telebot
from telebot import types

TOKEN = '6638552024:AAFQ7lYbQIC1T_MOrGMce89cHo5bhvMOglg'
bot = telebot.TeleBot(TOKEN)

excuses_data = {}  # Dictionary to store student excuses data

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_message = "اهلا بك في خدمت الاعذار الرجاء اختيار خدمة"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton( "خدمات الطلاب")
    item2 = types.KeyboardButton("خدمات اعضاء هيئة التدريس")
    item3 = types.KeyboardButton("خدمات اخرى")
    # Add more services as needed
    markup.add(item1, item2,item3)
    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_services(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if message.text == "n":
        bot.send_message(chat_id, "Please provide your name:")
        bot.register_next_step_handler(message, process_name_step)
    # Add more services handling as needed

def process_name_step(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    excuses_data[user_id] = {'name': message.text}
    bot.send_message(chat_id, "Please provide your excuse details:")
    bot.register_next_step_handler(message, process_excuse_details_step)

def process_excuse_details_step(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    excuses_data[user_id]['excuse_details'] = message.text
    bot.send_message(chat_id, "Please state the reason for your excuse:")
    bot.register_next_step_handler(message, process_reason_step)

def process_reason_step(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    excuses_data[user_id]['reason'] = message.text
    bot.send_message(chat_id, "Do you have an image for your excuse? (Yes/No):")
    bot.register_next_step_handler(message, process_image_step)

def process_image_step(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if message.text.lower() == 'yes':
        bot.send_message(chat_id, "Please upload your image.")
        bot.register_next_step_handler(message, process_upload_image_step)
    else:
        send_excuse_to_manager(chat_id, user_id)

def process_upload_image_step(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if message.photo:
        # Get the file_id of the largest photo
        file_id = message.photo[-1].file_id
        excuses_data[user_id]['image'] = file_id
        send_excuse_to_manager(chat_id, user_id)
    else:
        bot.send_message(chat_id, "No image uploaded. Sending excuse without an image.")
        send_excuse_to_manager(chat_id, user_id)

def send_excuse_to_manager(chat_id, user_id):
    manager_chat_id = 1396310289  # Replace with the actual manager's chat ID
    manager_message = f"New Excuse from User ID {user_id}:\nName: {excuses_data[user_id]['name']}\nExcuse Details: {excuses_data[user_id]['excuse_details']}\nReason: {excuses_data[user_id]['reason']}"

    # Check if an image is attached and send it to the manager
    if 'image' in excuses_data[user_id]:
        image_file_id = excuses_data[user_id]['image']
        sent_message = bot.send_photo(manager_chat_id, image_file_id, caption=manager_message, reply_markup=get_accept_refuse_keyboard(user_id))
    else:
        sent_message = bot.send_message(manager_chat_id, manager_message, reply_markup=get_accept_refuse_keyboard(user_id))

    # Store the sent message ID for manager's reply
    excuses_data[user_id]['manager_message_id'] = sent_message.message_id

    bot.send_message(chat_id, "Your excuse has been submitted. The manager will review it.")

def get_accept_refuse_keyboard(user_id):
    markup = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton("Accept", callback_data=f"accept_{user_id}")
    refuse_button = types.InlineKeyboardButton("Refuse", callback_data=f"refuse_{user_id}")
    markup.row(accept_button, refuse_button)
    return markup

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    user_id = int(call.data.split('_')[-1])

    if user_id in excuses_data and 'manager_message_id' in excuses_data[user_id]:
        manager_message_id = excuses_data[user_id]['manager_message_id']

        if call.data.startswith("accept"):
            # Get the manager's original message text
            original_caption = call.message.caption or ""
            original_text = call.message.text or ""
            
            if original_caption:
                updated_caption = f"{original_caption}\nExcuse Accepted!"
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=manager_message_id, caption=updated_caption)
            elif original_text:
                updated_text = f"{original_text}\nExcuse Accepted!"
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=manager_message_id, text=updated_text)

            # Send a confirmation to the student
            bot.send_message(user_id, "Your excuse has been accepted!")

        elif call.data.startswith("refuse"):
            # Get the manager's original message text
            original_caption = call.message.caption or ""
            original_text = call.message.text or ""

            if original_caption:
                updated_caption = f"{original_caption}\nExcuse Refused!"
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=manager_message_id, caption=updated_caption)
            elif original_text:
                updated_text = f"{original_text}\nExcuse Refused!"
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=manager_message_id, text=updated_text)

            # Send a refusal message to the student
            bot.send_message(user_id, "Your excuse has been refused.")


if __name__ == "__main__":
    bot.polling(none_stop=True)
