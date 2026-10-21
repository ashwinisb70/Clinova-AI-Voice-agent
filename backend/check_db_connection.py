import asyncio
from database import client, db

async def main():
    try:
        result = await client.admin.command("ping")
        print("Atlas connection: SUCCESS")
        print("Database selected:", db.name)
    except Exception as exc:
        print("Atlas connection: FAILED")
        print("Error type:", type(exc).__name__)
        print("Check Atlas network access and credentials; do not share your URI.")

asyncio.run(main())
