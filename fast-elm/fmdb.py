import os
import logging

from databases import DatabaseURL
from motor.motor_asyncio import AsyncIOMotorClient

# -----------------------------------------------------------------------------
# mongodb config
MAX_CONN = int(os.getenv("MAX_CONN", 10))
MIN_CONN = int(os.getenv("MIN_CONN", 10))
MONGODB_URL = os.getenv("MONGODB_URL", "")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "mongo")
MONGO_PASS = os.getenv("MONGO_PASS", "12345")
MONGO_DB = os.getenv("MONGO_DB", "test")


if not MONGODB_URL:
    # MONGO_DB = os.getenv("MONGO_DB", "fastlearn")

    MONGODB_URL = DatabaseURL(
        f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"
    )
else:
    MONGODB_URL = DatabaseURL(MONGODB_URL)
# =============================================================================


# -----------------------------------------------------------------------------
# db object
class DataBase:
    client: AsyncIOMotorClient = None


db = DataBase()


async def get_database() -> AsyncIOMotorClient:
    return db.client
# =============================================================================


# -----------------------------------------------------------------------------
# connect & close
async def connect_to_mongo():
    logging.info("连接数据库中...")
    logging.info(str(MONGODB_URL))
    db.client = AsyncIOMotorClient(
        str(MONGODB_URL),
        maxPoolSize=MAX_CONN,
        minPoolSize=MIN_CONN
    )
    logging.info("连接数据库成功！")


async def close_mongo_connection():
    logging.info("关闭数据库连接...")
    db.client.close()
    logging.info("数据库连接关闭！")
# =============================================================================


# -----------------------------------------------------------------------------
# db collections
db_name = MONGO_DB
articles_collection_name = "articles"
favorites_collection_name = "favorites"
tags_collection_name = "tags"
users_collection_name = "users"
commentaries_collection_name = "commentaries"
followers_collection_name = "followers"

# elm collections
cities_collection_name = "cities"
entries_collection_name = "entries"

users_collection_name = "users"
userinfos_collection_name = "userinfos"
categories_collection_name = "categories"
restaurants_collection_name = "shops"
deliveries_collection_name = "deliveries"
activities_collection_name = "activities"
menus_collection_name = "menus"
ratings_collection_name = "ratings"
# =============================================================================
