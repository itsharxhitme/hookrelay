from hookrelay.db.session import session_scope
from hookrelay.db.models import Delivery, DeliveryAttempt
from hookrelay.worker.claim import claim_one_delivery
from hookrelay.worker.reaper import reap_expired_leases
from hookrelay.worker.run_once import run_once
from sqlalchemy import text, select
import httpx2
import asyncio

async def crash_simulation():
    
    async with session_scope() as session:
        await session.execute(text("DELETE FROM delivery_attempts"))
        await session.execute(text("DELETE FROM deliveries"))
        await session.execute(text("DELETE FROM events"))
    
    async with httpx2.AsyncClient() as client:
        data = {
            "event_type": "user.created",
            "payload":{
                "user_id":"demo-123"
            }
        }
        res = await client.post(url='http://127.0.0.1:8000/events',json=data)
        print(f"POST /events -> {res.status_code}")        
    
    async with session_scope() as session:
        
        claimed = await claim_one_delivery(session=session)
    
    
    async with session_scope() as session:
        
       delivery = await session.get(Delivery, claimed.delivery_id)
       attempt = await session.get(DeliveryAttempt, claimed.attempt_id)
    
    print(f"delivery_status -> {delivery.status}")
    print(f"delivery attempt count -> {delivery.attempt_count}")
    print(f"attempt outcome -> {attempt.outcome}")
    
    async with session_scope() as session:
        
        await session.execute(text(
            """
                UPDATE deliveries
                SET lease_expiry = now() - interval '1 second'
                WHERE id = :id
            """
        ),{"id":claimed.delivery_id})

    async with session_scope() as session:
        reaped = await reap_expired_leases(session = session)
    

    print(f"expired leases reap count -> {reaped}")
    
    async with session_scope() as session:
            
            await session.execute(text(
                """
                    UPDATE deliveries
                    SET due_time = now()
                    WHERE id = :id
                """
            ),{"id":claimed.delivery_id})
            
    async with session_scope() as session:
            
        delivery = await session.get(Delivery, claimed.delivery_id)
        attempt = await session.get(DeliveryAttempt, claimed.attempt_id)
    
   
    print(f"delivery status -> {delivery.status}")
    print(f"delivery attempt count -> {delivery.attempt_count}")
    
    
    
    await run_once()
    
    async with session_scope() as session:
                    
        delivery = await session.get(Delivery, claimed.delivery_id)
        attempts = (await session.execute(select(DeliveryAttempt).where(DeliveryAttempt.delivery_id == claimed.delivery_id).order_by(DeliveryAttempt.attempt_number))).scalars().all()
        

    print(f"delivery status -> {delivery.status}")
    print(f"delivery attempt count -> {delivery.attempt_count}")
    
    for attempt in attempts:
        print(f"\nAttempt Number {attempt.attempt_number}")
        print(f"Attempt outcome {attempt.outcome}")
        

def main():
    asyncio.run(crash_simulation())

if __name__ == "__main__":
    main()