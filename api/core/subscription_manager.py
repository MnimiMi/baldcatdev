import os
from datetime import datetime, timedelta

import stripe


class SubscriptionManager:
    def __init__(self, tg_id: int, email: str = None):
        self._tg_id = tg_id
        self._email = email
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')

    def is_subscribed(self) -> bool:
        if self._email and self._check_by_email():
            return True
        return self._check_by_tg_id()

    def _check_by_email(self) -> bool:
        try:
            clients = stripe.Customer.search(query=f"email:'{self._email}'")
            if not clients['data']:
                return False
            customer_id = clients['data'][0]['id']
            subs = stripe.Subscription.list(customer=customer_id, status='active', limit=5)
            if subs['data']:
                return True
            subs_trial = stripe.Subscription.list(customer=customer_id, status='trialing', limit=5)
            return bool(subs_trial['data'])
        except stripe.error.StripeError:
            return False

    def _check_by_tg_id(self) -> bool:
        if not self._tg_id:
            return False
        try:
            since = int((datetime.now() - timedelta(days=31)).timestamp())
            query = f"metadata['tguser']:'{self._tg_id}' and status:'succeeded' and created>{since}"
            charge = stripe.Charge.search(query=query)
            return len(charge['data']) > 0
        except stripe.error.StripeError:
            return False
