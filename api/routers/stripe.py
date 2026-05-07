import os

import stripe
from fastapi import APIRouter, HTTPException, Request

from core.db_class import MongoDBHandler
from core.user_class import User

router = APIRouter(prefix="/stripe", tags=["stripe"])


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event.type in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "customer.subscription.paused",
        "customer.subscription.resumed",
    ):
        customer_email = event.data.object.get("customer_email") or \
                         _get_customer_email(event.data.object.get("customer"))
        if customer_email:
            _invalidate_subscription_cache(customer_email)

    return {"success": True}


def _get_customer_email(customer_id: str) -> str | None:
    if not customer_id:
        return None
    try:
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        customer = stripe.Customer.retrieve(customer_id)
        return customer.get("email")
    except Exception:
        return None


def _invalidate_subscription_cache(email: str) -> None:
    db = MongoDBHandler()
    db.update(
        User.TABLE,
        {"subscription_cache": None},
        User.FIELD_WEB_LOGIN,
        email,
    )
