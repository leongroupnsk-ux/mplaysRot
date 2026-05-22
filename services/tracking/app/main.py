from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.tracker import record_click, resolve_destination

app = FastAPI(title="Attribly Tracking", docs_url=None, redoc_url=None)
Instrumentator().instrument(app).expose(app)


@app.get("/t/{trax_id}")
async def track_click(trax_id: str, request: Request):
    """Точка входа трекинг-ссылки. Фиксирует клик, редиректит на карточку товара."""
    destination = await resolve_destination(trax_id)
    if not destination:
        return Response(status_code=404)

    await record_click(trax_id=trax_id, request=request)
    return RedirectResponse(url=destination, status_code=302)


@app.get("/pixel/{trax_id}.gif")
async def tracking_pixel(trax_id: str, request: Request):
    """1x1 GIF пиксель для server-side трекинга на лендингах."""
    await record_click(trax_id=trax_id, request=request)
    gif_bytes = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    return Response(content=gif_bytes, media_type="image/gif")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "tracking"}
