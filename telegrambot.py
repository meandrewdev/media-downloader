
import logging
import os
from datetime import datetime
from os import environ
from shutil import rmtree
from urllib import request

import instaloader
from i18n import t
from telebot.async_telebot import AsyncTeleBot
from telebot.formatting import escape_markdown
from telebot.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto)

from helpers import get_user_dir
from instagram import Instagram

TELEGRAM_BOT_TOKEN = environ.get("TELEGRAM_BOT_TOKEN")
MAX_CAPTION_LENGTH = 2500

bot = AsyncTeleBot(TELEGRAM_BOT_TOKEN, parse_mode='MarkdownV2')
logger = logging.getLogger('media-downloader')
logging.basicConfig(filename='app.log', level=logging.INFO)


async def start_bot():
    print("Starting telegram bot")
    try:
        await bot.infinity_polling()
    except Exception as e:
        print('Error starting telegram bot')
        logger.exception(e)


@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    try:
        get_user_dir(message)
        await bot.send_message(
            message.chat.id, t('telegram.start'))

    except Exception as e:
        logger.exception(e)
        await bot.send_message(message.chat.id, t(
            'telegram.start_error', error=str(e)))


@bot.message_handler(commands=['clear'])
async def clear_data(message):
    rmtree(get_user_dir(message))
    await bot.send_message(message.chat.id, t('clear-success'))


@bot.message_handler(regexp="https://.*\\.instagram\\.com/.*")
async def instagram_download(message):
    start_msg = await bot.reply_to(message, t('download.start'))

    try:
        insta = Instagram(get_user_dir(message))
        post = await insta.get_post(message.text)

        post_caption = post.caption or ''
        post_caption = post_caption[:MAX_CAPTION_LENGTH] + '...' if len(
            post_caption) > MAX_CAPTION_LENGTH else post_caption

        if post.is_video:
            caption = "{}\n\n[{}]({})".format(escape_markdown(
                post_caption), t('telegram.post-link'), message.text)

            try:
                video_name = str(datetime.now().timestamp()) + \
                    post.shortcode + ".mp4"
                request.urlretrieve(post.video_url, video_name)
                with open(video_name, 'rb') as video:
                    await bot.send_video(message.chat.id, video, caption=caption, parse_mode=None)
            except Exception as e:
                logger.exception(e)
                await bot.reply_to(message, t('download.error', error=str(e)))
                return
            finally:
                if os.path.exists(video_name):
                    os.remove(video_name)

        else:
            imgs_nodes = post.get_sidecar_nodes()
            imgs = [InputMediaPhoto(img.display_url) for img in imgs_nodes]
            imgs[0].caption = caption = "{}\n\n{}".format(
                post_caption, message.text)
            await bot.send_media_group(message.chat.id, imgs)

        await bot.delete_message(message.chat.id, message.message_id)

    except instaloader.LoginRequiredException as e:
        await login_required(message, "instagram")

    except Exception as e:
        logger.exception(e)
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
        logger.exception(e)
        await bot.send_message(message.chat.id, t('login.error', error=str(e)))


async def login_required(message, type):
    button = InlineKeyboardButton(
        t('login.button'), callback_data=type + '_login')
    keyboard = InlineKeyboardMarkup()
    keyboard.add(button)

    await bot.reply_to(message, t('login.required'), reply_markup=keyboard)
