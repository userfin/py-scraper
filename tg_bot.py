import telebot
from telebot import types
from parser import *
from template_handler import *

bot = telebot.TeleBot('your_key')

template_list = []
try:
    template_list = read_csv('template.csv')
except:
    template_list = []

@bot.message_handler(commands=['start'])
def start(message):
    #Обработать csv с темплейтами
    bot.send_message(message.chat.id, f'Hello {message.from_user.first_name}, please provide a .csv template file (url,channel_name, channel_id, tags)')


@bot.message_handler(content_types=['document']) # parser template
def set_template(message):
    file_name = 'template.csv'
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)
    global template_list
    template_list = read_csv(file_name)

    bot.send_message(message.chat.id, 'Template file saved')


@bot.message_handler(commands=['create_post'])
def create_post(message):
    list_of_channels = ''
    for template in template_list:
        list_of_channels += template[1] + '\n'
    bot.send_message(message.chat.id, f'Found these channels in your template file. Choose one:\n{list_of_channels}')
    bot.register_next_step_handler(message, choose_channel)

def choose_channel(message):
    global where_to
    try:
        where_to = str(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, 're-do input')
        bot.register_next_step_handler(message, choose_channel)
        return

    template_index = get_template_index(where_to, template_list)

    article_link = get_article_link(template_list[template_index][0])
    global article
    article = parse_article(article_link)
    channel_name = template_list[template_index][1]
    global channel_id
    channel_id = template_list[template_index][2]
    message_template = ''
    for tag in template_list[template_index][3]:
        message_template += f"{article[tag]}" + '\n\n'
    global message_text 
    message_text = (message_template[:1021] + '...') if len(message_template) > 1024 else message_template

    markup = types.InlineKeyboardMarkup(row_width=2)
    send_post_button = types.InlineKeyboardButton(f'Send to {channel_name}', callback_data='send')
    delete_post_button = types.InlineKeyboardButton('Discard post', callback_data='delete')
    markup.add(send_post_button, delete_post_button)

    try:
        bot.send_photo(message.chat.id, f"{article['image_link']}", caption=message_text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, message_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def post_to_channel_callback(call):
    if call.data == 'send':
        try:
            bot.send_photo(channel_id, f"{article['image_link']}", caption=message_text)
        except:
            bot.send_message(channel_id, message_text)
        return
    if call.data == 'delete':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return

bot.polling(non_stop=True)