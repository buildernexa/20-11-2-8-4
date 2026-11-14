# language: Python, file: app.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import re
from core import extractor, downloader, history

app = FastAPI(title="TikTok Studio")
app.mount("/static", StaticFiles(directory="static"), name="static")
tpl = Jinja2Templates(directory="templates")

def is_tt(u: str) -> bool:
    return bool(re.search(r"tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com", u or ""))

class Req(BaseModel):
    url: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return tpl.TemplateResponse("home.html", {"request": request, "active": "home"})

@app.get("/history", response_class=HTMLResponse)
async def hist(request: Request):
    rows = history.recent(100)
    return tpl.TemplateResponse("history.html", {"request": request, "active": "history", "rows": rows})

@app.get("/themes", response_class=HTMLResponse)
async def themes(request: Request):
    return tpl.TemplateResponse("themes.html", {"request": request, "active": "themes"})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return tpl.TemplateResponse("about.html", {"request": request, "active": "about"})

@app.post("/api/resolve")
async def resolve(req: Req):
    if not is_tt(req.url):
        raise HTTPException(400, "URL TikTok tidak valid")
    res = await extractor.resolve(req.url)
    if res.get("ok"):
        d = res["data"]
        history.log(req.url, d["title"], d["author"], d["source"], "ok")
    else:
        history.log(req.url, "-", "-", "-", "fail")
    return res

@app.post("/api/download")
async def download(req: Req):
    if not is_tt(req.url):
        raise HTTPException(400, "URL TikTok tidak valid")
    res = await extractor.resolve(req.url)
    if not res.get("ok"):
        raise HTTPException(502, f"Semua sumber gagal: {res.get('errors')}")
    d = res["data"]
    name = downloader.safe_name(d["title"]) + ".mp4"
    return StreamingResponse(
        downloader.stream(d["url"]),
        media_type="video/mp4",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )

@app.delete("/api/history")
async def clear_hist():
    history.clear()
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
