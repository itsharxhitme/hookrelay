from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, UniqueConstraint, func, LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
class Endpoint(Base):
    __tablename__ = "endpoints"
    id: Mapped[str] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    url:Mapped[str] = mapped_column()
    signing_secret_ref :Mapped[str] = mapped_column()
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at:Mapped[datetime] = mapped_column(server_default=func.now())

class Event(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    event_type:Mapped[str] = mapped_column()
    payload:Mapped[bytes] = mapped_column(LargeBinary)
    payload_hash: Mapped[str] = mapped_column()
    created_at:Mapped[datetime] = mapped_column(server_default=func.now())

class Delivery(Base):
    __tablename__ = "deliveries"
    id: Mapped[str] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"))
    endpoint_id: Mapped[str] = mapped_column(ForeignKey("endpoints.id"))
    status: Mapped[str] = mapped_column(default="pending")
    due_time: Mapped[datetime] = mapped_column(server_default=func.now(),index=True)
    lease_token: Mapped[Optional[str]] = mapped_column()
    lease_expiry: Mapped[Optional[datetime]] = mapped_column()
    attempt_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        UniqueConstraint('event_id','endpoint_id',name = 'uq_delivery_event_endpoint'),
    )

class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"
    id: Mapped[str] = mapped_column(primary_key=True)
    delivery_id: Mapped[str] = mapped_column(ForeignKey("deliveries.id"))
    attempt_number: Mapped[int] = mapped_column()
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column()
    outcome: Mapped[Optional[str]] = mapped_column()
    response_status: Mapped[Optional[int]] = mapped_column()
    error_summary: Mapped[Optional[str]] = mapped_column()
    
    __table_args__ = (
        UniqueConstraint('delivery_id','attempt_number',name = "uq_attempt_delivery_number"),
    )

  
    