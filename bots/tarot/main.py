import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.executor import start_webhook

import TG.config as config
from TG import main_tg_request, help_request, check_web_login, payment, support_chat
from TG.weather import weather_main

logging.basicConfig(level=logging.INFO)

WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', 'https://bot.baldcat.dev')
WEBHOOK_PATH = f"/webhook/{config.TARO_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT', 8080))

storage = MemoryStorage()
bot = Bot(token=config.TARO_TOKEN)
dp = Dispatcher(bot, storage=storage)

main_tg_request.main_requests_handler(dp)
weather_main.reg_weather(dp)
check_web_login.check_web_handler(dp)
payment.payment_handler(dp)
support_chat.reg_handlers_sup(dp)
dp.middleware.setup(LoggingMiddleware())


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set: {WEBHOOK_URL}")


async def on_shutdown(dp):
    await bot.delete_webhook()
    await storage.close()
    await bot.close()


if __name__ == '__main__':
    logging.info("Starting bot in webhook mode.")
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
