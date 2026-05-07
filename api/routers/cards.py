import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from core.deck_class import Deck
from core.legacy_card import Card, GPTMEANING, get_meaning, get_imean

router = APIRouter(prefix="/cards", tags=["cards"])


class RunePredictRequest(BaseModel):
    rune_description: str
    language: str = "EN"


def _meaning_shell(api_path: str) -> HTMLResponse:
    return HTMLResponse(f"""<!DOCTYPE html>
<html bgcolor="#0f0e13">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ min-height: 100%; background: #0f0e13; }}
    body {{
      color: #f0e6d3;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      min-height: 100vh;
      padding: 28px 20px 48px;
    }}
    .sigil-wrap {{
      display: flex;
      justify-content: center;
      margin-bottom: 20px;
      transition: opacity .35s ease, transform .35s ease;
    }}
    .sigil-wrap svg {{ width: 110px; height: 110px; }}
    .ring-1 {{ transform-origin: 130px 130px; animation: spinFast 6s linear infinite; }}
    .ring-2 {{ transform-origin: 130px 130px; animation: spinMid 11s linear infinite reverse; }}
    .ring-3 {{ transform-origin: 130px 130px; animation: spinSlow 20s linear infinite; }}
    @keyframes spinFast {{ to {{ transform: rotate(360deg); }} }}
    @keyframes spinMid  {{ to {{ transform: rotate(-360deg); }} }}
    @keyframes spinSlow {{ to {{ transform: rotate(360deg); }} }}
    h2 {{
      font-size: 1rem;
      color: #c6a85f;
      text-align: center;
      margin-bottom: 16px;
      letter-spacing: 0.06em;
      min-height: 1.25rem;
    }}
    .divider {{
      width: 60px; height: 1px;
      background: linear-gradient(to right, transparent, #c6a85f, transparent);
      margin: 0 auto 20px;
    }}
    .loading-text {{
      color: #c6a85f;
      text-align: center;
      letter-spacing: .08em;
      text-transform: uppercase;
      font-size: .72rem;
      opacity: .78;
    }}
    p {{
      font-size: 0.92rem;
      line-height: 1.75;
      margin-bottom: 12px;
      opacity: 0.9;
      white-space: pre-wrap;
    }}
    body.is-ready .sigil-wrap {{
      opacity: .82;
      transform: scale(.86);
    }}
  </style>
</head>
<body>
  <div class="sigil-wrap">
    <svg viewBox="0 0 260 260" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="3.5" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <g class="ring-3">
        <circle cx="130" cy="130" r="118" fill="none" stroke="#c6a85f"
                stroke-width="1" stroke-dasharray="6 14" opacity="0.55"/>
      </g>
      <g class="ring-2">
        <circle cx="130" cy="130" r="90" fill="none" stroke="#c6a85f"
                stroke-width="1.2" stroke-dasharray="3 9" opacity="0.65" filter="url(#glow)"/>
      </g>
      <g class="ring-1">
        <circle cx="130" cy="130" r="62" fill="none" stroke="#d4a850"
                stroke-width="1.5" stroke-dasharray="2 5" opacity="0.9" filter="url(#glow)"/>
      </g>
    </svg>
  </div>
  <h2 id="title"></h2>
  <div class="divider"></div>
  <main id="content"><div class="loading-text">Reading the cards</div></main>
  <script>
    const tg = window.Telegram?.WebApp;
    tg?.setHeaderColor?.('#0f0e13');
    tg?.setBackgroundColor?.('#0f0e13');
    tg?.ready?.();

    const params = new URLSearchParams(window.location.search);
    const url = new URL({api_path!r}, window.location.origin);
    url.search = params.toString();

    function addParagraphs(text) {{
      const content = document.getElementById('content');
      content.textContent = '';
      String(text || '').split('\\n').filter(Boolean).forEach((line) => {{
        const p = document.createElement('p');
        p.textContent = line;
        content.appendChild(p);
      }});
    }}

    fetch(url)
      .then((response) => {{
        if (!response.ok) throw new Error('Request failed');
        return response.json();
      }})
      .then((data) => {{
        document.body.classList.add('is-ready');
        document.getElementById('title').textContent = data.name || '';
        addParagraphs(data.mean || data.text || data.prediction || '');
      }})
      .catch(() => {{
        document.body.classList.add('is-ready');
        addParagraphs("I'm having some trouble providing a reading right now, please try again a bit later.");
      }});
  </script>
</body>
</html>""")


