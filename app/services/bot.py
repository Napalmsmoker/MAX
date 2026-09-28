import asyncio
import logging
import httpx
from app.services.provider import get_counterparty_data

logger = logging.getLogger("max_bot")
logging.basicConfig(level=logging.INFO)

BASE_URL = "https://platform-api2.max.ru"
WEBAPP_URL = "https://max-bot-hackathon.vercel.app"


def format_bot_reply(inn: str) -> str:
    data = get_counterparty_data(inn)
    comp = data.company

    status_icon = (
        "🟢"
        if data.risk_status == "GREEN"
        else ("🟡" if data.risk_status == "YELLOW" else "🔴")
    )

    lines = [
        f"{status_icon} Результат проверки контрагента:",
        f"Организация: {comp.name}",
        f"ИНН: {comp.inn} | ОГРН: {comp.ogrn}",
        f"Статус: {comp.status}",
        f"Индекс надежности: {data.risk_score}/100 ({data.risk_status})",
        "",
        f"Вердикт: {data.summary_verdict}",
        "",
        "Ключевые факторы:",
    ]

    for factor in data.risk_factors:
        f_icon = (
            "✅"
            if factor.level == "success"
            else ("⚠️" if factor.level == "warning" else "⛔")
        )
        lines.append(f"{f_icon} {factor.title}: {factor.description}")

    lines.append("")
    lines.append("Рекомендации:")
    for rec in data.recommendations:
        lines.append(f"• {rec}")

    return "\n".join(lines)


async def send_message(
    client: httpx.AsyncClient, token: str, chat_id: int, text: str
):
    headers = {"Authorization": token, "Accept": "application/json"}
    try:
        resp = await client.post(
            f"{BASE_URL}/messages",
            headers=headers,
            params={"chat_id": chat_id},
            json={"text": text},
        )
        if resp.status_code not in (200, 201):
            logger.error(
                f"Ошибка отправки сообщения: {resp.status_code} {resp.text}"
            )
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")


async def send_message_with_webapp_button(
    client: httpx.AsyncClient, token: str, chat_id: int, text: str
):
    """
    Отправляет сообщение с кнопкой «Открыть приложение».
    Пробует разные форматы кнопки, чтобы попасть в актуальный API MAX.
    """
    headers = {
        "Authorization": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payloads = [
        # Вариант 1: attachments → inline_keyboard с типом link
        {
            "text": text,
            "attachments": [
                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": [
                            [
                                {
                                    "type": "link",
                                    "text": "🔍 Открыть приложение",
                                    "url": WEBAPP_URL,
                                }
                            ]
                        ]
                    },
                }
            ],
        },
        # Вариант 2: type web_app с web_app полем
        {
            "text": text,
            "attachments": [
                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": [
                            [
                                {
                                    "type": "web_app",
                                    "text": "🔍 Открыть приложение",
                                    "web_app": WEBAPP_URL,
                                }
                            ]
                        ]
                    },
                }
            ],
        },
        # Вариант 3: кнопка в корне сообщения
        {
            "text": text,
            "keyboard": [
                [
                    {
                        "type": "link",
                        "text": "🔍 Открыть приложение",
                        "url": WEBAPP_URL,
                    }
                ]
            ],
        },
    ]

    for i, payload in enumerate(payloads, 1):
        try:
            resp = await client.post(
                f"{BASE_URL}/messages",
                headers=headers,
                params={"chat_id": chat_id},
                json=payload,
            )
            if resp.status_code in (200, 201):
                logger.info(f"✅ Сообщение с кнопкой отправлено (вариант {i})")
                return True
            else:
                logger.warning(
                    f"Вариант {i} не сработал: {resp.status_code} {resp.text[:200]}"
                )
        except Exception as e:
            logger.error(f"Вариант {i} упал: {e}")

    # Фолбэк — просто текст
    logger.warning("Все форматы кнопок не сработали, отправляю текст с URL")
    await send_message(
        client,
        token,
        chat_id,
        f"{text}\n\nОткрыть приложение: {WEBAPP_URL}",
    )
    return False


async def run_bot_polling(token: str):
    headers = {"Authorization": token.strip(), "Accept": "application/json"}
    marker = None
    logger.info(">>> Фоновый воркер бота MAX успешно стартовал! <<<")
    logger.info(f">>> Мини-приложение: {WEBAPP_URL} <<<")

    async with httpx.AsyncClient(verify=False, timeout=35.0) as client:
        while True:
            params = {"timeout": 25}
            if marker:
                params["marker"] = marker

            try:
                resp = await client.get(
                    f"{BASE_URL}/updates", headers=headers, params=params
                )
                if resp.status_code == 200:
                    data = resp.json()
                    marker = data.get("marker", marker)
                    updates = data.get("updates", [])

                    for event in updates:
                        msg = event.get("message")
                        if not msg:
                            continue

                        chat_id = msg.get("recipient", {}).get("chat_id")
                        text = msg.get("body", {}).get("text", "").strip()

                        if not chat_id or not text:
                            continue

                        logger.info(f"📩 Сообщение от {chat_id}: {text[:50]}")

                        if text.lower() in (
                            "/start",
                            "старт",
                            "привет",
                            "/help",
                        ):
                            welcome = (
                                "👋 Привет! Я сервис проверки благонадёжности контрагентов.\n\n"
                                "📱 Нажми кнопку ниже, чтобы открыть приложение для удобного поиска.\n\n"
                                "Или отправь ИНН компании (10 или 12 цифр) прямо здесь, чтобы получить скоринг рисков."
                            )
                            await send_message_with_webapp_button(
                                client, token, chat_id, welcome
                            )
                        elif text.isdigit() and len(text) in (10, 12, 13, 15):
                            reply = format_bot_reply(text)
                            await send_message(client, token, chat_id, reply)
                        else:
                            await send_message(
                                client,
                                token,
                                chat_id,
                                "Пожалуйста, отправьте корректный ИНН (10 или 12 цифр) или нажмите /start.",
                            )

            except httpx.ReadTimeout:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Сбой polling: {e}")
                await asyncio.sleep(2)