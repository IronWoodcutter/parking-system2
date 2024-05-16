import redis.asyncio as redis

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable

from ipaddress import ip_address

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_limiter import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.conf import messages
from src.database.db import get_db
from src.routes import auth, users, admin, plates
from src.conf.config import settings
from src.pages.router import router as router_pages
from src.services.tg_bot import bot, dp, types


#######
@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(url=settings.WEBHOOK_URL)
    r = await redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                password=settings.REDIS_PASSWORD,
            )
    await FastAPILimiter.init(r)
    yield
    await FastAPILimiter.close()
    yield
    await bot.delete_webhook()

app = FastAPI(lifespan=lifespan)

WEBHOOK_PATH = f"/bot/{settings.TELEGRAM_TOKEN}"
WEBHOOK_URL = f"{settings.WEBHOOK_URL}{WEBHOOK_PATH}"
#######


banned_ips = [ip_address("192.168.255.1"), ip_address("192.168.255.1")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
BASE_DIR = Path(__file__).parent
directory = BASE_DIR / "src" / "static"
app.mount("/src/static", StaticFiles(directory=directory), name="static")

app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')
app.include_router(admin.router, prefix='/api')
app.include_router(plates.router, prefix='/api')
app.include_router(router_pages)

templates = Jinja2Templates(directory=BASE_DIR / "src" / "templates")


@app.middleware("http")
async def ban_ips(request: Request, call_next: Callable):
    """
    The ban_ips function is a middleware function that checks if the client's IP address
    is in the banned_ips list. If it is, then we return a JSON response with status code 403
    and an error message. Otherwise, we call the next middleware function and return its response.

    :param request: Request: Get the client's ip address
    :param call_next: Callable: Pass the next function in the middleware chain to ban_ips
    :return: A jsonresponse with a status code of 403 and a message
    :doc-author: Trelent
    """
    if settings.APP_ENV == "production":
        ip = ip_address(request.client.host)
        if ip in banned_ips:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, content={"detail": messages.MAIN_IP_BANNED}
            )
    response = await call_next(request)
    return response


@app.get("/", response_class=HTMLResponse, description="Main Page")
async def read_root(request: Request):
    """
    The read_root function is a coroutine that returns an HTML response.
    The function uses the templates module to render the index.html template,
    which is located in the templates directory of our project.

    :param request: Request: Pass the request object to the template
    :return: A templateresponse object
    :doc-author: Trelent
    """
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "PhotoShare App"}
    )


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    The healthchecker function is a simple function that checks the health of the database.
    It does this by executing a SQL query to check if it can connect to the database and retrieve data.
    If it cannot, then an HTTPException is raised with status code 500 (Internal Server Error) and detail message &quot;Error connection to database&quot;.
    Otherwise, if everything works as expected, then we return {&quot;message&quot;: &quot;Welcome to FastAPI!&quot;}.

    :param db: AsyncSession: Get the database session
    :return: A dictionary with a message
    :doc-author: Trelent
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail=messages.MAIN_DB_NOT_CONFIGURED
            )
        return {"message": messages.WELCOME_MESSAGE}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=messages.MAIN_DB_ERROR_CONNECTION)


@app.post("/")
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)
