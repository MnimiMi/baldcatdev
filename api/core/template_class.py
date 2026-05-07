from core.template_loader import TemplateLoader


class Template:

    def __init__(self, template_id: int, orientation: int):
        self.loader = TemplateLoader()
        _data = self.loader.load_template_by_id(template_id)
        self.__suit_id = _data[TemplateLoader.F_SUIT]
        self.__value_id = _data[TemplateLoader.F_VALUE]
        self.__interpretation = _data[TemplateLoader.F_MEANING][str(orientation)]

    # def get_suit_name(self):
    #     return cart_dict.suits_names.get(self.__suit_id)

    def get_data(self):
        # _values_temp_name = cart_dict.values_names[
        #     self.__value_id] if self.__value_id in cart_dict.values_names else str(self.__value_id)
        _return = {
            # 'value': _values_temp_name,
            'value_id': self.__value_id
        }
        if self.__value_id < 16:
            _return['suite'] = self.__suit_id
            # _return["suites_name"] = self.get_suit_name()
        _return['interpretation'] = self.__interpretation
        return _return
