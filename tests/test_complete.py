import pytest
from hookrelay.db.session import session_scope
from sqlalchemy import text
from hookrelay.db.models import Event, Delivery, DeliveryAttempt
import uuid
from hookrelay.hashing import sha256_hex
from hookrelay.domain import ClaimedWork, SendResult
from hookrelay.worker.complete import finalize_attempt
from datetime import datetime, timezone, timedelta
from hookrelay.worker.policy import MAX_ATTEMPTS
from dataclasses import replace

def make_result(claimed: ClaimedWork, is_success: bool, status_code: int | None = 200) -> SendResult:
    return SendResult(
        delivery_id=claimed.delivery_id,
        is_success=is_success,
        status_code=status_code,
        error_summary=None if is_success else f"HTTP {status_code}",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )
@pytest.fixture
async def claimed_delivery():
    
    async with session_scope() as session:
        await session.execute(text("DELETE FROM delivery_attempts"))
        await session.execute(text("DELETE FROM deliveries"))
        await session.execute(text("DELETE FROM events"))
        
        event_id = uuid.uuid4().hex
        payload = b'{"user_id":"12"}'
        payload_hash = sha256_hex(payload)
        new_event = Event(id=event_id, tenant_id = 'local-tenant', event_type="user.created", payload= payload, payload_hash = payload_hash)
        session.add(new_event)
        await session.flush()
        
        delivery_id = uuid.uuid4().hex
        lease_token = uuid.uuid4().hex
        lease_expiry = datetime.now(timezone.utc) + timedelta(seconds=60)
        new_delivery = Delivery(id = delivery_id, event_id = event_id, endpoint_id='local-endpoint', status = 'in_progress', lease_token= lease_token, lease_expiry = lease_expiry, attempt_count = 1)
        
        session.add(new_delivery)
        await session.flush()
        
        attempt_id = uuid.uuid4().hex
        new_attempt = DeliveryAttempt(id = attempt_id, delivery_id = delivery_id, attempt_number = 1)
        session.add(new_attempt)
    
    claimed = ClaimedWork(
        event_id=event_id,
        endpoint_id='local-endpoint',
        delivery_id=delivery_id,
        payload=payload,
        attempt_id=attempt_id,
        attempt_number=1,
        lease_token=lease_token,
        lease_expiry=lease_expiry
    )
    yield claimed
    async with session_scope() as session:
        await session.execute(text("DELETE FROM delivery_attempts"))
        await session.execute(text("DELETE FROM deliveries"))
        await session.execute(text("DELETE FROM events"))


async def test_finalize_attempt_success(claimed_delivery):
    claimed = claimed_delivery
    result =  make_result(claimed, is_success=True)
    async with session_scope() as session:
        response  = await finalize_attempt(claimed=claimed,session=session, result=result)

    assert response is True
    
    async with session_scope() as session:
        
        delivery = await session.get(Delivery, claimed.delivery_id)
    
        attempt = await session.get(DeliveryAttempt, claimed.attempt_id)
        
    assert delivery.status == 'success'
    assert delivery.lease_token is None
    assert delivery.lease_expiry is None
    assert attempt.outcome == 'success'
    assert attempt.response_status == 200
    assert attempt.finished_at is not None
    
async def test_finalize_attempt_retryable_500_schedules_retry(claimed_delivery):
    claimed = claimed_delivery
    result =  make_result(claimed, is_success=False, status_code=500)
    async with session_scope() as session:
        response = await finalize_attempt(claimed=claimed,session=session, result=result)

    assert response is True
    
    async with session_scope() as session:
        
       delivery = await session.get(Delivery, claimed.delivery_id)
           
       attempt = await session.get(DeliveryAttempt, claimed.attempt_id)
        
    assert delivery.status == 'pending'
    assert delivery.lease_token is None
    assert delivery.lease_expiry is None
    assert delivery.due_time > datetime.now(timezone.utc)
    assert attempt.outcome == 'failure'
    assert attempt.response_status == 500
    assert attempt.finished_at is not None    

