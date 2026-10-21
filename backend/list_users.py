import asyncio
from main import users_collection

async def check():
    if users_collection is None:
        print("Users collection is not configured.")
        return

    count = 0
    async for user in users_collection.find(
        {}, {"_id": 0, "username": 1, "role": 1}
    ):
        print("Username:", user.get("username", "(missing)"),
              "| Role:", user.get("role", "(not set)"))
        count += 1

    print("Total accounts:", count)

asyncio.run(check())
