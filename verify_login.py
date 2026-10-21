import asyncio
from main import users_collection
from auth import verify_password

async def check():
    user = await users_collection.find_one({"username": "Ashwini"})
    print("Account found:", bool(user))

    if user:
        password = input("Enter the password used during registration: ")
        print("Password matches:", verify_password(password, user["password_hash"]))

asyncio.run(check())
