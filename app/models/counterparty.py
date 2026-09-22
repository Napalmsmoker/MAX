from typing import List, Optional
from pydantic import BaseModel, Field


class RiskFactor(BaseModel):
    level: str = Field(..., description="danger | warning | success")
    title: str = Field(..., description="Название фактора риска")
    description: str = Field(..., description="Описание риска")


class CounterpartyCheckRequest(BaseModel):
    query: str = Field(
        ...,
        description="ИНН (10 или 12 цифр) или ОГРН контрагента",
        examples=["7707083893", "7701999999"],
    )


class CounterpartyDetails(BaseModel):
    inn: str
    ogrn: str
    name: str
    full_name: str
    status: str
    registration_date: str
    ceo_name: Optional[str] = None
    legal_address: str
    authorized_capital: Optional[float] = None
    is_msp: bool = Field(..., description="Субъект МСП")
    tax_system: Optional[str] = None


class CounterpartyCheckResponse(BaseModel):
    company: CounterpartyDetails
    risk_score: int = Field(
        ..., ge=0, le=100, description="Индекс благонадежности (0-100)"
    )
    risk_status: str = Field(
        ..., description="GREEN (Надежный) | YELLOW (Внимание) | RED (Высокий риск)"
    )
    summary_verdict: str
    risk_factors: List[RiskFactor]
    recommendations: List[str]