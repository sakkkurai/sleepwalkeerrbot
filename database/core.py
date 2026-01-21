from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import config
from database.models import Base

engine = create_async_engine(
    url=config.DB_URL,
    echo=True 
)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        
        #await conn.run_sync(Base.metadata.drop_all)

        await conn.run_sync(Base.metadata.create_all)
