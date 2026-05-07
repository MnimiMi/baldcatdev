import json

from Crypto.Random import get_random_bytes

from core.card_class import Card
from core.local_class import Localizator
from core.template_loader import TemplateLoader


class Deck:

    def __init__(self, total, lang, context=''):

        self.__cards_ids = []
        self.__cards = []
        self.__templates_used = set()
        self.__total = total  # Использование переданного параметра total
        self.__localisation = lang
        self.__context = context

    def draw(self):
        """
        Initialize deck
        :return: bool
        """
        self.__cards = []  # Инициализация списка карт только один раз
        loader = TemplateLoader()
        self.__cards_ids = loader.load_card_ids()
        if not self.__cards_ids:
            raise Exception("Could not load cards")
        for _ in range(self.__total):
            _crd = self.__draw_a_card()
            if not _crd:
                return False
        return True

    def __draw_a_card(self):
        """
        Draw a card with a random template
        :return: bool
        """

        templates_available = set(self.__cards_ids) - self.__templates_used

        if not templates_available:
            print("No more cards")
            return False

        # Генерируем случайный байт
        random_byte = get_random_bytes(1)

        # Преобразуем в целое число от 0 до len(templates_available)
        random_index = int.from_bytes(random_byte, byteorder='big') % len(templates_available)

        template_id = list(templates_available)[random_index]

        self.__templates_used.add(template_id)

        _card = Card(template_id)
        if self.__context != '':
            _card.context = self.__context


        if self.__total == 1:
            _card.is_daily = True

        _card_localized = Localizator(_card, self.__localisation)
        self.__cards.append(_card_localized)

        return True

    def get_cards(self):
        return self.__cards

    def get_cards_json(self):
        """
        Return cards as json
        :return:
        """
        cards_dict_list = []  # Создаем список словарей для каждой карты
        for card in self.__cards:
            _card_data = card.get_taro_for_json()
            _card_machine_data = card.get_local_id()
            # print(_card_machine_data)
            _card_data['_value'] = _card_machine_data['value_id']
            _card_data['_suite'] = _card_machine_data.get('suite')
            _card_data['_orientation'] = int(_card_machine_data['orientation'])

            cards_dict_list.append(_card_data)

        return json.dumps(cards_dict_list, ensure_ascii=False, indent=4)
