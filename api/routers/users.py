import datetime
import json
import os
import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.db_class import MongoDBHandler
from core.subscription_manager import SubscriptionManager
from core.user_class import User, WebUser, Trial

router = APIRouter(prefix="/users", tags=["users"])


class LoginRequest(BaseModel):
    login: str
    pw: str


class SaveRequest(BaseModel):
    login: str
    pw: str


class LangRequest(BaseModel):
    lang: str


class RulesRequest(BaseModel):
    accepted: bool


class TarotDrawClaimRequest(BaseModel):
    chat_id: int
    message_id: int
    action: str = "tarot_quantity"


class TelegramFileCacheRequest(BaseModel):
    file_id: str


_TELEGRAM_FILE_CACHE = "telegram_file_cache"


@router.get("/telegram/file-cache/{key}")
def get_telegram_file_cache(key: str):
    cached = MongoDBHandler().select(_TELEGRAM_FILE_CACHE, "key", key)
    return {
        "success": True,
        "found": cached is not None,
        "file_id": cached.get("file_id") if cached else None,
        "updated_at": cached.get("updated_at").isoformat() if cached and cached.get("updated_at") else None,
    }


@router.put("/telegram/file-cache/{key}")
def save_telegram_file_cache(key: str, req: TelegramFileCacheRequest):
    db = MongoDBHandler().get_db()
    db[_TELEGRAM_FILE_CACHE].update_one(
        {"key": key},
        {
            "$set": {
                "file_id": req.file_id,
                "updated_at": datetime.datetime.utcnow(),
            }
        },
        upsert=True,
    )
    return {"success": True}


@router.delete("/telegram/file-cache/{key}")
def delete_telegram_file_cache(key: str):
    MongoDBHandler().get_db()[_TELEGRAM_FILE_CACHE].delete_one({"key": key})
    return {"success": True}


@router.post("/check")
def user_check(req: LoginRequest):
    user = WebUser(req.login)
    if user.is_new:
        return {"success": False, "error": User.ERROR_LOGIN_NOT_FOUND}

    if req.pw == "GOOGLE_AUTH_DUMMY_PASSWORD":
        success = True
    else:
        success = user.password_check(req.pw)

    if not success:
        return {"success": False, "error": User.ERROR_INVALID_PASSWORD}

    return {
        "success": True,
        "user": {
            "login": req.login,
            "tgid": user.get_tg_id(),
            "lang": user.get_lang(),
            "subscription_status": user.subscription,
        }
    }


@router.post("/save")
def user_save(req: SaveRequest):
    if not req.login or not req.pw:
        return {"success": False, "error_message": "Login or password not set"}
    if User.user_check(req.login):
        return {"success": False, "error_message": "Login already exists"}
    if User.user_save(req.login, req.pw):
        return {"success": True}
    return {"success": False, "error_message": "Cannot save login/password"}


_SUBSCRIPTION_CACHE_HOURS = 6


def _get_subscription(user: User) -> int:
    """Returns 1/0. Checks Stripe at most once per _SUBSCRIPTION_CACHE_HOURS."""
    info = user.get_info()
    cache = info.get("subscription_cache")
    if cache:
        age = datetime.datetime.utcnow() - cache.get("checked_at", datetime.datetime.min)
        if age < datetime.timedelta(hours=_SUBSCRIPTION_CACHE_HOURS):
            return cache.get("status", 0)

    status = 1 if SubscriptionManager(tg_id=user.get_tg_id(), email=user.get_email()).is_subscribed() else 0
    MongoDBHandler().update(
        User.TABLE,
        {"subscription_cache": {"status": status, "checked_at": datetime.datetime.utcnow()}},
        object_id=user.get_id(),
    )
    return status


@router.get("/{tg_id}")
def get_user(tg_id: int):
    user = User(tg_id)
    trial = user.get_trial()
    daily = user.get_daily_allowance()
    return {
        "success": True,
        "tg_id": tg_id,
        "lang": user.get_lang(),
        "rules_accepted": user.get_rules_accepted(),
        "subscription": _get_subscription(user),
        "trial_state": trial.get_state() if trial else Trial.STATE_NOTFOUND,
        "daily": daily.get_state() if daily else {"allowed": True, "timestamp": None},
    }


@router.put("/{tg_id}/lang")
def set_lang(tg_id: int, req: LangRequest):
    user = User(tg_id)
    user.set_lang(req.lang)
    user.save()
    return {"success": True}


@router.put("/{tg_id}/rules")
def accept_rules(tg_id: int, req: RulesRequest):
    user = User(tg_id)
    user.set_rules_accepted(req.accepted)
    user.save()
    return {"success": True}


