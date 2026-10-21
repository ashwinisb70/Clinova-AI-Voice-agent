import asyncio
from database import users_collection

async def main():
    if users_collection is None:
        print("Database is not configured.")
        return

    admins = await users_collection.find(
        {"role": "admin"},
        {"_id": 0, "username": 1, "role": 1, "hospital_id": 1}
    ).to_list(50)

    if not admins:
        print("No admin accounts found in this database.")
        return

    for user in admins:
        print(user)

if __name__ == "__main__":
    asyncio.run(main())
