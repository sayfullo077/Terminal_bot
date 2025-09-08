import uuid
import random


async def generate_unique_number():
    # UUID dan 6 xonali raqam yaratish, 0 bilan boshlanmasligi uchun
    unique_id = str(uuid.uuid4().int)
    # Agar raqam 0 bilan boshlansa, random raqam qo'shamiz
    if unique_id.startswith('0'):
        unique_id = str(random.randint(100000, 999999))
    else:
        unique_id = unique_id[:6]
    return int(unique_id)
