import asyncio
import os
import pytest
import uvicorn
from datetime import datetime, timezone
from hookrelay.domain import ClaimedWork
from hookrelay.worker.sender import SecureWebhookSender

os.environ.setdefault("HOOKRELAY_RECEIVER_SECRET","test-secret")
@pytest.fixture(scope="session", autouse=True)
async def receiver_server():
    

    config = uvicorn.Config(
        "hookrelay.receiver.app:app",
        host="127.0.0.1",
        port=8001,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    
    while not server.started:
        await asyncio.sleep(0.05)
        
    yield
    
    server.should_exit = True
    await task




def make_claimed(payload: bytes = b'{"x":1}', delivery_id: str = "test-delivery") -> ClaimedWork:
    return ClaimedWork(
        event_id="evt-1",
        endpoint_id="local-endpoint",
        delivery_id=delivery_id,
        payload=payload,
        attempt_id="att-1",
        attempt_number=1,
        lease_token="tok-1",
        lease_expiry=datetime.now(timezone.utc),
    )

async def test_send_returns_success_on_200(receiver_server):
    sender = SecureWebhookSender()
    claimed = make_claimed()
    result = await sender.send(work=claimed, url="http://127.0.0.1:8001/receive", secret="test-secret")

    assert result.is_success is True
    assert result.status_code == 200
    assert result.error_summary is None

async def test_send_fails_on_wrong_secret(receiver_server):
    sender = SecureWebhookSender()
    claimed = make_claimed()
    result = await sender.send(claimed, url="http://127.0.0.1:8001/receive", secret="wrong-secret")

    assert result.is_success is False
    assert result.status_code == 401

async def test_send_classifies_500_as_failure(receiver_server):
    sender = SecureWebhookSender()
    claimed = make_claimed()
    
    result = await sender.send(claimed,"http://127.0.0.1:8001/receive",secret="test-secret",extra_headers={'x-test-behavior':'status_500'})
    
    assert result.is_success is False
    assert result.status_code == 500

async def test_send_rejects_huge_response(receiver_server):
    
    sender = SecureWebhookSender(max_response_bytes=1024)
    claimed = make_claimed()
    result = await sender.send(claimed,"http://127.0.0.1:8001/receive",secret="test-secret",extra_headers={'x-test-behavior':'huge'})
    
    assert result.is_success is False
    assert "cap" in (result.error_summary or "").lower() or "exceeded" in (result.error_summary or "").lower()

async def test_send_rejects_gzip(receiver_server):
    sender = SecureWebhookSender(max_response_bytes=1024)
    claimed = make_claimed()
    result = await sender.send(claimed,"http://127.0.0.1:8001/receive",secret="test-secret",extra_headers={'x-test-behavior':'gzip'})
        
    assert result.is_success is False
    assert "unsupported content-encoding" in (result.error_summary or "").lower()
    
async def test_send_enforces_read_timeout(receiver_server):
    sender = SecureWebhookSender(max_response_bytes=1024)
    claimed = make_claimed()
    result = await sender.send(claimed,"http://127.0.0.1:8001/receive",secret="test-secret",extra_headers={'x-test-behavior':'stall'})
            
    assert result.is_success is False
    assert "network timeout" in (result.error_summary or "").lower()
    
async def test_send_enforces_total_deadline(receiver_server):
    sender = SecureWebhookSender(max_response_bytes=1024)
    claimed = make_claimed()
    result = await sender.send(claimed,"http://127.0.0.1:8001/receive",secret="test-secret",extra_headers={'x-test-behavior':'trickle'})
            
    assert result.is_success is False
    assert "hard timeout" in (result.error_summary or "").lower()
    
async def test_send_does_not_follow_redirects(receiver_server):
    sender = SecureWebhookSender(max_response_bytes=1024)
    claimed = make_claimed()
    result = await sender.send(claimed,"http://127.0.0.1:8001/receive",secret="test-secret",extra_headers={'x-test-behavior':'redirect'})
            
    assert result.is_success is False
    assert result.status_code == 302

async def test_send_handles_connection_refused():
    sender = SecureWebhookSender(max_response_bytes=1024)
    claimed = make_claimed()
    result = await sender.send(claimed,"http://127.0.0.1:9999/receive",secret="test-secret")
            
    assert result.is_success is False
    assert result.status_code is None   
    assert "transport error" in (result.error_summary or "").lower()