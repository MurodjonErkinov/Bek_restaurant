import re


def normalize_uzbek_phone(value):
    if value in (None, ''):
        return None
    digits = re.sub(r'\D', '', str(value))
    if len(digits) == 12 and digits.startswith('998'):
        digits = digits[3:]
    if len(digits) != 9:
        raise ValueError('Telefon raqam 9 xonali yoki +998 bilan 12 xonali bo‘lishi kerak.')
    return digits
