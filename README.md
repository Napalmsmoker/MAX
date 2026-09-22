# MAX Business Counterparty Scoring

Сервис автоматической проверки и оценки рисков контрагентов для мессенджера **МАХ**. 
Решение разработано в рамках хакатона по созданию ботов и мини-приложений.

## Архитектура решения
- **Backend:** FastAPI (асинхронный REST API + Swagger UI)
- **Bot Worker:** Фоновый Long Polling воркер для Bot API MAX (`/updates` и `/messages`)
- **Контейнеризация:** Docker & Docker Compose
- **Спецификация:** OpenAPI 3.0 + DATA-API.yaml