@router.get("/draw")
def draw(size: int = Query(1, ge=1, le=10), lang: str = Query("en")):
    deck = Deck(size, lang)
    if not deck.draw():
        raise HTTPException(status_code=500, detail="Unable to draw cards")
    cards_raw = json.loads(deck.get_cards_json())
    cards = [
        {"value": c["_value"], "suit": c["_suite"], "orient": c["_orientation"],
         "suit_name": c["suit"], "value_name": c["value"], "meaning": c["meaning"]}
        for c in cards_raw
    ]
    return {"success": True, "cards": cards, "desk": cards}


@router.get("/mean")
def mean(val: int, suite: int = 0, orient: int = 0, lang: str = "en", daily: int = 0):
    result = get_meaning(lang=lang, suit=suite, value=val, orient=orient, is_daily=daily)
    return json.loads(result)


@router.get("/imean")
def imean(
    val: int,
    suite: int = 0,
    orient: int = 0,
    lang: str = "en",
    daily: int = 0,
    context: str = None,
    pst: str = None,
    prs: str = None,
):
    result = get_imean(
        suit=suite, value=val, orient=orient, lang=lang,
        daily=daily, context=context, pst=pst, prs=prs
    )
    return json.loads(result)


@router.get("/mean_personal")
def mean_personal(val: int, suite: int = 0, orient: int = 0, lang: str = "en", context: str = ""):
    gpt = GPTMEANING()
    result = gpt.get_personal_reading(val, suite, orient, context, lang)
    return result


@router.get("/meaning_personal", response_class=HTMLResponse)
def meaning_personal_page(val: int, suite: int = 0, orient: int = 0, lang: str = "en", context: str = ""):
    return _meaning_shell("/cards/mean_personal")


@router.get("/meaning", response_class=HTMLResponse)
def meaning_page(val: int, suite: int = 0, orient: int = 0, lang: str = "en",
                 daily: int = 0, pst: str = None, prs: str = None):
    return _meaning_shell("/cards/imean")


@router.get("/image")
def image(val: int, suite: int = 0, orient: int = 0, lang: str = "en"):
    card = Card(value=val, suit=suite, orient=orient, lang=lang)
    import base64
    image_b64 = card.get_image()
    image_bytes = base64.b64decode(image_b64.encode("latin-1"))
    return Response(content=image_bytes, media_type="image/png")


@router.get("/image_name")
def image_name(val: int, suite: int = 0, orient: int = 0, lang: str = "en"):
    card = Card(value=val, suit=suite, orient=orient, lang=lang)
    name = card.create_image_name()
    return {"success": True, "name": name, "data": name}


@router.get("/string")
def get_string(key: str = Query(...), lang: str = Query("en")):
    from core.local_class import Localizator
    message = Localizator.get_string(key, lang)
    return {"success": True, "message": message}


@router.get("/translate")
def translate(string: str, lang: str = "en"):
    gpt = GPTMEANING()
    return gpt.get_translation(string, lang)


@router.post("/rune/predict")
def rune_predict(req: RunePredictRequest):
    gpt = GPTMEANING()
    prompts = {
        "RU": f"На основе следующей руны: {req.rune_description}, дайте предсказание.",
        "UA": f"На основі наступної руни: {req.rune_description}, дайте передбачення.",
        "EN": f"Based on the following rune: {req.rune_description}, provide a prediction.",
        "FR": f"Basé sur la rune suivante: {req.rune_description}, faites une prédiction.",
    }
    prompt = prompts.get(req.language.upper(), prompts["EN"])
    return gpt.get_rune_prediction(prompt, req.language)
