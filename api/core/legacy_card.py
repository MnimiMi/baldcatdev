import argparse
import base64
import io
import json

import os
from openai import OpenAI
from PIL import Image
# from click import prompt
from pymongo import MongoClient
from pymongo.errors import OperationFailure

suits = {
    1: 'Wands',
    2: 'Cups',
    3: 'Swords',
    4: 'Pentacles',
}

values = {
    1: "Ace",
    11: "Page",
    12: "Knight",
    13: "Queen",
    14: "King",
    15: "Fool",
    16: "Magician",
    17: "Priestess",
    18: "Empress",
    19: "Emperor",
    20: "Hierophant",
    21: "Lovers",
    22: "Chariot",
    23: "Justice",
    24: "Hermit",
    25: "Wheel",
    26: "Strength",
    27: "Hanged",
    28: "Death",
    29: "Temperance",
    30: "Devil",
    31: "Tower",
    32: "Star",
    33: "Moon",
    34: "Sun",
    35: "Judgement",
    36: "World"
}


class Card:

    def __init__(self, value: int, suit: int = None, orient: int = 0, lang: str = 'en'):
        self.daily = False
        self.lang = lang
        self.suit = int(suit) if suit else None
        self.value = int(value)
        self.orientation = str(orient)
        self.db = DB(lang)

    def set_daily(self):
        self.daily = True

    def get_orientation_string(self):
        if int(self.orientation) == 0:
            return 'upright'
        return 'reversed'

    def get_title(self):

        return self.__value_localize() + ' ' + self.__suit_localize()

    def get_text(self):
        return self.__meaning_localize()

    def get_image(self) -> str:
        folder = os.getenv('IMAGES_PATH', '/var/tarot_images') + '/'
        _filename = folder + self.create_image_name()
        print(_filename)
        try:
            image = Image.open(_filename)
        except FileNotFoundError:
            image = Image.open(folder + "default.jpg")
            self.orientation = '0'

        if self.orientation == '1':
            image = image.rotate(180)

        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_data = image_bytes.getvalue()

        base64_bytes = base64.b64encode(image_data)
        return base64_bytes.decode("latin-1")

    def create_image_name(self) -> str:
        if self.__is_major_arcana():
            _fn_suit = 'ha'
        else:
            _fn_suit = self.__suit_stringify().lower()
        # value
        _fn_value = self.__value_stringify().lower()

        # combine
        return f"{_fn_suit}_{_fn_value}.jpg"

    def __is_major_arcana(self) -> bool:
        return self.value > 14

    def __get_collection_name(self) -> str:
        if not self.__is_major_arcana():
            return 'meaning'
        return 'arcana_meaning'

    def __suit_localize(self) -> str:
        if self.__is_major_arcana():
            return ''
        if self.suit is not None and self.suit > 0:
            _suit_i18_collection = self.db.find(condition={'_type': 'suit'})

            if _suit_i18_collection is None:
                return '?'
            return _suit_i18_collection.get('suit').get(str(self.suit))
        return '?'

    def __value_localize(self) -> str:
        if 1 < int(self.value) < 11:
            return str(self.value)
        _value_i18 = self.db.find(condition={'_type': 'value'})

        return _value_i18.get('value').get(str(self.value))

    def __meaning_localize(self) -> str:

        _data = self.db.find(condition={'_type': self.__get_collection_name()})
        if _data is None:
            raise Exception(self.__value_stringify() + ' not found in ' + self.lang)

        if self.__is_major_arcana():
            _suit_data = _data
        else:
            _suit_data = _data.get(self.__suit_stringify())
        if _suit_data is None:
            raise Exception(self.__suit_stringify() + ' not found in ' + self.lang + ' . ' + self.__value_stringify())

        _set = _suit_data.get(self.__value_stringify())
        if _set is None:
            raise Exception('Dataset for ' + self.__value_stringify() + ' not found in ' + self.lang)
        if not self.daily:
            return _set.get(self.orientation)
        return _set.get('daily')

    def __suit_stringify(self) -> str:
        return suits[self.suit]

    def __value_stringify(self) -> str:
        """
        Finds Value string machine name by its int representation
        Not the print or localized Value!
        :return:
        """
        if 1 < self.value < 11:
            return str(self.value)
        return values[self.value]