async def test_finalize_attempt_terminal_400_marks_failure(claimed_delivery):
    claimed = claimed_delivery
    result =  make_result(claimed, is_success=False, status_code=400)
    async with session_scope() as session:
        response = await finalize_attempt(claimed=claimed,session=session, result=result)

    assert response is True
    
    async with session_scope() as session:
        
       delivery = await session.get(Delivery, claimed.delivery_id)
           
       attempt = await session.get(DeliveryAttempt, claimed.attempt_id)
        
    assert delivery.status == 'failure'
    assert delivery.lease_token is None
    assert delivery.lease_expiry is None
    assert attempt.outcome == 'failure'
    assert attempt.response_status == 400
    assert attempt.finished_at is not None    

async def test_finalize_attempt_exhausted_marks_exhausted(claimed_delivery):
    claimed = replace(claimed_delivery, attempt_number= MAX_ATTEMPTS)

    result =  make_result(claimed, is_success=False, status_code=500)
    
    async with session_scope() as session:
        response = await finalize_attempt(claimed=claimed,session=session, result=result)

    assert response is True
    
    async with session_scope() as session:
        
       delivery = await session.get(Delivery, claimed.delivery_id)
           
       attempt = await session.get(DeliveryAttempt, claimed.attempt_id)
        
    assert delivery.status == 'exhausted'
    assert delivery.lease_token is None
    assert delivery.lease_expiry is None
    assert attempt.outcome == 'failure'
    assert attempt.response_status == 500
    assert attempt.finished_at is not None   

async def test_finalize_attempt_stale_token(claimed_delivery):
    claimed = claimed_delivery
    
    async with session_scope() as session:
        await session.execute(text(
    """
        UPDATE deliveries
        SET lease_token = 'new_token'
        WHERE id = :delivery_id
    """
        ),{"delivery_id":claimed.delivery_id})
        
    result = make_result(claimed, is_success=True)
        
    async with session_scope() as session:
        response = await finalize_attempt(claimed=claimed,session=session, result=result)
            
    assert response is False
        
    async with session_scope() as session:
                
        delivery = await session.get(Delivery, claimed.delivery_id)
            
        attempt = await session.get(DeliveryAttempt, claimed.attempt_id)
                
    assert delivery.status == 'in_progress'
    assert delivery.lease_token == 'new_token'
    assert delivery.lease_expiry is not None
    assert attempt.outcome is None
    assert attempt.response_status is None
    assert attempt.finished_at is None


async def test_finalize_twice(claimed_delivery):
    claimed = claimed_delivery
    result =  make_result(claimed, is_success=False, status_code=500)
    
    async with session_scope() as session:
        response1 = await finalize_attempt(claimed=claimed,session=session, result=result)
    
    assert response1 is True
    
    async with session_scope() as session:
        response2 = await finalize_attempt(claimed=claimed,session=session, result=result)
        
    assert response2 is False
    
    async with session_scope() as session:
            
        delivery = await session.get(Delivery, claimed.delivery_id)
        
    assert delivery.status == 'pending'
    assert delivery.lease_token is None
    
async def test_finalize_attempt_success_does_not_change_due_time(claimed_delivery):
    
    claimed = claimed_delivery
    
    async with session_scope() as session:
        
        original_delivery = await session.get(Delivery, claimed.delivery_id)
        original_due_time = original_delivery.due_time
    
    result = make_result(claimed = claimed, is_success=True)
    
    async with session_scope() as session:
            response = await finalize_attempt(claimed=claimed,session=session, result=result)
            
    assert response is True
    
    async with session_scope() as session:
        delivery = await session.get(Delivery, claimed.delivery_id)
    
    assert delivery.due_time == original_due_time

async def test_finalize_retryable_status_code_none_schedules_retry(claimed_delivery):
    
    claimed = claimed_delivery
    
    async with session_scope() as session:
        
        original_delivery = await session.get(Delivery, claimed.delivery_id)
        original_due_time = original_delivery.due_time
    
    result = replace(make_result(claimed = claimed, is_success=False, status_code=None),error_summary = "transport error")
    
    async with session_scope() as session:
            response = await finalize_attempt(claimed=claimed,session=session, result=result)
            
    assert response is True
    
    async with session_scope() as session:
        delivery = await session.get(Delivery, claimed.delivery_id)
    
    assert delivery.status == 'pending'