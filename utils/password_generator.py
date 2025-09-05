import uuid


async def generate_unique_number():
    unique_id = str(uuid.uuid4().int)[:6]
    return int(unique_id)