@router.post("/{tg_id}/trial")
def start_trial(tg_id: int):
    user = User(tg_id)
    started = user.get_trial().start()
    return {"success": started, "message": "Trial already active" if not started else "Trial started"}


@router.post("/{tg_id}/daily")
def mark_daily(tg_id: int):
    db = MongoDBHandler()
    updated = db.update("users_data", {"timestamp": datetime.datetime.now()}, "user_id", tg_id)
    if not updated:
        db.insert("users_data", {"user_id": tg_id, "timestamp": datetime.datetime.now()})
    return {"success": True}


@router.post("/{tg_id}/tarot-draws/claim")
def claim_tarot_draw(tg_id: int, req: TarotDrawClaimRequest):
    db = MongoDBHandler().get_db()
    claims = db["tarot_draw_claims"]
    claims.create_index("created_at", expireAfterSeconds=60 * 60 * 24)

    claim_id = f"{req.action}:{tg_id}:{req.chat_id}:{req.message_id}"
    result = claims.update_one(
        {"_id": claim_id},
        {
            "$setOnInsert": {
                "tg_id": tg_id,
                "chat_id": req.chat_id,
                "message_id": req.message_id,
                "action": req.action,
                "created_at": datetime.datetime.utcnow(),
            }
        },
        upsert=True,
    )
    return {"success": True, "claimed": result.upserted_id is not None}


_SESSION_TABLE = "sessions"
_SESSION_DAYS = 7


def _create_session(user_login: str) -> str:
    session_id = secrets.token_hex(32)
    MongoDBHandler().insert(_SESSION_TABLE, {
        "session_id": session_id,
        "user_login": user_login,
        "expires_at": datetime.datetime.utcnow() + datetime.timedelta(days=_SESSION_DAYS),
    })
    return session_id


def _get_session(session_id: str) -> dict | None:
    session = MongoDBHandler().select(_SESSION_TABLE, "session_id", session_id)
    if not session:
        return None
    if session["expires_at"] < datetime.datetime.utcnow():
        return None
    return session


class SessionCheckRequest(BaseModel):
    session_id: str


@router.post("/login")
def web_login(req: LoginRequest):
    user = WebUser(req.login)
    if user.is_new:
        return {"success": False, "error": User.ERROR_LOGIN_NOT_FOUND}
    if not user.password_check(req.pw):
        return {"success": False, "error": User.ERROR_INVALID_PASSWORD}
    session_id = _create_session(req.login)
    return {"success": True, "user": {"login": req.login, "session_id": session_id}}


@router.post("/register")
def web_register(req: SaveRequest):
    if not req.login or not req.pw:
        return {"success": False, "error_message": "Login or password not set"}
    if User.user_check(req.login):
        return {"success": False, "error_message": "Login already exists"}
    if not User.user_save(req.login, req.pw):
        return {"success": False, "error_message": "Cannot save login/password"}
    session_id = _create_session(req.login)
    return {"success": True, "user": {"login": req.login, "session_id": session_id}}


@router.post("/session")
def check_web_session(req: SessionCheckRequest):
    session = _get_session(req.session_id)
    if not session:
        return {"success": False}
    return {"success": True, "user": {"login": session["user_login"], "session_id": req.session_id}}


class GoogleAuthRequest(BaseModel):
    token: str


@router.post("/google-auth")
def google_auth(req: GoogleAuthRequest):
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests

    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    try:
        idinfo = id_token.verify_oauth2_token(req.token, google_requests.Request(), client_id)
        email = idinfo["email"]
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    user = WebUser(email)
    if user.is_new:
        if not User.user_save(email, "GOOGLE_AUTH_DUMMY_PASSWORD"):
            raise HTTPException(status_code=500, detail="Cannot create user")

    return {
        "success": True,
        "user": {
            "login": email,
            "tgid": user.get_tg_id(),
            "lang": user.get_lang(),
            "subscription_status": user.subscription,
        }
    }


class WeblinkRequest(BaseModel):
    email: str


@router.get("/email/{email}/exists")
def email_exists(email: str):
    """Check if email exists in user_pass (web login)"""
    return {"exists": User.user_check(email)}


@router.get("/email/{email}/linked")
def email_linked(email: str):
    """Check if email is already linked to any Telegram user"""
    db = MongoDBHandler()
    result = db.select(User.TABLE, User.FIELD_WEB_LOGIN, email)
    return {"linked": result is not None}


@router.put("/{tg_id}/weblogin")
def set_weblogin(tg_id: int, req: WeblinkRequest):
    """Link a web email to a Telegram user"""
    db = MongoDBHandler()
    user = User(tg_id)
    updated = db.update(User.TABLE, {User.FIELD_WEB_LOGIN: req.email}, object_id=user.get_id())
    return {"success": updated}
