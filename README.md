# 🐈‍⬛ baldcatdev

> 🔮 Live project: [tell.guru](https://tell.guru) — AI-powered tarot & rune readings via Telegram bot and web app.

---

## What is this?

A distributed app that delivers AI-generated tarot and rune readings across two platforms — a Telegram bot and a Vue 3 web app. Everything runs in Docker behind Traefik, with OpenAI doing the interpretations and Stripe handling subscriptions.

---

## Architecture

```mermaid
graph TD
    A[Internet] --> B[Traefik\nreverse proxy · TLS · routing]

    B -->|bot.baldcat.dev| C[tarot-bot\nAiogram · webhook]
    B -->|apps.baldcat.dev| D[tarot-api · FastAPI]
    B -->|tell.guru| E[tellguru-nginx\nVue 3 SPA]

    E -->|API calls| D

    C --> F[(MongoDB)]
    D --> F

    D --> G[OpenAI\nGPT-4o-mini]
    D --> H[Stripe\nsubscriptions]
    D --> I[Resend\nemail]

    style B fill:#7F77DD,color:#fff
    style C fill:#1D9E75,color:#fff
    style D fill:#378ADD,color:#fff
    style E fill:#9B59B6,color:#fff
    style F fill:#639922,color:#fff
    style G fill:#D85A30,color:#fff
    style H fill:#BA7517,color:#fff
    style I fill:#D4537E,color:#fff
```

---

## Tech Stack

### Backend
![Python](https://img.shields.io/badge/Python-3.11-3776ab?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-TTL_collections-47a248?logo=mongodb&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe-subscriptions-635bff?logo=stripe&logoColor=white)

### Frontend
![Vue 3](https://img.shields.io/badge/Vue-3-42b883?logo=vue.js&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-8-646cff?logo=vite&logoColor=white)
![Pinia](https://img.shields.io/badge/Pinia-3-ffd859?logo=pinia&logoColor=black)

### Bot
![Aiogram](https://img.shields.io/badge/Aiogram-v2-2ca5e0?logo=telegram&logoColor=white)

### Infrastructure
![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?logo=docker&logoColor=white)
![Traefik](https://img.shields.io/badge/Traefik-TLS-FF4500?logo=traefikproxy&logoColor=white)

---

## Services

| Service | Domain | Description |
|---|---|---|
| `tarot-api` | `apps.baldcat.dev` | FastAPI backend — cards, users, Stripe, email |
| `tarot-bot` | `bot.baldcat.dev` | Telegram bot (webhook) |
| `tellguru-nginx` | `tell.guru` | Vue 3 SPA static files |
| `traefik` | — | Reverse proxy, TLS, routing |

---

## Highlights

- **Idempotent card draws** — MongoDB atomic `$setOnInsert` + in-memory lock prevents duplicate readings on double-tap
- **Telegram Mini App** — bot opens full card meaning pages as inline WebApp
- **Calendar-based daily card** — resets at midnight, not 24h from last use
- **Language-keyed cache** — card meanings cached per language in Pinia + localStorage
- **Honeypot spam protection** — contact form silently drops bot submissions

---

## Related

- 🌐 [tell.guru](https://tell.guru) — web app
- 🤖 [@Tarotelling_bot](https://t.me/Tarotelling_bot) — Telegram bot
