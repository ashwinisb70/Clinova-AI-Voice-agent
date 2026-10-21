import asyncio
from main import users_collection
from auth import hash_password

async def reset():
    username = "clinovatest01"
    new_password = "Test@890"

    result = await users_collection.update_one(
        {"username": username},
        {"$set": {"password_hash": hash_password(new_password)}}
    )

    print("PASSWORD RESET:", result.modified_count == 1)

asyncio.run(reset())