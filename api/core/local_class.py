import importlib

from core.card_class import Card
from core.db_class import MongoDBHandler


class Localizator:
    DB_NAME = "tarot_cards_db"
    LANG_DEFAULT = "en"

    def __init__(self, card: Card = None, lang: str = LANG_DEFAULT):
        self.card = card
        self.lang = lang
        self.translate = importlib.import_module(f"core.lockaliz.{lang}")
        if card is not None:
            self.__load_db()

    def __load_db(self):
        card_data = self.card.get_card_data()
        if "suite" not in card_data:
            card_data["suite"] = 0

        db = MongoDBHandler().get_db()
        collection = db[self.lang] if self.lang in db.list_collection_names() else db[self.LANG_DEFAULT]

        res = collection.find_one({"_type": "suit"}, {"_id": 0, f"suit.{card_data['suite']}": 1})
        suit_map = res.get('suit', {})
        self.__suit_loc = suit_map.get(f"{card_data['suite']}", '')

        if 2 < int(card_data["value_id"]) < 10:
            self.__value_loc = card_data['value_id']
        else:
            res = collection.find_one({"_type": "value"}, {"_id": 0, f"value.{card_data['value_id']}": 1})
            self.__value_loc = res['value'][f"{card_data['value_id']}"]

        one_card = "daily" if self.card.is_daily else card_data["orientation"]

        if int(card_data["value_id"]) >= 15:
            arcana_names = {
                15: "Fool", 16: "Magician", 17: "Priestess", 18: "Empress",
                19: "Emperor", 20: "Hierophant", 21: "Lovers", 22: "Chariot",
                23: "Strength", 24: "Hermit", 25: "Wheel", 26: "Justice",
                27: "Hanged", 28: "Death", 29: "Temperance", 30: "Devil",
                31: "Tower", 32: "Star", 33: "Moon", 34: "Sun",
                35: "Judgement", 36: "World"
            }
            name = arcana_names.get(int(card_data['value_id']))
            res = collection.find_one({"_type": "arcana_meaning"}, {"_id": 0, f"{name}.{one_card}": 1})
            self.__value_mean = res[name][str(one_card)]
        else:
            suite_names = {1: "Wands", 2: "Cups", 3: "Swords", 4: "Pentacles"}
            value_names = {1: "Ace", 11: "Page", 12: "Knight", 13: "Queen", 14: "King"}
            suite = suite_names.get(int(card_data['suite']))
            value = value_names.get(card_data["value_id"], card_data["value_id"])
            res = collection.find_one({"_type": "meaning"}, {"_id": 0, f"{suite}.{value}.{one_card}": 1})
            self.__value_mean = res[suite][str(value)][str(one_card)]

    def get_taro_for_json(self) -> dict:
        return {"suit": self.__suit_loc, "value": self.__value_loc, "meaning": self.__value_mean}

    def get_local_id(self):
        return self.card.get_card_data()

    @staticmethod
    def get_string(string: str, lang: str) -> str:
        if lang is None:
            raise Exception('Language is not set')
        _lang = importlib.import_module(f"core.lockaliz.{lang}")
        return _lang.dictionary.get(string, string)