class DB:
    LANG_DEFAULT = 'en'
    _client = None

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            cls._client = MongoClient(os.getenv('MONGO_HOST', 'tarot-mongo'))
        return cls._client

    def __init__(self, lang: str = 'en'):
        self.db = self._get_client()[os.getenv('MONGO_DB', 'tarot_cards_db')]
        try:
            self.db.validate_collection(lang)
            self.lang = lang
        except OperationFailure:
            self.lang = DB.LANG_DEFAULT

    def find(self, collection: str = None, condition: dict = None, filter_: dict = None):
        if collection is None:
            collection = self.lang
        return self.db[collection].find_one(condition, filter_)


class GPTMEANING:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.orientation_meanings = {
            0: "upright",
            1: "reversed"
        }

    @staticmethod
    def __get_language_human_name(langcode):
        names = {
            'uk': 'Ukrainian',
            'en': 'English',
            'ru': 'Russian'
        }
        return names.get(langcode, 'English')

    def __string_prepare(self, card, **kw):

        def __(card):
            return f"{card.get_title()} oriented {card.get_orientation_string()}"

        if kw.get('q_type') == 'daily':
            context = "considering this is a prediction for a current day"
        elif not kw.get('context', None):
            # triple draw (soso...)// todo: specify
            if kw.get('present_card', None):
                # FUTURE
                _pastc = __(kw.get('past_card'))
                _presc = __(kw.get('present_card'))

                context = f"assuming this is a triple draw and this card represents the future. The present is represented by {_presc} and past represented by {_pastc} in this draw"
            elif kw.get('past_card', None):
                # PRESENT
                _pastc = __(kw.get('past_card'))
                context = f"assuming this is a triple draw and this card represents the present. The past is represented by {_pastc} in this draw"
            else:
                # PAST
                context = "assuming this is a triple draw and this card represents the past"
        else:
            context = f"for {kw.get('context')}"
        return f"What does the {__(card)} card mean in tarot {context}? Answer in {kw.get('lang')} langauge."

        # 1 карта
        # Tell me the meaning of this card assuming this is a triple draw and this card represents the past
        # Tell me the meaning of this card assuming this is a triple draw and this card represents the present and past was in card[]
        # Tell me the meaning of this card assuming this is a triple draw and this card represents the future. past was in card[] and present was in card[]


    def get_ai_meaning(self, card, context = '', **kw):
        """
        Gets an AI-driven card meaning
        Args:
            card: Card
            context: ? string a context to use if any
            past_card: ? Card
            presetn_card: ? Card

        Returns:
            dictionary:
                name: string localized card title (suite + value)
                mean: string generated meaning

        """
        request = self.__string_prepare(card,
                                        q_type='daily' if card.daily else 'common',
                                        context=context,
                                        lang=self.__get_language_human_name(card.lang),
                                        **kw
                                        ) # we need UKRAINIAN here
        print(request)
        model = 'gpt-4o-mini'
        # model = 'gpt-3.5-turbo'
        print(f"Model used: {model}")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful and kind tarot telling assistant."},
                    {"role": "user","content": request }
                ]
            )
            reading = response.choices[0].message.content
        except Exception as e:
            print(f"Error: {e}")
            reading = "I'm having some trouble providing a reading right now, please try again a bit later."

        return {'name': card.get_title(), 'mean': reading}


    def get_personal_reading(self, value, suit, orientation, question, lang) -> dict:
    

        card = Card(value=int(value), suit=int(suit), orient=int(orientation), lang=lang)
        orientation_meanings = {
            0: "upright",
            1: "reversed"
        }
        # print(lang, card.get_title(), orientation_meanings[int(orientation)])
        # content = f"What does the {card.get_title()} with orientation {orientation_meanings[orientation]} tarot card mean for: {question}? Answer in {lang} langauge."
        try:

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful tarot telling assistant."},
                    {"role": "user",
                     "content": f"What does the {card.get_title()} with {orientation_meanings[int(orientation)]} orientation "
                                f"tarot card mean for: {question}? Answer in {self.__get_language_human_name(lang)} langauge."}
                ]
            )
            reading = response.choices[0].message.content
        except Exception as e:
            print(f"Error: {e}")
            reading = "I'm having some trouble providing a reading right now, please try again a bit later."

        return {'name': card.get_title(), 'mean': reading}


    def get_translation(self, string, lang) -> dict:
        _success = False
        _message = None
        # client = openai.AsyncOpenAI(
        #     api_key=self.OPENAI_API_KEY
        # )
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                # prompt=f"You are a helpful and friendly assistant. Translate {string} to {lang}.",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user",
                     "content": f"Translate {string} to {lang}."}
                ]
            )
            _translated = response.choices[0].message.content
            _success = True
        except Exception as e:
            print(f"Error: {e}")
            _translated = ""
            _message = e

        return {
            'success': _success,
            'translated': _translated,
            'message': _message
        }

    def get_rune_prediction(self, prompt: str, lang: str = "EN") -> dict:
        """
        Generate AI-powered rune prediction.
        Used for rune readings instead of tarot.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable rune reading assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            prediction = response.choices[0].message.content
            return {
                'success': True,
                'prediction': prediction
            }
        except Exception as e:
            print(f"Error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def get_imean(**kw)->str:
    card = Card(
        suit = kw.get('suit'),
        value = kw.get('value'),
        orient = kw.get('orient'),
        lang = kw.get('lang')
    )
    print(kw)
    if kw.get('daily', 0) == 1:
        card.daily = True

    kw_ = {}
    if kw.get('pst', None):
        # 11_4_0
        card_split = kw.get('pst').split('_')
        past_card = Card(
            suit=card_split[0],
            value = card_split[1],
            orient = card_split[2],
            lang = kw.get('lang')
        )
        kw_.update({'past_card': past_card})
    if kw.get('prs', None):
        # 11_4_0
        card_split = kw.get('prs').split('_')
        present_card = Card(
            suit=card_split[0],
            value = card_split[1],
            orient = card_split[2],
            lang = kw.get('lang')
        )
        kw_.update({'present_card': present_card})

    gpt = GPTMEANING()
    response = gpt.get_ai_meaning(card, kw.get('context'), **kw_)
    print(response)
    return json.dumps(response)


def get_meaning(lang: str, suit: int, value: int, orient: int = 0, is_daily: int = 0) -> str:
    """
    Gets data and returns corresponding card data taken from database

    Parameters:
        lang (str): language
        suit (int): suit
        value (int): according to table
        orient (int): orientation
        is_daily: if set get a different description

    Returns:
        str: jsoned data: 'name' string, 'mean' string, 'debug' string
    """

    card = Card(value, suit, orient, lang)
    if is_daily == 1:
        card.set_daily()
    title = card.get_title()
    text = card.get_text()
    return json.dumps({
        'name': title,
        'mean': text,
        'debug': '<ul><li>lang is {lang}</li> <li>suit is {suit}</li> <li>value is {value}</li><li>orientation is {orientation}</li>'.format(
            lang=lang, suit=suit, value=value, orientation=orient)
    })


def image_get(suit, value, orientation):
    card = Card(value=int(value), suit=int(suit), orient=int(orientation))
    return card.get_image()


def image_get_name(suit, value, orientation):
    card = Card(value=int(value), suit=int(suit), orient=int(orientation))
    return card.create_image_name()


def get_personal_meaning(*args):
    gpt = GPTMEANING()
    return json.dumps(gpt.get_personal_reading(args[0].get("v"), args[0].get("s"), args[0].get("o"), args[0].get("q"),
                                               args[0].get("l")))


def get_ai_translate(*args):
    gpt = GPTMEANING()
    return json.dumps(gpt.get_translation(args[0]['string'], args[0]['l']))


def run(args):
    """
    AKA Runner. The main method used to call appropriate methods.
    !Do not modify!

    """
    if args.m not in globals():
        print("Invalid method: " + args.m)
        return
    return globals()[args.m](vars(args))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--m', '--method', help="Method to use", type=str, required=True)
    parser.add_argument('--s', '--suit', help="Suit", type=int)
    parser.add_argument('--v', '--value', help="Value", type=int)
    parser.add_argument('--o', '--orientation', help="Orientation", type=str)
    parser.add_argument('--l', '--lang', help="Lang", type=str, default="en")
    parser.add_argument('--q', '--question', help="Question", type=str)
    parser.add_argument('--string', help="String to translate", type=str)
    args = parser.parse_args()
    print(run(args))
