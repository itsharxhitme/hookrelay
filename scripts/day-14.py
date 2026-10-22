import asyncio
from hookrelay.db.session import session_scope
import httpx2
from sqlalchemy import text
from hookrelay.worker.run_once import run_once

async def helper():
    
    async with session_scope() as session:
        
        await session.execute(text("DELETE from delivery_attempts"))
        await session.execute(text("DELETE from deliveries"))
        await session.execute(text("DELETE from events"))
    
    headers = {
        "Content-Type": "application/json"
    }
    body =  {
        "event_type":"user.created",
        "payload":{
            "user_id":"demo-1"
        }
    }
    
    async with httpx2.AsyncClient() as client:
        
        response = await client.post(url = 'http://127.0.0.1:8000/events', headers=headers, json=body)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
        
    res  = await run_once()
        
        
def main():
    asyncio.run(helper())

if __name__ == '__main__':
    main()