import datetime
import time

import bcrypt

from core.db_class import MongoDBHandler


class User:
    TABLE = 'users_data'
    FILED_USERID = 'user_id'
    FIELD_USER_LANG = 'user_language'
    FIELD_DB_ID = '_id'
    FIELD_RULES = 'user_rules_accepted'
    FIELD_WEB_LOGIN = 'weblogin'
    TABLE_EMAIL = 'user_pass'
    ERROR_LOGIN_NOT_FOUND = '1'
    ERROR_INVALID_PASSWORD = '2'

    @staticmethod
    def user_check(login: str) -> bool:
        db = MongoDBHandler()
        return db.select(User.TABLE_EMAIL, 'login', login) is not None

    @staticmethod
    def user_save(login: str, password: str) -> bool:
        db = MongoDBHandler()
        if User.user_check(login):
            return False
        user = {'login': login, 'password': User.hash_password(password)}
        result = db.insert(User.TABLE_EMAIL, user)
        return not (isinstance(result, int) and result == 0)

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    @staticmethod
    def user_lang(user_tg_id: int) -> str:
        return User(user_tg_id).get_lang()

    def __init__(self, user_id: int = None, **kwargs):
        self.db = MongoDBHandler()
        self._email = kwargs.get('user_mail', None)
        self._tg_id: int = user_id
        self._id: str = ''
        self._lang_code: str = 'en'
        self._rules_accepted: int = 0
        self._subscription: int = 0
        self._info: dict = {}
        self._trial = None
        self._daily_allowance = None
        if user_id is not None:
            self.user_load()

    @property
    def subscription(self):
        return self._subscription

    def user_load(self):
        user = self.db.select(User.TABLE, User.FILED_USERID, self._tg_id)
        if not user:
            self.db.insert(User.TABLE, {
                User.FILED_USERID: self._tg_id,
                User.FIELD_USER_LANG: self._lang_code
            })
            return self.user_load()
        self._info = user
        self._id = str(user['_id'])
        self._lang_code = user.get(User.FIELD_USER_LANG, 'en')
        self._email = user.get(User.FIELD_WEB_LOGIN, None)
        self._rules_accepted = int(user.get(User.FIELD_RULES, '0'))
        self._trial = Trial(self)
        self._daily_allowance = DailyAllowance(self)

    def save(self):
        data = {
            User.FIELD_USER_LANG: self._lang_code,
            User.FIELD_RULES: str(1 if self._rules_accepted else 0)
        }
        if not self.db.update(User.TABLE, data, object_id=self._id):
            raise Exception('Failed to save User object')

    def get_id(self):
        return self._id

    def get_tg_id(self):
        return self._tg_id

    def get_email(self):
        return self._email

    def get_lang(self):
        return self._lang_code

    def set_lang(self, lang_code: str):
        self._lang_code = lang_code

    def get_rules_accepted(self) -> bool:
        return self._rules_accepted == 1

    def set_rules_accepted(self, state: bool):
        self._rules_accepted = 1 if state else 0

    def get_info(self):
        return self._info

    def get_trial(self):
        return self._trial

    def get_daily_allowance(self):
        return self._daily_allowance


class WebUser(User):
    FIELD_LOGIN = 'login'
    FIELD_PASSWORD = 'password'

    def __init__(self, user_mail: str):
        self.is_new = False
        self.db = MongoDBHandler()
        self._email = user_mail
        self._tg_id = None
        self._id = ''
        self._lang_code = 'en'
        self._rules_accepted = 0
        self._subscription = 0
        self._info = {}
        self._trial = None
        self._daily_allowance = None
        self.user_load()

    def user_load(self):
        user = self.db.select(User.TABLE_EMAIL, WebUser.FIELD_LOGIN, self._email)
        if not user:
            self.is_new = True
            return False
        self._info = user
        self._lang_code = self._info.get(User.FIELD_USER_LANG, 'en')

    def password_check(self, password: str) -> bool:
        stored = self._info.get(WebUser.FIELD_PASSWORD)
        if not stored:
            return False
        return bcrypt.checkpw(password.encode(), stored.encode())

    def get_tg_id(self):
        if self._tg_id:
            return self._tg_id
        res = self.db.select(User.TABLE, User.FIELD_WEB_LOGIN, self._email)
        if not res:
            return None
        self._tg_id = res.get(User.FILED_USERID)
        return self._tg_id


class DailyAllowance:
    FIELD_TIMESTAMP = 'timestamp'

    def __init__(self, user: User):
        self._user = user

    def get_state(self) -> dict:
        timestamp = self._user.get_info().get(DailyAllowance.FIELD_TIMESTAMP)
        if timestamp is None:
            return {'allowed': True, 'timestamp': None}
        stamp_date = timestamp.date() if hasattr(timestamp, 'date') else datetime.datetime.fromisoformat(str(timestamp)).date()
        return {'allowed': stamp_date < datetime.date.today(), 'timestamp': timestamp}


class Trial:
    TABLE = 'trials'
    FIELD_USER_ID = 'user_db_id'
    FIELD_VALID_TILL = 'trial_timestamp'
    FIELD_USER_TG_ID = 'user_id'
    FIELD_STARTED = 'trial_start'
    TRIAL_PERIOD_DAYS = 7

    STATE_ACTIVE = 3
    STATE_ENDED = 2
    STATE_NOTFOUND = 1

    def __init__(self, user: User):
        self.db = MongoDBHandler()
        self._user = user
        self._info: dict = {}
        self.load()

    def load(self):
        res = self.db.select(Trial.TABLE, Trial.FIELD_USER_ID, self._user.get_id())
        if res:
            self._info = res

    def get_state(self) -> int:
        trial_timestamp = self._info.get(Trial.FIELD_VALID_TILL)
        if not trial_timestamp:
            return Trial.STATE_NOTFOUND
        if datetime.datetime.utcnow() >= trial_timestamp:
            return Trial.STATE_ENDED
        return Trial.STATE_ACTIVE

    def start(self):
        if self._info:
            return False
        now = datetime.datetime.utcnow()
        self.db.insert(Trial.TABLE, {
            Trial.FIELD_USER_TG_ID: self._user.get_tg_id(),
            Trial.FIELD_USER_ID: self._user.get_id(),
            Trial.FIELD_STARTED: time.time(),
            Trial.FIELD_VALID_TILL: now + datetime.timedelta(days=Trial.TRIAL_PERIOD_DAYS)
        })
        return True
