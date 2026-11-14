# language: Python, file: core/downloader.py
import httpx, re
from typing import AsyncIterator

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"

async def stream(url: str, chunk: int = 65536) -> AsyncIterator[bytes]:
    async with httpx.AsyncClient(timeout=120, follow_redirects=True, headers={"User-Agent": UA}) as c:
        async with c.stream("GET", url) as r:
            r.raise_for_status()
            async for part in r.aiter_bytes(chunk):
                yield part

def safe_name(title: str) -> str:
    return (re.sub(r"[^\w\-_. ]", "_", title or "tiktok")[:80]).strip() or "tiktok"
