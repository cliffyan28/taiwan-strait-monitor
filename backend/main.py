from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from config import DB_PATH
from routers import threat, mnd, aircraft, news, status

app = FastAPI(title="Taiwan Strait Monitor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(threat.router)
app.include_router(mnd.router)
app.include_router(aircraft.router)
app.include_router(news.router)
app.include_router(status.router)


@app.on_event("startup")
def startup():
    init_db(str(DB_PATH))
