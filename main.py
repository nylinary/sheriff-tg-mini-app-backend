import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.auth import auth_router
from routers.users import users_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("miniapp")

app = FastAPI(title="MiniApp backend logger")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sherifex.com",
        "https://web.telegram.org",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(auth_router)
app.include_router(users_router)