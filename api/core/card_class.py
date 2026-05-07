import random

from core.template_class import Template


class Card:
    def __init__(self, template_id: int):
        self.__is_daily = False
        self.__orientation = self.__set_orientation()
        self.__template_id = template_id
        self.__load_template()
        self.__context = ''

    @property
    def context(self):
        return self.__context

    @context.setter
    def context(self, new_context: str):
        self.__context = new_context

    @property
    def orientation(self):
        return self.__orientation

    @orientation.setter
    def orientation(self, new_orientation: int):
        self.__orientation = new_orientation

    @property
    def is_daily(self):
        return self.__is_daily

    @is_daily.setter
    def is_daily(self, value):
        self.__is_daily = value

        if value:
            self.__load_template()


    def __set_orientation(self) -> int:
        return random.randint(0, 1)

    def __load_template(self):
        self.__template = Template(self.__template_id, self.__orientation)

    def get_card_data(self) -> dict:
        _data = self.__template.get_data()
        _data['orientation'] = self.__orientation

        return _data
