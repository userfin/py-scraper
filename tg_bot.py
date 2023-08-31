import telebot
from telebot import types
from parser import *
from template_handler import *
from pymongo import MongoClient
import datetime
import os.path
import pandas as pd
import time

bot = telebot.TeleBot('-')
client = MongoClient('localhost', 27017, username='-', password='-')
db = client.tg_posts
posts = db.posts

template_list = []
try:
    template_list = read_csv('template.csv')
except:
    template_list = []
    

@bot.message_handler(commands=['start'])
def start(message):
    #Обработать csv с темплейтами
    bot.send_message(message.chat.id, f'Hello {message.from_user.first_name}, please provide a .csv template file')


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
        list_of_channels += template[6] + '\n'
    bot.send_message(message.chat.id, f'Found these channels in template file. Choose one:\n{list_of_channels}')
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
    
    url = template_list[template_index][0]
    base_url = template_list[template_index][1]
    article_div = template_list[template_index][4]
    link_div = template_list[template_index][2]
    link_class = template_list[template_index][3]

    article_link = get_article_link(url, base_url, link_div, link_class)
    global article
    article = parse_article(article_link, base_url, article_div)
    
    channel_name = template_list[template_index][6]
    global channel_id
    channel_id = template_list[template_index][7]
    
    message_template = ''
    for tag in template_list[template_index][5]:
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
        
        
    post_ids = [int(id) for id in posts.find().distinct('post_id')]
    
    posts.insert_one({
            'post_id': int(post_ids[-1]+1),
            'channel_name': channel_name,
            'channel_id': int(channel_id),
            'heading': article['heading'],
            'url': article['article_link'],
            'date_posted': datetime.datetime.now()
        })
        

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
    
    
@bot.message_handler(commands=['view_posts_today'])
def view_posts_today(message):
    #find all posts for today. Show the titles and channel names
    posts_today = []
    posts_cur = posts.find()
    for post in posts_cur:
        if (post['date_posted'].date() == datetime.datetime.now().date()):
            posts_today.append(post)
            
    message_text = ''
    for post in posts_today: 
        message_text = message_text + post['heading'][:20] + '...' + '   ' + post['channel_name'] + '\n\n'
    bot.send_message(message.chat.id, message_text)
    
    
@bot.message_handler(commands=['start_autoposting'])
def autoposting(message):
    #get latest posts, check if url in database, post
    #15 min interval
    starttime = time.time()
    while True:
        for template in template_list:
            url = template[0]
            base_url = template[1]
            link_div = template[2]
            link_class = template[3]
            article_div = template[4]
            tags = template[5]
            auto_channel_name = template[6]
            auto_channel_id = template[7]

            article_link = get_article_link(url, base_url, link_div, link_class)
            
            if not list(posts.find({'url': article_link})):
                article = parse_article(article_link, base_url, article_div)

                message_template = ''
                for tag in tags:
                    message_template += f"{article[tag]}" + '\n\n'
                message_text = (message_template[:1021] + '...') if len(message_template) > 1024 else message_template
                
                try:
                    bot.send_photo(auto_channel_id, f"{article['image_link']}", caption=message_text)
                    bot.send_message(message.chat.id, f'New post in channel {auto_channel_name}')
                except:
                    bot.send_message(auto_channel_id, message_text)
                    bot.send_message(message.chat.id, f'New post in channel {auto_channel_name}')
                    
                post_ids = [int(id) for id in posts.find().distinct('post_id')]
        
                posts.insert_one({
                        'post_id': int(post_ids[-1]+1),
                        'channel_name': auto_channel_name,
                        'channel_id': int(auto_channel_id),
                        'heading': article['heading'],
                        'url': article['article_link'],
                        'date_posted': datetime.datetime.now()
                    })
                
        time.sleep(60.0 - ((time.time() - starttime) % 60.0))
        

@bot.message_handler(commands=['edit_templates'])
def check_for_template(message):
    if os.path.isfile('template.csv'):
        url_template_pairs = {}
        for template in template_list:
            url = template[0]
            tags = template[5]
            url_template_pairs[url] = tags
            
        message_text = ''
        for key in url_template_pairs:
            message_text = message_text + key + '   ' + str(url_template_pairs[key]) + '\n\n'
        bot.send_message(message.chat.id, f'Websites and templates:\n\n{message_text}Enter a website url and new tags')
        bot.register_next_step_handler(message, edit_templates)
    
def edit_templates(message):
    new_website_tags = message.text.strip().split(',') #https://3dnews.ru/news,heading;article_link;article_text
    website_name = new_website_tags[0]
    new_tags = new_website_tags[1]
    
    row_number = 0
    for template in template_list:
        if website_name in template:
            template[5] = new_tags.split(';')
            bot.send_message(message.chat.id, f'Succesfully updated tags for {website_name}')
            break
        row_number+=1
            
    df = pd.read_csv("template.csv")
    df.loc[row_number, 'Template'] = new_tags
    df.to_csv("template.csv", index=False)
    

@bot.message_handler(commands=['edit_channels'])
def check_for_template(message):
    if os.path.isfile('template.csv'):
        url_channel_pairs = {}
        for template in template_list:
            url = template[0]
            channel_name = template[6]
            url_channel_pairs[url] = channel_name
            
        message_text = ''
        for key in url_channel_pairs:
            message_text = message_text + key + '   ' + str(url_channel_pairs[key]) + '\n\n'
        bot.send_message(message.chat.id, f'Websites and channels:\n\n{message_text}Enter a website url and new channelName and ID')
        bot.register_next_step_handler(message, edit_channel)
        
def edit_channel(message):
    new_website_channel = message.text.strip().split(',')#https://www.ixbt.com,Channel 2,-1001899784786
    website_name = new_website_channel[0]
    new_channel_name = new_website_channel[1]
    new_channel_id = new_website_channel[2]
    
    row_number = 0
    for template in template_list:
        if website_name in template:
            template[6] = new_channel_name
            template[7] = new_channel_id
            bot.send_message(message.chat.id, f'Succesfully updated channel for {website_name}')
            break
        row_number+=1
            
    df = pd.read_csv("template.csv")
    df.loc[row_number, 'ChannelName'] = new_channel_name
    df.loc[row_number, 'ChannelId'] = int(new_channel_id)
    df.to_csv("template.csv", index=False)
    

bot.polling(non_stop=True)