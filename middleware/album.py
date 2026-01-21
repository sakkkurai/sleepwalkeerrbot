import asyncio
from typing import Any, Dict, Union
from aiogram import BaseMiddleware
from aiogram.types import Message

class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: float = 0.5):
        self.latency = latency
        self.album_data = {}

    async def __call__(self, handler, event: Message, data: Dict[str, Any]) -> Any:
        if not event.media_group_id:
            return await handler(event, data)

        group_id = event.media_group_id

        if group_id not in self.album_data:
            self.album_data[group_id] = []
            self.album_data[group_id].append(event)
            await asyncio.sleep(self.latency)
            album = self.album_data[group_id]
            album.sort(key=lambda x: x.message_id)
            data["album"] = album
            del self.album_data[group_id]
            return await handler(event, data)
        
        else:
            self.album_data[group_id].append(event)
            return