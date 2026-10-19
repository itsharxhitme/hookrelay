from hookrelay.db.session import session_scope
from hookrelay.db.models import Endpoint
from hookrelay.worker.claim import claim_one_delivery
from hookrelay.config import get_required
from hookrelay.worker.sender import SecureWebhookSender
from hookrelay.worker.complete import finalize_attempt
from hookrelay.domain import SendResult
from datetime import datetime, timezone

async def run_once():
    
    async with session_scope() as session:   
        claimed = await claim_one_delivery(session=session)
        
    if claimed is None:
        print('No due deliveries')
        return 
    
    async with session_scope() as session:
        
        endpoint = await session.get(Endpoint, claimed.endpoint_id)
        
    if endpoint is None :
        result = SendResult(
            delivery_id = claimed.delivery_id, 
            is_success = False,
            status_code = None,
            error_summary= "endpoint not found",
            started_at= datetime.now(timezone.utc),
            finished_at= datetime.now(timezone.utc)
            )
        async with session_scope() as session:
            await finalize_attempt(session = session, claimed = claimed, result = result)
        return 
    
    secret = get_required(endpoint.signing_secret_ref)
    sender = SecureWebhookSender()
        
    result = await sender.send(claimed, endpoint.url,secret)
    
    async with session_scope() as session:
        await finalize_attempt(session = session, claimed = claimed, result = result)
        
        
    print(f"attempt with delivery_id: {result.delivery_id} processed with outcome: {result.is_success} status: {result.status_code}")
        