# language: Python, file: core/extractor.py
import asyncio, re, httpx, yt_dlp
from typing import Optional

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"

def _normalize(d: dict, source: str) -> dict:
    return {
        "source": source,
        "title": (d.get("title") or "TikTok video")[:200],
        "author": (d.get("author") or "unknown")[:80],
        "thumbnail": d.get("thumbnail"),
        "duration": d.get("duration"),
        "url": d.get("url"),
        "ext": d.get("ext") or "mp4",
        "watermark_free": d.get("watermark_free", True),
    }

async def src_ytdlp(url: str) -> dict:
    def _run():
        opts = {"quiet": True, "no_warnings": True, "skip_download": True, "format": "best"}
        with yt_dlp.YoutubeDL(opts) as y:
            i = y.extract_info(url, download=False)
        return {
            "title": i.get("title"),
            "author": i.get("uploader") or i.get("creator"),
            "thumbnail": i.get("thumbnail"),
            "duration": i.get("duration"),
            "url": i.get("url"),
            "ext": i.get("ext", "mp4"),
        }
    return _normalize(await asyncio.to_thread(_run), "yt-dlp")

async def src_tikwm(url: str) -> dict:
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}) as c:
        r = await c.get("https://www.tikwm.com/api/", params={"url": url, "hd": 1})
        j = r.json()
    if j.get("code") != 0 or not j.get("data"):
        raise RuntimeError(j.get("msg", "tikwm no data"))
    d = j["data"]
    return _normalize({
        "title": d.get("title"),
        "author": (d.get("author") or {}).get("unique_id"),
        "thumbnail": d.get("cover"),
        "duration": d.get("duration"),
        "url": d.get("hdplay") or d.get("play"),
    }, "tikwm")

async def src_douyin(url: str) -> dict:
    # tikwm's douyin mirror handles some blocks tiktok path fails on
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}) as c:
        r = await c.get("https://www.tikwm.com/api/", params={"url": url, "hd": 1, "region": "cn"})
        j = r.json()
    if j.get("code") != 0 or not j.get("data"):
        raise RuntimeError("douyin mirror no data")
    d = j["data"]
    return _normalize({
        "title": d.get("title"), "author": (d.get("author") or {}).get("unique_id"),
        "thumbnail": d.get("cover"), "duration": d.get("duration"),
        "url": d.get("hdplay") or d.get("play"),
    }, "douyin-mirror")

async def src_snaptik(url: str) -> dict:
    # snaptik parse — HTML pattern, brittle but adds a fallback
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}, follow_redirects=True) as c:
        r = await c.post("https://snaptik.app/abc2.php",
                         data={"url": url}, headers={"Referer": "https://snaptik.app/"})
        html = r.text
    m = re.search(r'href="(https://[^"]+\.mp4[^"]*)"', html)
    if not m:
        raise RuntimeError("snaptik no mp4")
    return _normalize({"url": m.group(1), "title": "TikTok via snaptik", "author": "unknown"}, "snaptik")

async def src_musicaldown(url: str) -> dict:
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}) as c:
        r = await c.post("https://musicaldown.com/download",
                         data={"id": url}, headers={"Referer": "https://musicaldown.com/"})
        html = r.text
    m = re.search(r'href="(https://[^"]+\.mp4[^"]*)"', html)
    if not m:
        raise RuntimeError("musicaldown no mp4")
    return _normalize({"url": m.group(1), "title": "TikTok via musicaldown", "author": "unknown"}, "musicaldown")

SOURCES = [
    ("yt-dlp", src_ytdlp),
    ("tikwm", src_tikwm),
    ("douyin-mirror", src_douyin),
    ("snaptik", src_snaptik),
    ("musicaldown", src_musicaldown),
]

async def resolve(url: str) -> dict:
    errors = []
    for name, fn in SOURCES:
        try:
            data = await fn(url)
            if data.get("url"):
                data["attempted"] = [e[0] for e in errors]
                return {"ok": True, "data": data}
            errors.append((name, "no url"))
        except Exception as e:
            errors.append((name, str(e)[:120]))
    return {"ok": False, "errors": errors}
