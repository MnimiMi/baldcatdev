from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from routers import cards, users, stripe, contact
from core.rate_limiter import limiter

app = FastAPI(title="Tarot API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - ограничиваем до разрешённых доменов
ALLOWED_ORIGINS = [
    "https://apps.baldcat.dev",
    "https://bot.baldcat.dev",
    "https://tell.guru",
    "https://www.tell.guru",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(cards.router)
app.include_router(users.router)
app.include_router(stripe.router)
app.include_router(contact.router)


@app.get("/health")
def health():
    return {"status": "ok"}
