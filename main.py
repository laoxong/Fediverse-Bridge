#!/bin/env python
"""
|--------------------------------------------------------------|
|                 Telegram to Mastodon bridge                  |
|--------------------------------------------------------------|

Telegram bot API documentation:
        https://pypi.org/project/pyTelegramBotAPI/
Mastodon bot API documentation:
    https://mastodonpy.readthedocs.io/en/stable/

"""
import os
import logging
import time
import telebot
from mastodon import Mastodon
import requests
import json

'''
Basic setup
'''
logging.basicConfig(format='%(asctime)s: %(levelname)s %(name)s | %(message)s',
                    level=logging.INFO)
logger = telebot.logger.setLevel(logging.INFO)

# check if credentials exist, create if not
if not os.path.isfile("credentials.py"):
    logging.info("No credentials found")
    telegram_token = input("输入你的telegram bot token: ")
    web_type = input("输入网站类型(misskey):")
    if web_type == 'misskey':
        misskey_token = input("请输入Misskey bot token:")
        misskey_instance = input("请输入Misskey实例地址(https://m.moec.top):")
        misskey_visibility = input("帖子类型(public,home,followers)")
        character_limit = input("字数限制:")
        
        with open("credentials.py", "w") as creds:
            creds.write(
                f"telegram_token = '{telegram_token}'\nmisskey_token = '{misskey_token}'\nweb_type= '{web_type}'\n"
                f"misskey_instance = '{misskey_instance}'\nmisskey_visibility='{misskey_visibility}'\n"
                f"character_limit={character_limit}")
    elif web_type == "mastodon":
        character_limit = 500
        mastodon_token = input("输入你的mastodon bot token: ")
        mastodon_instance = input(
            "输入mastodon实例地址(https://example.social): ")
        web = mastodon_instance
        mastodon_visibility = input(
            "输入mastodon嘟文类型(public, unlisted, or private): ")
        with open("credentials.py", "w") as creds:
            creds.write(
                f"telegram_token = '{telegram_token}'\nweb_type= '{web_type}'\nmastodon_token = '{mastodon_token}'\n"
                f"mastodon_instance = '{mastodon_instance}'\nmastodon_visibility={mastodon_visibility}")
    else:
        print("输入有误")

else:
    try:
        from credentials import *
        logging.info("开始运行!")
    except ImportError:
        logging.fatal(
            "credentials配置文件出错,请删除重试")
        exit(1)

'''
Bots
'''
# Mastodon
if web_type == "mastodon":
    mastodon_bot = Mastodon(access_token=mastodon_token,
                            api_base_url=mastodon_instance)  # i.e.https://mastodon.social

# Telegram
# parse mode can be either HTML or MARKDOWN
bot = telebot.TeleBot(telegram_token, parse_mode="HTML")


def ping_bots():
    if web_type == "mastodon":
        try:
            ping_mastodon = mastodon_bot.me()["username"]
            logging.info(f"Running mastodon as {ping_mastodon}")
        except:
            logging.fatal("Failed to verify mastodon access token.")
            exit(1)

    try:
        a = requests.get('https://api.telegram.org/')
        if a.status_code != 200:
            logging.info(f"无法连接至TG API服务器")
        ping_telegram = bot.get_me()
        logging.info(f"成功登入Telegram 机器人帐号 {ping_telegram.username}")
    except:
        logging.fatal('无法验证 telegram token.')
        exit(1)


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

    if len(final_text) < character_limit:
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

def uploadfile(caption,filename, mimetype):
    rmediajson = {"i": misskey_token}
    files = {'file': (filename, open(filename, "rb"), mimetype)}
    try:
        trycount=0
        mediapost = requests.post(misskey_instance+'/api/drive/files/create', timeout=10, data=rmediajson, files=files)
    except:
        trycount = trycount + 1
        if trycount >= 3:
            logging.info(f"服务器超时")
        else:
            mediapost = requests.post(misskey_instance+'/api/drive/files/create', timeout=10, data=rmediajson, files=files)
    media_id_list=[]
    media_id_list.append(json.loads(mediapost.text)["id"])
    rjson = {'text': caption, "localOnly": False, "visibility": misskey_visibility,
                 "fileIds": media_id_list, "viaMobile": False, "i": misskey_token}
    logging.info(f"上传成功")
    return rjson

'''
#Posting
'''

