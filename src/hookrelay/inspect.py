import sys
import asyncio
from hookrelay.db.session import session_scope
from hookrelay.db.models import Delivery, DeliveryAttempt
from sqlalchemy import select 

async def inspect_delivery(delivery_id: str) -> int:
    async with session_scope() as session:
        
        delivery =  await session.get(Delivery, delivery_id)
        
        if delivery is None:
            print(f'no delivery found associated with delivery_id - {delivery_id}')
            return 1
        print('Delivery')
        print(f'id - {delivery.id}')
        print(f'status - {delivery.status}')
        print(f'attempt_count - {delivery.attempt_count}')
        print(f'due_time - {delivery.due_time}')
        print(f'lease_token - {delivery.lease_token}')
        print(f'lease_expiry - {delivery.lease_expiry}')
        print(f'created_at - {delivery.created_at}')
        
        
        query = select(DeliveryAttempt).where(DeliveryAttempt.delivery_id == delivery_id).order_by(DeliveryAttempt.attempt_number)
        result = await session.execute(query)
        
        attempts = result.scalars().all()
        if len(attempts) == 0:
            print("no attempts found associated with delivery_id")
        for attempt in attempts:
            print(f'\n\n\nAttempt - {attempt.attempt_number}')
            print(f'id - {attempt.id}')
            print(f'started_at - {attempt.started_at}')
            print(f'finished_at - {attempt.finished_at}')
            print(f'outcome - {attempt.outcome}')
            print(f'response_status - {attempt.response_status}')
            print(f'error_summary - {attempt.error_summary}')
            
    return 0
            
def main():
    
    if len(sys.argv) < 3 or sys.argv[1] != "delivery":
        print("usage: python -m hookrelay.inspect delivery <delivery_id>")
        return 2

    return asyncio.run(inspect_delivery(sys.argv[2]))
    
    
    

if __name__ == "__main__":
    sys.exit(main())