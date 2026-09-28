import asyncio
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.counterparty import (
    CounterpartyCheckRequest,
    CounterpartyCheckResponse,
)
from app.services.bot import run_bot_polling
from app.services.provider import get_counterparty_data

load_dotenv()
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    polling_task = None
    if BOT_TOKEN:
        polling_task = asyncio.create_task(run_bot_polling(BOT_TOKEN))
    yield
    if polling_task:
        polling_task.cancel()


app = FastAPI(
    title="MAX Business Counterparty Scoring API",
    description="API для скоринга и оценки рисков контрагентов в мессенджере МАХ",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://max-bot-hackathon.vercel.app",
        "http://localhost:5173",
        "http://localhost:8080",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "counterparty-scoring"}


@app.post(
    "/api/v1/counterparty/check",
    response_model=CounterpartyCheckResponse,
    tags=["Counterparty"],
    summary="Проверка контрагента по ИНН или ОГРН",
)
def check_counterparty(req: CounterpartyCheckRequest):
    inn = req.query.strip()
    if not (len(inn) in (10, 12, 13, 15) and inn.isdigit()):
        raise HTTPException(
            status_code=400,
            detail="Некорректный формат ИНН/ОГРН. Ожидается от 10 до 15 цифр.",
        )
    return get_counterparty_data(inn)