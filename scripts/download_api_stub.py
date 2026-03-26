from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/hybrid/video_data")
def video_data(payload: dict):
    url = payload.get("url") or ""
    data = {
        "title": "stub-title",
        "platform": "youtube" if "youtu" in url else "unknown",
        "duration": 120,
        "video_id": "stub123",
        "video_urls": [
            {"url": "http://example.com/video.mp4", "quality": "720p", "ext": "mp4", "resolution": "1280x720"}
        ],
        "links": [
            {"url": "http://example.com/video.mp4", "quality": "720p", "format": "mp4", "size": 1024}
        ],
    }
    return {"code": 200, "message": "ok", "data": data}

