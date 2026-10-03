import pytest
from httpx2 import AsyncClient, ASGITransport
from sqlalchemy import text, select, func
from hookrelay.api import app
from hookrelay.db.session import session_scope
from hookrelay.db.models import Event, Delivery

@pytest.fixture
async def cleanup_events():
    yield
    async with session_scope() as session:
        await session.execute(text("DELETE FROM deliveries"))
        await session.execute(text("DELETE FROM events"))


def make_client(): 
    return AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False) ,base_url="http://test")


async def test_post_events_returns_202(cleanup_events):
    async with make_client() as client:
        
        response = await client.post("/events",json={
            "event_type":"user.created",
            "payload":{
                "user_id":"user1"
            }
        })
        assert response.status_code == 202
        body = response.json()
        assert "event_id" in body
        assert body["delivery_count"] >= 1

async def test_post_events_persists_rows(cleanup_events):
    async with make_client() as client:
        
        response = await client.post("/events",json={
                    "event_type":"user.created",
                    "payload":{
                        "user_id":"user1"
                    }
                })
        body = response.json()
        event_id = body['event_id']
        expected_delivery_count = body['delivery_count']
        
        async with session_scope() as session:
            
            created_event = await session.execute(select(Event.id,Event.tenant_id,Event.event_type).where(Event.id == event_id))
            event_details = created_event.fetchone()
        
        assert event_details is not None
        assert event_details.tenant_id == "local-tenant"
        assert event_details.event_type == "user.created"
        
        async with session_scope() as session:
            delivery_count = (await session.execute(select(func.count()).select_from(Delivery).where(Delivery.event_id == event_id))).scalar()
            
            assert delivery_count == expected_delivery_count

async def test_post_events_missing_payload_returns_422(cleanup_events):
    
    async with make_client() as client:
        
        response = await client.post("/events",json = {"event_type":"user.created"})
    assert response.status_code == 422

async def test_post_events_array_as_body_returns_422(cleanup_events):
    async with make_client() as client:
        response = await client.post("/events",json = [{"event_type":"x"}])
    assert response.status_code == 422
    
async def test_ingest_rolls_back_on_failed_delivery(cleanup_events,monkeypatch):
    
    async def fake_endpoints(session, tenant_id: str):
        return ["does_not_exist"]
    
    monkeypatch.setattr("hookrelay.services.ingest.find_enabled_endpoint_ids",fake_endpoints)
    async with make_client() as client:
        response = await client.post("/events", json={
            "event_type": "user.created",
            "payload": {"user_id": "u1"},
        })

    assert response.status_code == 500
    async with session_scope() as session:
        count = (await session.execute(
            select(func.count()).select_from(Event)
        )).scalar()
        assert count == 0
        