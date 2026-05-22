"""
Auth Service - JWT token generation and validation
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Auth Service", version="1.0.0")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse({"status": "ok", "service": "auth"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
