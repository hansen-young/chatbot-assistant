from abc import ABC, abstractmethod
from datetime import datetime
from typing import Type

import pymongo
from pydantic import BaseModel, Field, MongoDsn
from pymongo import AsyncMongoClient

from core.types.message import Message, Messages
from core.types.message_content import ContentPart, ContentPartText


class Session(BaseModel):
    id: str
    messages: Messages
    created_at: datetime = Field(default_factory=datetime.now)

    def add_message(
        self,
        cls: Type[Message],
        *,
        text: str | None = None,
        content: list[ContentPart] | None = None,
        **kwargs,
    ):
        if text is not None:
            self.messages.append(cls(content=[ContentPartText(text=text)], **kwargs))

        elif content is not None:
            self.messages.append(cls(content=content, **kwargs))

        else:
            raise ValueError("add_message requires one of 'text' or 'content'.")


class SessionService(ABC):
    @abstractmethod
    async def create(self, session_id: str) -> Session: ...

    @abstractmethod
    async def load(self, session_id: str) -> Session | None: ...

    @abstractmethod
    async def save(self, session: Session): ...

    @abstractmethod
    async def list(self, n: int, page: int) -> list[str]: ...

    @abstractmethod
    async def delete(self, session_id: str): ...


class InMemorySessionService(SessionService):
    def __init__(self):
        self.sessions: dict[str, Session] = {}

    async def create(self, session_id: str) -> Session:
        if session_id in self.sessions:
            raise ValueError(f"Session `{session_id}` already exists")

        session = Session(id=session_id, messages=[])
        await self.save(session)

        return session

    async def load(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    async def save(self, session: Session):
        self.sessions[session.id] = session

    async def list(self, n: int = 10, page: int = 1) -> list[str]:
        if n <= 0 or page <= 0:
            raise ValueError("n and page must be a positive integer.")

        sidx = (page - 1) * n
        return list(self.sessions.keys())[sidx : sidx + n]

    async def delete(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]


class MongoConfig(BaseModel):
    uri: MongoDsn
    collection: str = "sessions"


class MongoSessionService(SessionService):
    def __init__(self, client: AsyncMongoClient, collection: str):
        self.client = client
        self.collection = collection

    @classmethod
    async def from_config(cls, config: MongoConfig):
        client = AsyncMongoClient(config.uri.unicode_string())
        return cls(client, config.collection)

    async def get_collection(self):
        database = self.client.get_default_database()
        collection = database.get_collection(self.collection)
        await collection.create_index([("id", pymongo.ASCENDING)], unique=True)
        await collection.create_index([("created_at", pymongo.DESCENDING)])
        return collection

    async def is_session_exists(self, session_id: str):
        collection = await self.get_collection()
        count = await collection.count_documents({"id": session_id})
        return count == 1

    async def create(self, session_id: str) -> Session:
        if await self.is_session_exists(session_id):
            raise ValueError(f"Session `{session_id}` already exists")

        session = Session(id=session_id, messages=[])
        await self.save(session)

        return session

    async def load(self, session_id: str) -> Session | None:
        collection = await self.get_collection()
        doc = await collection.find_one({"id": session_id}, {"_id": 0})

        if doc:
            return Session(**doc)

    async def save(self, session: Session):
        collection = await self.get_collection()
        await collection.update_one(
            filter={"id": session.id},
            update={"$set": session.model_dump()},
            upsert=True,
        )

    async def list(self, n: int = 10, page: int = 1) -> list[str]:
        if n <= 0 or page <= 0:
            raise ValueError("n and page must be a positive integer.")

        collection = await self.get_collection()
        cursor = (
            collection.find({}, {"_id": 0, "id": 1})
            .sort("created_at", pymongo.DESCENDING)
            .skip((page - 1) * n)
            .limit(n)
        )
        return [doc["id"] async for doc in cursor]

    async def delete(self, session_id: str):
        collection = await self.get_collection()
        await collection.delete_one({"id": session_id})
