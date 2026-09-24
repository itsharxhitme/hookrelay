from dataclasses import dataclass
from typing import Literal, Optional
from datetime import datetime

DeliveryStatus = Literal['pending','success','failure']
AttemptOutcome = Literal['failure','success','unknown']
@dataclass(frozen=True)
class Event:
    event_id: str
    type: str
    payload: bytes
    created_at: datetime

@dataclass
class Delivery:
    delivery_id: str
    event_id: str
    endpoint_id: str
    status: DeliveryStatus
    due_time: datetime
    created_at: datetime
    lease_token: Optional[str] = None
    lease_expiry: Optional[datetime] = None
    attempt_count: int = 0
    

@dataclass
class DeliveryAttempt:
    attempt_id: str
    delivery_id: str
    attempt_number: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    outcome: Optional[AttemptOutcome] = None
    response_status: Optional[int] = None
    error_summary: Optional[str] = None   