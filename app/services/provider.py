from app.models.counterparty import (
    CounterpartyCheckResponse,
    CounterpartyDetails,
)


MOCK_DATA = {

    "7707083893": {
        "company": {
            "inn": "7707083893",
            "ogrn": "1027700132195",
            "name": "ПАО СБЕРБАНК",
            "full_name": 'ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО "СБЕРБАНК РОССИИ"',
            "status": "Действующая",
            "registration_date": "1991-06-20",
            "ceo_name": "Греф Герман Оскарович",
            "legal_address": "г. Москва, ул. Вавилова, д. 19",
            "authorized_capital": 67760844000.0,
            "is_msp": False,
            "tax_system": "ОСНО",
        },
        "risk_score": 98,
        "risk_status": "GREEN",
        "summary_verdict": "Высокая степень надежности. Критических факторов риска не обнаружено.",
        "risk_factors": [
            {
                "level": "success",
                "title": "Возраст организации",
                "description": "Организация ведет деятельность более 30 лет.",
            },
            {
                "level": "success",
                "title": "Финансовая устойчивость",
                "description": "Крупный уставный капитал, отсутствие блокировок счетов ФНС.",
            },
        ],
        "recommendations": [
            "Стандартный порядок заключения договора.",
            "Специальных ограничений не требуется.",
        ],
    },

    "7701999999": {
        "company": {
            "inn": "7701999999",
            "ogrn": "1237700000001",
            "name": 'ООО "ВЕКТОР-М"',
            "full_name": 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ВЕКТОР-М"',
            "status": "В стадии ликвидации",
            "registration_date": "2024-01-15",
            "ceo_name": "Иванов И.И. (дисквалифицирован)",
            "legal_address": "г. Москва (адрес массовой регистрации)",
            "authorized_capital": 10000.0,
            "is_msp": True,
            "tax_system": "УСН",
        },
        "risk_score": 18,
        "risk_status": "RED",
        "summary_verdict": "Критический уровень риска! Высокая вероятность финансовых потерь и проблем с налоговой.",
        "risk_factors": [
            {
                "level": "danger",
                "title": "Массовый адрес регистрации",
                "description": "По данному адресу зарегистрировано более 70 юрлиц.",
            },
            {
                "level": "danger",
                "title": "Процесс ликвидации",
                "description": "В ЕГРЮЛ внесена запись о предстоящем исключении организации.",
            },
            {
                "level": "danger",
                "title": "Долги перед ФССП",
                "description": "Обнаружено 4 открытых производства на сумму более 2.5 млн руб.",
            },
        ],
        "recommendations": [
            "Категорически не рекомендуется производить авансирование.",
            "Запросить независимую банковскую гарантию либо отказаться от сделки.",
        ],
    },
}


def get_counterparty_data(inn: str) -> CounterpartyCheckResponse:
    clean_inn = inn.strip()

    if clean_inn in MOCK_DATA:
        return CounterpartyCheckResponse(**MOCK_DATA[clean_inn])


    return CounterpartyCheckResponse(
        company=CounterpartyDetails(
            inn=clean_inn,
            ogrn="1027739000000",
            name=f"ООО Контрагент ({clean_inn})",
            full_name=f'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КОНТРАГЕНТ {clean_inn}"',
            status="Действующая",
            registration_date="2021-03-12",
            ceo_name="Петров Алексей Сергеевич",
            legal_address="г. Москва, ул. Тверская, д. 1",
            authorized_capital=50000.0,
            is_msp=True,
            tax_system="УСН Доходы-Расходы",
        ),
        risk_score=75,
        risk_status="YELLOW",
        summary_verdict="Средний уровень риска. Требуется базовая осмотрительность при постоплате.",
        risk_factors=[
            {
                "level": "warning",
                "title": "Судебная активность",
                "description": "Наличие арбитражных споров в качестве ответчика.",
            },
            {
                "level": "success",
                "title": "Субъект МСП",
                "description": "Компания состоит в Едином реестре субъектов МСП.",
            },
        ],
        recommendations=[
            "Проверить полномочия директора по свежей выписке ЕГРЮЛ.",
            "Предусмотреть постоплату по факту приемки работ/товаров.",
        ],
    )