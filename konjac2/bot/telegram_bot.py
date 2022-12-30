import requests
from telegram import Update
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import CallbackContext
from konjac2.config import settings


def startup_bot():
    updater = Updater(token=settings.telegram_token, use_context=True)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)
    updater.start_polling()


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def say_something(something):
    requests.get(
        f"https://api.telegram.org/{settings.telegram_bot}/sendMessage",
        params={
            "parse_mode": "HTML",
            "chat_id": "1068224058",
            "text": something,
        },
    )
