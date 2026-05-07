class CardInfo:
    def __init__(self, card_data):
        self.value = card_data.get('_value')
        self.suite = card_data.get('_suite')
        self.orientation = card_data.get('_orientation')

    def get_info_for_out(self):
        # Make a message on JSON based
        message = f"Card Value: {self.value}\n"
        message += f"Card Suite: {self.suite}\n"
        message += f"Card Orientation: {self.orientation}\n"

        return message
