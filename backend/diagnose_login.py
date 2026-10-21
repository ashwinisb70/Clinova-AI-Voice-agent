import asyncio
import getpass
from database import db, users_collection
from auth import verify_password

async def check():
    print("Database:", db.name if db is not None else "NOT CONNECTED")
    username = "clinovatest01"
    user = await users_collection.find_one({"username": username}) if users_collection is not None else None
    print("Admin account found:", bool(user))

    if user:
        password = getpass.getpass("Enter the new password (hidden): ")
        print("Password matches this database:", verify_password(password, user["password_hash"]))

asyncio.run(check())
