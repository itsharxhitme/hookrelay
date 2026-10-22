from sqlalchemy.ext.asyncio import AsyncSession
from hookrelay.domain import ClaimedWork, SendResult
from sqlalchemy import text
from hookrelay.worker.policy import classify_result, compute_next_due_time, MAX_ATTEMPTS
from datetime import datetime , timezone



async def finalize_attempt(
    session: AsyncSession,
    claimed: ClaimedWork,
    result: SendResult
) -> bool:
        
        classification = classify_result(result)
        
        status = ''
        
        next_due_time = None
        if classification == 'terminal':
                status = 'failure'
        elif classification == 'retryable':
                if claimed.attempt_number >= MAX_ATTEMPTS:
                        status = 'exhausted'
                else:
                        next_due_time = compute_next_due_time(attempt_number=claimed.attempt_number, now = datetime.now(timezone.utc))
                        status = 'pending'
        else:
                status = 'success'
        
        res = await session.execute(text("""
                UPDATE deliveries 
                SET status = :delivery_outcome, 
                lease_token = NULL,
                lease_expiry = NULL ,
                due_time = CASE
                        WHEN :condition_met THEN :next_due_time
                        ELSE due_time
                        END 
                WHERE lease_token = :lease_token AND id = :id
                returning id
                """),{"id":claimed.delivery_id,"delivery_outcome":status, "lease_token":claimed.lease_token, "condition_met":status == 'pending', "next_due_time":next_due_time
        })
        
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
                """),{"finished_at":result.finished_at, "outcome":'success' if status == 'success' else 'failure',"response_status":result.status_code,"error_summary":result.error_summary,"attempt_id":claimed.attempt_id}))


        return True

    
    
    
    