import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
TARO_TOKEN = os.getenv("TARO_TOKEN")
TAROT_PAY_TOKEN = os.getenv("TAROT_PAY_TOKEN")
SECRET_KEY_STRIPE = os.getenv("SECRET_KEY_STRIPE")
I_AM_AT_HOME = os.getenv("I_AM_AT_HOME") == "true"
ABOUT_MESSAGE = ("👋 bot-tarot is a bot for Tarot Readings, we bridge the ancient wisdom of tarot cards "
                 "with the "
                 "cutting-edge power of artificial intelligence, providing a unique and insightful experience "
                 "for seekers of guidance and enlightenment. Our business is a fusion of tradition and technology, "
                 "where the mystique of the past meets the innovation of the future. "
                 "What sets bot-tarot apart is our commitment to authenticity and personalization. "
                 "We've meticulously crafted our tarot reading bot to capture the essence of traditional "
                 "tarot readings while infusing it with AI-generated responses. "
                 "Our AI has been trained to replicate the depth and wisdom of experienced tarot card readers,"
                 " providing users with enlightening and thought-provoking answers to their questions.\n")
TELEGRAM_SUPPORT_CHAT_ID = os.getenv("TELEGRAM_SUPPORT_CHAT_ID")
WEATHER_TOKEN = os.getenv("WEATHER_TOKEN")#weatherapi
RULES_MESSAGE = ("The tarot readings provided by this bot are for entertainment purposes only. "
                 "They should not be considered as professional advice or predictions of future events."
                 "The interpretations and meanings presented in the readings are based on traditional tarot "
                 "card meanings. However, they may not always apply to every situation or person. "
                 "The bot generates readings randomly using algorithms. "
                 "It does not have real psychic or predictive abilities. "
                 "The accuracy and relevance of any reading cannot be guaranteed.Users should carefully "
                 "consider all options and exercise their own judgement when making life decisions. Do not make "
                 "significant choices based solely on a reading received from this bot.This service is not intended "
                 "as a substitute for consultation with lawyers, financial advisors, therapists, or other licensed "
                 "professionals. Consult appropriate experts for guidance on specific situations.The creators and "
                 "operators of this bot accept no liability for the accuracy, relevance or outcome of any reading. "
                 "Use of this service is at the user's sole discretion and risk.By requesting or receiving a tarot "
                 "reading from this bot, the user acknowledges that the readings are for entertainment only. The user "
                 "agrees not to hold the creators, operators or providers of this bot legally responsible for any "
                 "reading or interpretation.")

REPLY_TO_THIS_MESSAGE = os.getenv("REPLY_TO_THIS_MESSAGE", "REPLY_TO_THIS")
WRONG_REPLY = os.getenv("REPLY_TO_THIS_MESSAGE", "REPLY_TO_THIS")
