import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import fastapi

cxn = AsyncIOMotorClient("mongodb://mongo:12345@localhost:27017/test")

app = fastapi.FastAPI()

db = cxn["test"]

async def main():
    data = []
    cities = db["shops"].find()
    async for c in cities:
        data.append(c)

    print(data)

loop = asyncio.get_event_loop()

loop.run_until_complete(main())


