import asyncio
import getpass
from main import users_collection
from auth import hash_password

async def reset_password():
    username = "clinovatest01"

    if users_collection is None:
        print("ERROR: Database is not configured.")
        return

    user = await users_collection.find_one({"username": username})
    if not user:
        print("ERROR: Admin account not found.")
        return

    password = getpass.getpass("Enter a NEW admin password: ")
    confirm = getpass.getpass("Confirm the new password: ")

    if len(password) < 12:
        print("ERROR: Use at least 12 characters.")
        return

    if password != confirm:
        print("ERROR: Passwords do not match.")
        return

    result = await users_collection.update_one(
        {"username": username},
        {"$set": {"password_hash": hash_password(password)}}
    )

    if result.modified_count == 1:
        print("SUCCESS: Admin password reset.")
    else:
        print("ERROR: Password was not changed.")

    password = None
    confirm = None

asyncio.run(reset_password())
