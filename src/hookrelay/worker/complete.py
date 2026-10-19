from sqlalchemy.ext.asyncio import AsyncSession
from hookrelay.domain import ClaimedWork, SendResult
from sqlalchemy import text
async def finalize_attempt(
    session: AsyncSession,
    claimed: ClaimedWork,
    result: SendResult
) -> bool:
        
        attempt_outcome = 'success' if result.is_success else 'failure'
        delivery_outcome = 'success' if result.is_success else 'failure'
        res = (await session.execute(text("""
                UPDATE deliveries 
                SET status = :delivery_outcome, 
                lease_token = NULL,
                lease_expiry = NULL 
                WHERE lease_token = :lease_token AND id = :id
                returning id
                """),{"id":claimed.delivery_id,"delivery_outcome":delivery_outcome, "lease_token":claimed.lease_token}))
        row = res.fetchone()
        if row is None:
                return False
        
        (await session.execute(text("""
                        UPDATE delivery_attempts 
                        SET finished_at = :finished_at,
                        outcome = :outcome,
                        response_status = :response_status,
                        error_summary = :error_summary
                        WHERE id = :attempt_id
                """),{"finished_at":result.finished_at, "outcome":attempt_outcome,"response_status":result.status_code,"error_summary":result.error_summary,"attempt_id":claimed.attempt_id}))


        return True

    
    
    
    