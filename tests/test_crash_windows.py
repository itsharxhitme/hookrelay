import pytest
import httpx2
import uuid
from sqlalchemy import select, text
from hookrelay.db.models import DeliveryAttempt, Event, Delivery
from hookrelay.db.session import session_scope
from hookrelay.worker.run_once import run_once
from hookrelay.worker.claim import claim_one_delivery
from hookrelay.hashing import sha256_hex
from hookrelay.worker.reaper import reap_expired_leases
from hookrelay.worker.sender import SecureWebhookSender

@pytest.fixture
async def clean_receiver():
    async with httpx2.AsyncClient() as client:
        await client.post('http://127.0.0.1:8001/receipts/reset')
    
    yield

@pytest.fixture
async def ingested_delivery():
    
    async with session_scope() as session:
        await session.execute(text("DELETE FROM delivery_attempts"))
        await session.execute(text("DELETE FROM deliveries"))
        await session.execute(text("DELETE FROM events"))
        
    event_id = uuid.uuid4().hex
    payload = b'{"user_id":"demo-123"}'
    payload_hash = sha256_hex(payload)
    delivery_id = uuid.uuid4().hex
    
    async with session_scope() as session:
        
        event = Event(id = event_id, tenant_id = 'local-tenant', event_type = "user.created", payload=payload, payload_hash = payload_hash)
        session.add(event)
        await session.flush()
        delivery = Delivery(id=delivery_id, event_id=event_id, endpoint_id='local-endpoint')
        session.add(delivery)

    yield
    
    async with session_scope() as session:
        await session.execute(text("DELETE FROM delivery_attempts"))
        await session.execute(text("DELETE FROM deliveries"))
        await session.execute(text("DELETE FROM events"))



async def test_post_acceptance_crash_causes_duplicate_delivery(clean_receiver, ingested_delivery):
    
    async with session_scope() as session:
        claimed = await claim_one_delivery(session)
    
    assert claimed is not None
    
    sender = SecureWebhookSender()
    
    await sender.send(work = claimed, url = "http://127.0.0.1:8001/receive",secret='test-secret')
    
    async with session_scope() as session:
        await session.execute(text(
    """
        UPDATE deliveries
        SET lease_expiry = now() - interval '1 second'
        WHERE id = :id
    """
        ),{"id": claimed.delivery_id})
    
    async with session_scope() as session:
        reaped = await reap_expired_leases(session=session)
    
    assert reaped == 1
    
    async with session_scope() as session:
        await session.execute(text(
    """
        UPDATE deliveries
        SET due_time = now()
        WHERE id = :id
    """
        ),{"id":claimed.delivery_id})
    
    await run_once()    
    
    async with httpx2.AsyncClient() as client:
        res = await client.get("http://127.0.0.1:8001/receipts")
        body = res.json()
    
    assert body["count"] == 2
    assert body["receipts"][0]["delivery_id"] == body["receipts"][1]["delivery_id"]
    async with session_scope() as session:
        attempts = (await session.execute(
            select(DeliveryAttempt)
            .where(DeliveryAttempt.delivery_id == claimed.delivery_id)
            .order_by(DeliveryAttempt.attempt_number)
        )).scalars().all()
    assert len(attempts) == 2
    assert attempts[0].outcome == "unknown"
    assert attempts[1].outcome == "success"


async def test_pre_acceptance_crash_produces_single_delivery(clean_receiver, ingested_delivery):
    
    async with session_scope() as session:
        claimed = await claim_one_delivery(session)
    
    assert claimed is not None
    
    
    async with session_scope() as session:
        await session.execute(text(
    """
        UPDATE deliveries
        SET lease_expiry = now() - interval '1 second'
        WHERE id = :id
    """
        ),{"id": claimed.delivery_id})
    
    async with session_scope() as session:
        reaped = await reap_expired_leases(session=session)
    
    assert reaped == 1
    
    async with session_scope() as session:
        await session.execute(text(
    """
        UPDATE deliveries
        SET due_time = now()
        WHERE id = :id
    """
        ),{"id":claimed.delivery_id})
    
    await run_once()    
    
    async with httpx2.AsyncClient() as client:
        res = await client.get("http://127.0.0.1:8001/receipts")
        body = res.json()
    
    assert body["count"] == 1
    assert body["receipts"][0]["delivery_id"] == claimed.delivery_id
    async with session_scope() as session:
        attempts = (await session.execute(
            select(DeliveryAttempt)
            .where(DeliveryAttempt.delivery_id == claimed.delivery_id)
            .order_by(DeliveryAttempt.attempt_number)
        )).scalars().all()
    assert len(attempts) == 2
    assert attempts[0].outcome == "unknown"
    assert attempts[1].outcome == "success"
    