import asyncio
import logging
import httpx
from app.services.provider import get_counterparty_data

logger = logging.getLogger("max_bot")
logging.basicConfig(level=logging.INFO)

BASE_URL = "https://platform-api2.max.ru"


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
        await client.post(
            f"{BASE_URL}/messages",
            headers=headers,
            params={"chat_id": chat_id},
            json={"text": text},
        )
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")


async def run_bot_polling(token: str):
    headers = {"Authorization": token.strip(), "Accept": "application/json"}
    marker = None
    logger.info(">>> Фоновый воркер бота MAX успешно стартовал! <<<")

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

                        if text.lower() in (
                            "/start",
                            "старт",
                            "привет",
                            "/help",
                        ):
                            welcome = (
                                "👋 Привет! Я сервис проверки благонадежности контрагентов.\n\n"
                                "Отправьте ИНН компании (10 или 12 цифр), чтобы получить скоринг рисков."
                            )
                            await send_message(client, token, chat_id, welcome)
                        elif text.isdigit() and len(text) in (10, 12, 13, 15):
                            reply = format_bot_reply(text)
                            await send_message(client, token, chat_id, reply)
                        else:
                            await send_message(
                                client,
                                token,
                                chat_id,
                                "Пожалуйста, отправьте корректный ИНН (10 или 12 цифр).",
                            )

            except httpx.ReadTimeout:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Сбой polling: {e}")
                await asyncio.sleep(2)