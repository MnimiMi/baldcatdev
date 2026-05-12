import os
import aiohttp
import logging

API_BASE = os.getenv('TAROT_API_URL', 'http://tarot-api:8000')

logger = logging.getLogger(__name__)


async def _get(path: str, params: dict = None, tg_id: int = None) -> dict:
    """GET request with optional tg_id for rate limiting"""
    url = API_BASE + path
    
    # Add tg_id to params for rate limiting
    if tg_id and params is not None:
        params['tg_id'] = tg_id
    elif tg_id and params is None:
        params = {'tg_id': tg_id}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=20)) as r:
            r.raise_for_status()
            return await r.json()


async def _post(path: str, data: dict, tg_id: int = None) -> dict:
    """POST request with optional tg_id for rate limiting"""
    url = API_BASE + path
    
    # Add tg_id to data for rate limiting
    if tg_id:
        data['tg_id'] = tg_id
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=20)) as r:
            r.raise_for_status()
            return await r.json()


async def _put(path: str, data: dict, tg_id: int = None) -> dict:
    """PUT request with optional tg_id for rate limiting"""
    url = API_BASE + path
    
    # Add tg_id to data for rate limiting
    if tg_id:
        data['tg_id'] = tg_id
    
    async with aiohttp.ClientSession() as session:
        async with session.put(url, json=data, timeout=aiohttp.ClientTimeout(total=20)) as r:
            r.raise_for_status()
            return await r.json()


async def draw(size: int, lang: str, tg_id: int = None) -> dict:
    """Draw tarot cards, with optional tg_id for rate limiting"""
    return await _get('/cards/draw', {'size': size, 'lang': lang}, tg_id)


async def get_user(tg_id: int) -> dict:
    return await _get(f'/users/{tg_id}')


async def save_lang(tg_id: int, lang: str) -> dict:
    return await _put(f'/users/{tg_id}/lang', {'lang': lang})


async def accept_rules(tg_id: int) -> dict:
    return await _put(f'/users/{tg_id}/rules', {'accepted': True})


async def start_trial(tg_id: int) -> dict:
    return await _post(f'/users/{tg_id}/trial', {})


async def mark_daily(tg_id: int) -> dict:
    return await _post(f'/users/{tg_id}/daily', {})


async def claim_tarot_draw(tg_id: int, chat_id: int, message_id: int) -> dict:
    return await _post(
        f'/users/{tg_id}/tarot-draws/claim',
        {
            'chat_id': chat_id,
            'message_id': message_id,
            'action': 'tarot_quantity',
        }
    )


async def get_cached_file_id(key: str) -> str | None:
    result = await _get(f'/users/telegram/file-cache/{key}')
    if result.get('found'):
        return result.get('file_id')
    return None


async def save_cached_file_id(key: str, file_id: str) -> dict:
    return await _put(f'/users/telegram/file-cache/{key}', {'file_id': file_id})


async def delete_cached_file_id(key: str) -> dict:
    url = API_BASE + f'/users/telegram/file-cache/{key}'
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, timeout=aiohttp.ClientTimeout(total=20)) as r:
            r.raise_for_status()
            return await r.json()


async def get_string(key: str, lang: str, tg_id: int = None) -> str:
    """Get localized string, with optional tg_id for rate limiting"""
    result = await _get('/cards/string', {'key': key, 'lang': lang}, tg_id)
    return result.get('message', key)


async def get_random_copy(key: str, lang: str, tg_id: int = None) -> str:
    result = await _get('/cards/random-copy', {'key': key, 'lang': lang}, tg_id)
    return result.get('message', key)


async def get_imean(val: int, suite: int, orient: int, lang: str, 
                   context: str = None, pst: str = None, prs: str = None,
                   tg_id: int = None) -> dict:
    """Get AI meaning for a card (rate limited: 5/min)"""
    params = {
        'val': val,
        'suite': suite,
        'orient': orient,
        'lang': lang
    }
    if context:
        params['context'] = context
    if pst:
        params['pst'] = pst
    if prs:
        params['prs'] = prs
    
    return await _get('/cards/imean', params, tg_id)


async def get_mean_personal(val: int, suite: int, orient: int, lang: str, 
                            context: str = "", tg_id: int = None) -> dict:
    """Get personal reading for a card (rate limited: 5/min)"""
    params = {
        'val': val,
        'suite': suite,
        'orient': orient,
        'lang': lang,
        'context': context
    }
    return await _get('/cards/mean_personal', params, tg_id)


async def email_exists(email: str) -> bool:
    result = await _get(f'/users/email/{email}/exists')
    return result.get('exists', False)


async def email_linked(email: str) -> bool:
    result = await _get(f'/users/email/{email}/linked')
    return result.get('linked', False)


async def set_weblogin(tg_id: int, email: str) -> bool:
    result = await _put(f'/users/{tg_id}/weblogin', {'email': email})
    return result.get('success', False)


async def get_rune_prediction(rune_description: str, language: str = "EN", 
                              tg_id: int = None) -> dict:
    """Get AI prediction for a rune (rate limited: 5/min)"""
    return await _post('/cards/rune/predict', {
        'rune_description': rune_description,
        'language': language
    }, tg_id)
