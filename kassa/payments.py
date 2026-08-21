from decimal import Decimal, InvalidOperation


PAYMENT_METHODS = ('cash', 'card', 'credit')


def _decimal(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f'{field} noto‘g‘ri.') from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError(f'{field} manfiy bo‘la olmaydi.')
    return amount.quantize(Decimal('0.01'))


def parse_payment(data, total_price):
    total_price = total_price.quantize(Decimal('0.01'))
    split_fields = {'cash_amount', 'card_amount', 'credit_amount', 'partner_amount'}

    if split_fields.intersection(data.keys()):
        cash_amount = _decimal(data.get('cash_amount', '0'), 'cash_amount')
        card_amount = _decimal(data.get('card_amount', '0'), 'card_amount')
        credit_amount = _decimal(data.get('credit_amount', '0'), 'credit_amount')
        partner_amount = _decimal(data.get('partner_amount', '0'), 'partner_amount')
        if cash_amount + card_amount + credit_amount + partner_amount != total_price:
            raise ValueError(
                'cash_amount + card_amount + credit_amount + partner_amount '
                'buyurtma jami summasiga teng bo‘lishi kerak.'
            )
    else:
        payment_type = data.get('payment_type', 'cash')
        if payment_type not in PAYMENT_METHODS:
            raise ValueError('payment_type noto‘g‘ri.')
        paid_amount = _decimal(data.get('paid_amount', '0'), 'paid_amount')
        if paid_amount > total_price:
            raise ValueError('paid_amount buyurtma summasidan oshmasligi kerak.')
        if payment_type in {'cash', 'card'} and paid_amount != total_price:
            raise ValueError('cash yoki card to‘lovda to‘liq summa yuborilishi kerak.')

        cash_amount = paid_amount if payment_type in {'cash', 'credit'} else Decimal('0.00')
        card_amount = paid_amount if payment_type == 'card' else Decimal('0.00')
        credit_amount = total_price - paid_amount if payment_type == 'credit' else Decimal('0.00')
        partner_amount = Decimal('0.00')

    used_methods = sum(
        amount > 0 for amount in (cash_amount, card_amount, credit_amount, partner_amount)
    )
    if used_methods > 1:
        payment_type = 'mixed'
    elif card_amount > 0:
        payment_type = 'card'
    elif credit_amount > 0:
        payment_type = 'credit'
    elif partner_amount > 0:
        payment_type = 'partner_offset'
    else:
        payment_type = 'cash'

    paid_amount = cash_amount + card_amount
    return {
        'payment_type': payment_type,
        'paid_amount': paid_amount,
        'debt_amount': credit_amount,
        'is_paid': credit_amount == 0,
        'cash_amount': cash_amount,
        'card_amount': card_amount,
        'credit_amount': credit_amount,
        'partner_amount': partner_amount,
    }
