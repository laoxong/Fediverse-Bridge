#!/bin/env python
"""
|--------------------------------------------------------------|
|                 Telegram to Misskey bridge                   |
|--------------------------------------------------------------|

Telegram bot API documentation:
        https://pypi.org/project/pyTelegramBotAPI/

"""
import os
import logging
import sys
import time
import telebot
import requests
import json
import sqlite3

'''
Basic setup
'''



logging.basicConfig(format='%(asctime)s: %(levelname)s %(name)s | %(message)s',
                    level=logging.INFO)
logger = telebot.logger.setLevel(logging.INFO)

bots = {}
# check if credentials exist, create if not
if not os.path.isfile("config.conf") and "DOCKER_CONTAINER" not in os.environ:
    if os.path.isfile("credentials.py"):
        logging.info("转移旧的配置文件")
        try:
            from credentials import *
            telegramchannelid = input("请输入你的Telegram频道ID:")
            with open("config.conf", "w") as f:
                f.write(telegram_token + "\n")
                f.write(telegramchannelid + ",")
                f.write(misskey_instance + ",")
                f.write(misskey_token + ",")
                f.write(misskey_visibility)                 
        except ImportError:
            logging.fatal(
                "credentials配置文件出错,请删除")
            exit(1)
    else:
        telegram_token = input("请输入你的Telegram Token:")
        telegramchannelid = input("请输入你的Telegram频道ID:")
        misskey_instance = input("请输入你的Misskey实例地址(https://m.moec.top):")
        misskey_token = input("请输入你的Misskey Token:")
        misskey_visibility = input("请输入你的Misskey可见性:")
        with open("config.conf", "w") as f:
            f.write(telegram_token + "\n")
            f.write(telegramchannelid + ",")
            f.write(misskey_instance + ",")
            f.write(misskey_token + ",")
            f.write(misskey_visibility)
            print("配置文件已生成,请重新运行")
            exit(0)
