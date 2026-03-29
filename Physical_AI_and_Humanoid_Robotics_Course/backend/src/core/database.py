from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql+asyncpg://user:password@host:port/database" # This should come from config.py

database = Database(DATABASE_URL)
metadata = MetaData()
Base = declarative_base()
engine = create_engine(DATABASE_URL)

async def connect_db():
    await database.connect()

async def disconnect_db():
    await database.disconnect()