'''
#mastodon 有空写
@bot.channel_post_handler(content_types=["photo"])
def get_image(message):
    logging.info(f"New {message.content_type}")
    caption = footer_image(message)

    fileID = message.photo[-1].file_id
    logging.info(f"Photo ID {fileID}")

    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("tmp_img", "wb") as tmp_image:
        tmp_image.write(downloaded_file)

    media_id = mastodon_bot.media_post("tmp_img")
    posted = mastodon_bot.status_post(
        status=caption, media_ids=media_id, visibility=mastodon_visibility)
    logging.info(f"Posted: {posted['uri']}")


@bot.channel_post_handler(content_types=["video"])
def get_video(message):
    logging.info(f"New {message.content_type}")
    caption = footer_image(message)

    fileID = message.video.file_id
    logging.info(f"Video ID {fileID}")

    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("tmp_video", "wb") as tmp_video:
        tmp_video.write(downloaded_file)

    media_id = mastodon_bot.media_post(
        "tmp_video", mime_type=message.video.mime_type)
    posted = mastodon_bot.status_post(
        status=caption, media_ids=media_id, visibility=mastodon_visibility)
    logging.info(f"Posted: {posted['uri']}")


# repost text messages
@bot.channel_post_handler(content_types=["text"])
def get_text(message):
    logging.info(f"New {message.content_type}")
    status_text = footer_text(message)

    if type(status_text) == list:
        recent_post = mastodon_bot.status_post(
            status=status_text[0], visibility=mastodon_visibility)

        for i in status_text[1:]:
            time.sleep(1)
            this_recent_post = mastodon_bot.status_post(
                status=i, visibility=mastodon_visibility, in_reply_to_id=recent_post.get('id'))
            recent_post = this_recent_post
    else:
        print(status_text)
        mastodon_bot.status_post(
            status=status_text, visibility=mastodon_visibility)
'''


# Misskey

@bot.channel_post_handler(content_types=["text"])
def get_text(message):
    logging.info(f"New {message.content_type}")
    status_text = footer_text(message)
    rjson = {'text': status_text, "localOnly": False, "visibility": misskey_visibility, "viaMobile": False,
             "i": misskey_token}
    notepost = requests.post(misskey_instance + "/api/notes/create", json=rjson)
    logging.info(f"发布帖子成功")

@bot.channel_post_handler(content_types=["photo"])
def get_image(message):
    logging.info(f"New {message.content_type}")
    caption = footer_image(message)

    fileID = message.photo[-1].file_id
    logging.info(f"Photo ID {fileID}")

    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("tmp_img", "wb") as tmp_image:
        tmp_image.write(downloaded_file)
    rmediajson = {"i": misskey_token}
    files = {'file': ("tmp_img",open("tmp_img", "rb"),'image/png')}
    mediapost = requests.post(misskey_instance+'/api/drive/files/create', data=rmediajson, files=files)
    media_id_list=[]
    media_id_list.append(json.loads(mediapost.text)["id"])
    rjson = {'text': caption, "localOnly": False, "visibility": misskey_visibility, "fileIds":media_id_list, "viaMobile": False,  "i": misskey_token}
    logging.info(f"上传图片成功")
    posted = requests.post(misskey_instance + "/api/notes/create", json=rjson)
    logging.info(f"发布帖子成功")

@bot.channel_post_handler(content_types=["video"])
def get_video(message):
    logging.info(f"New {message.content_type}")
    caption = footer_image(message)

    fileID = message.video.file_id
    logging.info(f"Video ID {fileID}")

    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("tmp_video", "wb") as tmp_video:
        tmp_video.write(downloaded_file)
    if web_type == "misskey":
        rmediajson = {"i": misskey_token}
        files = {'file': ("tmp_video", open("tmp_video", "rb"))}
        mediapost = requests.post(misskey_instance + '/api/drive/files/create', data=rmediajson, files=files)
        media_id_list = []
        media_id_list.append(json.loads(mediapost.text)["id"])
        rjson = {'text': caption, "localOnly": False, "visibility": misskey_visibility,
                 "fileIds": media_id_list, "viaMobile": False, "i": misskey_token}
        logging.info(f"上传视频成功")
        posted = requests.post(misskey_instance + "/api/notes/create", json=rjson)
        logging.info(f"发布帖子成功")

    elif web_type == "mastodon":
        media_id = mastodon_bot.media_post(
            "tmp_video", mime_type=message.video.mime_type)
        posted = mastodon_bot.status_post(
            status=caption, media_ids=media_id, visibility=mastodon_visibility)
        logging.info(f"Posted: {posted['uri']}")

@bot.channel_post_handler(content_types=["audio"])
def get_audio(message):
    logging.info(f"New {message.content_type}")
    caption = footer_image(message)

    fileID = message.audio.file_id
    logging.info(f"Audio ID {fileID}")

    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("tmp_audio", "wb") as tmp_audio:
        tmp_audio.write(downloaded_file)
    rjson = uploadfile(caption, "tmp_audio", "audio/mp3")
    posted = requests.post(misskey_instance + "/api/notes/create", json=rjson)
    logging.info(f"发布帖子成功")
'''
Finally run tg polling
'''

try:
    ping_bots()
    bot.polling(interval=5)
except KeyboardInterrupt:
    exit(0)
except:
    logging.error("Something went wrong.")
    ping_bots()
    bot.polling(interval=5)
finally:
    print("\nBye!")