if not os.path.isfile("messages.db"):
    # 创建数据库
    logging.info("创建数据库")
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS `messages` (
        `id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        `channel_id`	INTEGER NOT NULL,
        `message_id`	INTEGER NOT NULL,
        `misskeynote_id`	TEXT NOT NULL
    );''')
    conn.commit()
    conn.close()

#判断启动参数
if len(sys.argv) > 1:
    if sys.argv[1] == "-add":
        if os.path.isfile("config.conf"):
            telegramchannelid = input("请输入你的Telegram频道ID:")
            misskey_instance = input("请输入你的Misskey实例地址:")
            misskey_token = input("请输入你的Misskey Token:")
            misskey_visibility = input("请输入你的Misskey可见性:")
            with open("config.conf", "a+") as f:
                f.write("\n" + telegramchannelid + ",")
                f.write(misskey_instance + ",")
                f.write(misskey_token + ",")
                f.write(misskey_visibility)
        else:
            telegram_token = input("请输入你的Telegram Token:")
            telegramchannelid = input("请输入你的Telegram频道ID:")
            misskey_instance = input("请输入你的Misskey实例地址(https://m.moec.top):")
            misskey_token = input("请输入你的Misskey Token:")
            misskey_visibility = input("请输入你的Misskey可见性:")
            with open("config.conf", "w") as f:
                f.write(telegram_token + "\n")
                f.write(telegramchannelid + ",")
                f.write(misskey_instance + ",")
                f.write(misskey_token + ",")
                f.write(misskey_visibility)
        exit(0)

if "DOCKER_CONTAINER" not in os.environ:
    logging.info("读取配置文件")
    with open("config.conf", "r") as f:
        lines = f.readlines()
        telegram_token = lines[0].strip('\n')
        for i in lines[1:]:
            i = i.strip('\n')
            telegramchannelid, misskey_instance, misskey_token, misskey_visibility = i.split(",")
            bots[int(telegramchannelid)] = [str(misskey_instance), str(misskey_token), str(misskey_visibility)]
            logging.debug(bots)
else:
    logging.info("从环境变量中读取配置")
    telegram_token = os.environ.get("telegramtoken")
    for i in os.environ.get("misskeybot").split("&"):
        telegramchannelid, misskey_instance, misskey_token, misskey_visibility = i.split(",")
        bots[int(telegramchannelid)] = [str(misskey_instance), str(misskey_token), str(misskey_visibility)]    
        logging.debug(bots)


# Telegram
# parse mode can be either HTML or MARKDOWN
bot = telebot.TeleBot(telegram_token, parse_mode="MARKDOWN", )


'''
Functions
'''


def footer_text(message):
    if message.forward_from_chat != None and message.chat.username != None:
        final_text = message.text + "\r\rFrom " + message.chat.username + \
                     f"\nForwarded from {message.forward_from_chat.title}"
    elif message.forward_from_chat != None and message.chat.username == None:
        final_text = message.text + "\r\r" + message.chat.title + \
                     f"\nForwarded from {message.forward_from_chat.title}"
    elif message.chat.username != None:
        final_text = message.text + "\r\rFrom " + message.chat.username
    elif message.chat.username == None:
        final_text = message.text + "\r\r" + message.chat.title
    else:
        final_text = message.text

    if len(final_text) < 3000:
        return final_text
    else:
        pass


def footer_image(message):
    if message.forward_from_chat != None:
        forward = f"\n转发自 {message.forward_from_chat.title}"
        try:
            caption = message.json['caption']
            if message.chat.username != None:
                final_text = caption + "\r\r来自 " + message.chat.username + forward
                return final_text
            else:
                final_text = caption + "\r\r" + message.chat.title + forward
                return final_text
        except:
            if message.chat.username != None:
                final_text = "来自 " + message.chat.username + forward
                return final_text
            else:
                final_text = message.chat.title + forward
                return final_text
    else:
        try:
            caption = message.json['caption']
            if message.chat.username != None:
                final_text = caption + "\r\r来自 " + message.chat.username
                return final_text
            else:
                final_text = caption + "\r\r" + message.chat.title
                return final_text
        except KeyError:
            if message.chat.username != None:
                final_text = "来自 " + message.chat.username
                return final_text
            else:
                final_text = message.chat.title
                return final_text

def uploadfile(caption,filename, mimetype, id):
    rmediajson = {"i": bots[id][1]}
    files = {'file': (filename, open(filename, "rb"), mimetype)}
    mediapost = requests.post(bots[id][0]+'/api/drive/files/create', timeout=10, data=rmediajson, files=files)
    i = 4
    media_id_list=[]
    media_id_list.append(json.loads(mediapost.text)["id"])
    rjson = {'text': caption, "localOnly": False, "visibility": bots[id][2],
                "fileIds": media_id_list, "viaMobile": False, "i": bots[id][1]}
    logging.info(f"上传成功")
    return rjson

'''
#Posting
'''



# Misskey

@bot.channel_post_handler(content_types=["text"])
def get_text(message):
    if message.chat.id in bots:
        logging.info(f"New {message.content_type}")
        conn = sqlite3.connect('messages.db')
        status_text = footer_text(message)
        rjson = {'text': status_text, "localOnly": False, "visibility": bots[message.chat.id][2], "viaMobile": False,
                "i": bots[message.chat.id][1]}
        if message.reply_to_message != None:
            c = conn.cursor()
            c.execute("SELECT * FROM messages WHERE message_id = (?)", (message.reply_to_message.message_id,))
            data = c.fetchone()
            if data != None:
                rjson["replyId"] = data[3]
        notepost = requests.post(bots[message.chat.id][0] + "/api/notes/create", json=rjson)
        if notepost.status_code == 200:
            c = conn.cursor()
            c.execute("INSERT INTO messages('channel_id', 'message_id', 'misskeynote_id') VALUES (?, ?, ?)",(message.chat.id, message.message_id, json.loads(notepost.text)["createdNote"]["id"]))
            conn.commit()
            conn.close()
            logging.info("发布帖子%s成功", json.loads(notepost.text)["createdNote"]["id"])
        else:
            logging.info("发布帖子失败")
            logging.info(notepost.text)

@bot.channel_post_handler(content_types=["photo"])
def get_image(message):
    if message.chat.id in bots:
        logging.info(f"New {message.content_type}")
        conn = sqlite3.connect('messages.db')
        caption = footer_image(message)

        fileID = message.photo[-1].file_id
        logging.info(f"Photo ID {fileID}")

        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("tmp_img", "wb") as tmp_image:
            tmp_image.write(downloaded_file)
        rmediajson = {"i": bots[message.chat.id][1]}
        timestamp = int(time.time())
        files = {'file': ("Fediverse-Bridge-upload-img-"+str(timestamp),open("tmp_img", "rb"),'image/png')}
        mediapost = requests.post(bots[message.chat.id][0]+'/api/drive/files/create', data=rmediajson, files=files, timeout=5)
        if mediapost.status_code == 200:
            logging.info("上传%s成功", json.loads(mediapost.text)["id"])
        else:
            logging.info("上传失败")
            logging.info(mediapost.text)
            return False
        media_id_list=[]
        media_id_list.append(json.loads(mediapost.text)["id"])
        rjson = {'text': caption, "localOnly": False, "visibility": bots[message.chat.id][2], "fileIds":media_id_list, "viaMobile": False,  "i": bots[message.chat.id][1]}
        c = conn.cursor()
        if message.reply_to_message != None:
            c.execute("SELECT * FROM messages WHERE message_id = (?)", (message.reply_to_message.message_id,))
            data = c.fetchone()
            if data != None:
                rjson["replyId"] = data[3]
        posted = requests.post(bots[message.chat.id][0] + "/api/notes/create", json=rjson, timeout=5)
        if posted.status_code == 200:
            logging.info("发布帖子%s成功", json.loads(posted.text)["createdNote"]["id"])
        else:
            logging.info("发布帖子失败")
            logging.info(posted.text)

@bot.channel_post_handler(content_types=["video"])
def get_video(message):
    if message.chat.id in bots:
        logging.info(f"New {message.content_type}")
        conn = sqlite3.connect('messages.db')
        c = conn.cursor()

        caption = footer_image(message)

        fileID = message.video.file_id
        logging.info(f"Video ID {fileID}")

        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("tmp_video", "wb") as tmp_video:
            tmp_video.write(downloaded_file)
        rmediajson = {"i": bots[message.chat.id][1]}
        timestamp = int(time.time())
        files = {'file': ("Fediverse-Bridge-upload-video-"+str(timestamp), open("tmp_video", "rb"))}
        mediapost = requests.post(bots[message.chat.id][0]+'/api/drive/files/create', data=rmediajson, files=files, timeout=5)

        if mediapost.status_code == 200:
            logging.info("上传%s成功", json.loads(mediapost.text)["id"])
        else:
            logging.info("上传%s失败", json.loads(mediapost.text)["id"])
            logging.info(mediapost.text)
            return False        
        media_id_list = []
        media_id_list.append(json.loads(mediapost.text)["id"])
        rjson = {'text': caption, "localOnly": False, "visibility": misskey_visibility, "fileIds": media_id_list, "viaMobile": False, "i": bots[message.chat.id][1]}
        if message.reply_to_message != None:
            c.execute("SELECT * FROM messages WHERE message_id = (?)", (message.reply_to_message.message_id,))
            data = c.fetchone()
            if data != None:
                rjson["replyId"] = data[3]
        posted = requests.post(bots[message.chat.id][0]+'/api/drive/files/create', json=rjson)
        if posted.status_code == 200:
            logging.info("发布帖子%s成功", json.loads(posted.text)["createdNote"]["id"])
        else:
            logging.info("发布帖子失败")
            logging.info(posted.text)

@bot.channel_post_handler(content_types=["audio"])
def get_audio(message):
    if message.chat.id in bots:
        logging.info(f"New {message.content_type}")
        caption = footer_image(message)
        timestamp = int(time.time())

        fileID = message.audio.file_id
        logging.info(f"Audio ID {fileID}")

        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("Fediverse-Bridge-upload-audio-"+str(timestamp), "wb") as tmp_audio:
            tmp_audio.write(downloaded_file)
        rjson = uploadfile(caption, "Fediverse-Bridge-upload-audio-"+str(timestamp), "audio/mp3")
        posted = requests.post(bots[message.chat.id][0] + "/api/notes/create", json=rjson, timeout=5)
        logging.info("发布帖子成功")

@bot.edited_channel_post_handler(content_types=["text"])
def edit_post(message):
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute("SELECT * FROM messages WHERE message_id = (?)", (message.message_id,))
    data = c.fetchone()
    if data != None:
        rjson = {"text": message.text, "i": bots[message.chat.id][1]}
        deleted = requests.post(bots[message.chat.id][0] + "/api/notes/delete", json={"noteId": data[3], "i": bots[message.chat.id][1]})
        logging.info("删除帖子%s", data[3])
        newpost = requests.post(bots[message.chat.id][0] + "/api/notes/create", json=rjson)
        if newpost.status_code == 200:
            logging.info("重新发布帖子%s成功", json.loads(newpost.text)["createdNote"]["id"])
            c.execute("UPDATE messages SET misskeynote_id = (?) WHERE id = (?)", (json.loads(newpost.text)["createdNote"]["id"], data[0]))
            conn.commit()
            conn.close()
        else:
            logging.info("重新发布帖子失败")
            logging.info(newpost.text)
'''
Finally run tg polling
'''

try:
    bot.polling(interval=5)
except KeyboardInterrupt:
    exit(0)
except:
    logging.error("Something went wrong.")
    bot.polling(interval=5)
finally:
    print("\nBye!")
