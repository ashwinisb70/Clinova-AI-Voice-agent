import asyncio
from main import users_collection
from auth import verify_password

async def check():
    u = await users_collection.find_one(
        {"username": "clinovatest01"}
    )

    print("USER FOUND:", bool(u))

    if u:
        password = input("Enter the password you used during registration: ")
        print("PASSWORD MATCH:", verify_password(password, u["password_hash"]))

asyncio.run(check())