import json
import logging
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)


def send_checkout_notification(order):
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_IDS:
        return {
            'sent': 0,
            'failed': 0,
            'errors': ['Telegram token yoki chat ID sozlanmagan.'],
        }

    table = f'Stol {order.table.number}' if order.table_id else 'Stolsiz'
    waiter = (
        order.waiter.get_full_name() or order.waiter.phone
        if order.waiter_id
        else 'Biriktirilmagan'
    )
    text = (
        f'✅ Buyurtma #{order.id} yopildi\n'
        f'{table}\n'
        f'Afitsant: {waiter}\n'
        f'Jami: {order.total_price}\n'
        f'Naqd: {order.paid_amount}\n'
        f'Qarz: {order.debt_amount}'
    )
    url = f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage'
    sent = 0
    errors = []

    for chat_id in settings.TELEGRAM_CHAT_IDS:
        try:
            request = Request(
                url,
                data=urlencode({'chat_id': chat_id, 'text': text}).encode(),
                method='POST',
            )
            with urlopen(request, timeout=10) as response:
                telegram_response = json.load(response)

            if not telegram_response.get('ok'):
                raise RuntimeError(
                    telegram_response.get('description', 'Telegram API xatosi.')
                )
            sent += 1
        except HTTPError as exc:
            try:
                error = json.load(exc).get('description', str(exc))
            except Exception:
                error = str(exc) or type(exc).__name__
            errors.append(error)
            logger.exception(
                'Telegram checkout xabari chat_id=%s uchun yuborilmadi: %s',
                chat_id,
                error,
            )
        except Exception as exc:
            error = str(exc) or type(exc).__name__
            errors.append(error)
            logger.exception(
                'Telegram checkout xabari chat_id=%s uchun yuborilmadi: %s',
                chat_id,
                error,
            )

    return {'sent': sent, 'failed': len(errors), 'errors': errors}
