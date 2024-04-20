
import json
import os
from os import environ
from shutil import rmtree

import instaloader
from i18n import t
from telebot.async_telebot import AsyncTeleBot
from telebot.formatting import escape_markdown
from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           InputMediaPhoto)

from helpers import get_user_dir
from instagram import Instagram

TELEGRAM_BOT_TOKEN = environ.get("TELEGRAM_BOT_TOKEN",
                                 "6809165420:AAE80S6kn5B4ERj8BbC0AZPzdViH1xxfd3M")

bot = AsyncTeleBot(TELEGRAM_BOT_TOKEN, parse_mode='MarkdownV2')


async def start_bot():
    print("Starting telegram bot")
    try:
        await bot.infinity_polling()
    except Exception as e:
        print('Error starting telegram bot')
        print(e)


@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    try:
        get_user_dir(message)
        await bot.send_message(
            message.chat.id, t('telegram.start'))

    except Exception as e:
        await bot.send_message(message.chat.id, t(
            'telegram.start_error', error=str(e)))


@bot.message_handler(commands=['clear'])
async def clear_data(message):
    rmtree(get_user_dir(message))
    await bot.send_message(message.chat.id, t('clear-success'))


@bot.message_handler(regexp="https://.*\\.instagram\\.com/.*")
async def instagram_download(message):
    start_msg = await bot.send_message(message.chat.id, t('download.start'))

    try:
        insta = Instagram(get_user_dir(message))
        post = await insta.get_post(message.text)

        if post.is_video:
            await bot.send_video(message.chat.id, post.video_url, caption=escape_markdown(post.caption, version=2))
        else:
            imgs_nodes = post.get_sidecar_nodes()
            imgs = [InputMediaPhoto(img.display_url) for img in imgs_nodes]
            imgs[0].caption = post.caption
            await bot.send_media_group(message.chat.id, imgs)

        await bot.delete_message(message.chat.id, message.message_id)

    except instaloader.LoginRequiredException as e:
        await login_required(message, "instagram")

    except Exception as e:
        if "HTTP error code 401" in str(e):
            await login_required(message, "instagram")
        else:
            await bot.reply_to(message, t('download.error', error=str(e)))

    finally:
        await bot.delete_message(message.chat.id, start_msg.message_id)


@ bot.callback_query_handler(func=lambda call: True)
async def callback_query(call):
    chat_id = call.message.chat.id

    if call.data == "instagram_login":
        await bot.send_message(
            chat_id, t('login.start', service="instagram"))


@bot.message_handler(regexp="/auth instagram .* .*")
async def instagram_login(message):
    try:
        words = message.text.strip().replace('\n', ' ').split(" ")
        if len(words) < 4:
            await bot.reply_to(message, t('login.invalid'))
            return
        username, password = words[2:4]

        await bot.delete_message(message.chat.id, message.message_id)

        insta = Instagram(get_user_dir(message))

        insta.data.default_user = username
        if username in insta.data.users:
            insta.data.write_to_file()
            await bot.send_message(message.chat.id, t('login.exists', username=username))
            return

        await bot.send_message(message.chat.id, t('login.progress'))

        await insta.login(username, password)

        await bot.send_message(message.chat.id, t('login.success', username=username))
    except Exception as e:
        await bot.send_message(message.chat.id, t('login.error', error=str(e)))


async def login_required(message, type):
    button = InlineKeyboardButton('Login', callback_data=type + '_login')
    keyboard = InlineKeyboardMarkup()
    keyboard.add(button)

    await bot.reply_to(message, t('login.required'), reply_markup=keyboard)
