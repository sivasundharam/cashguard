from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class InvoiceStatus(str, Enum):
    pending = "pending"
    overdue = "overdue"
    paid = "paid"
    partial = "partial"


class CaseStatus(str, Enum):
    new = "new"
    analyzing = "analyzing"
    draft_ready = "draft_ready"
    sent = "sent"
    responded = "responded"
    escalated = "escalated"
    resolved = "resolved"
    rejected = "rejected"
    closed = "closed"


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Tone(str, Enum):
    warm = "warm"
    firm = "firm"
    serious = "serious"


class Invoice(BaseModel):
    invoice_id: str
    client_id: str
    client_name: str
    amount: float
    due_date: datetime
    status: InvoiceStatus = InvoiceStatus.pending
    days_overdue: int = 0
    source: str = "google_sheets"
    synced_at: datetime = Field(default_factory=datetime.utcnow)


class ClientProfile(BaseModel):
    client_id: str
    client_name: str
    contact_email: str
    relationship_tenure_months: int
    total_invoices: int
    late_payment_count: int
    avg_days_to_pay: float
    tone_recommendation: Tone = Tone.firm
    relationship_score: int = 50


class CollectionsCase(BaseModel):
    case_id: str
    invoice_id: str
    client_id: str
    status: CaseStatus = CaseStatus.new
    urgency: Urgency = Urgency.medium
    tone: Tone = Tone.firm
    outreach_attempts: int = 0
    last_contact_date: Optional[datetime] = None
    next_action_date: Optional[datetime] = None
    email_draft: Optional[str] = None
    gap_linked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DailyForecast(BaseModel):
    date: str
    projected_balance: float
    gap: bool


class ForecastSnapshot(BaseModel):
    snapshot_date: str
    current_balance: float
    daily_forecast: List[DailyForecast]
    gap_dates: List[str]
    gap_amount: float
    linked_invoices: List[str]


class StatusUpdate(BaseModel):
    status: str
