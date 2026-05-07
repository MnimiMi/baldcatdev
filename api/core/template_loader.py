from core.db_class import MongoDBHandler


class TemplateLoader:
    _templates = None
    F_EXPOPRT_ID = "id"
    F_MEANING = 'meaning'
    F_SUIT = 'suit'
    F_VALUE = 'value'
    F_DB_ID = '_id'

    def __init__(self):
        self.db = MongoDBHandler()

    def load_template_by_id(self, template_id):
        _const_ = TemplateLoader
        collection = self.db.get_db()["cards"]
        query = {TemplateLoader.F_DB_ID: template_id}
        template = collection.find_one(query)
        if template:
            card_template = {
                _const_.F_EXPOPRT_ID: template[_const_.F_DB_ID],
                _const_.F_MEANING: template['meaning'],
                _const_.F_SUIT: template['suit'],
                _const_.F_VALUE: template['value']
            }
            return card_template
        else:
            return None

    def load_card_ids(self):
        loader = TemplateLoader()
        collection = self.db.get_db()["cards"]
        ids = collection.distinct(TemplateLoader.F_DB_ID)
        return ids
