from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime , timezone
from hookrelay.worker.policy import MAX_ATTEMPTS, compute_next_due_time
async def reap_expired_leases(session:AsyncSession, *, batch_size: int = 10) -> int:
    """Recover up to batch_size expired_leases. Returns number reaped"""
    
    count_reaped  = 0
    selected_deliveries = await session.execute(text(
        """
        SELECT id, lease_token, attempt_count
        FROM deliveries
        WHERE status = 'in_progress' AND lease_expiry < now()
        ORDER BY lease_expiry 
        LIMIT :limit
        
        FOR UPDATE SKIP LOCKED
        """
    ),{"limit":batch_size})
        
    for delivery in selected_deliveries:
        status = "exhausted" if delivery.attempt_count >= MAX_ATTEMPTS else "pending"
        next_due_time = None
        
        if status == 'pending':
            next_due_time = compute_next_due_time(attempt_number=delivery.attempt_count,now = datetime.now(timezone.utc))
            
        updated = await session.execute(text(
            """
            UPDATE deliveries
            SET status = :status,
            lease_token = NULL,
            lease_expiry = NULL,
            due_time = CASE
            WHEN :condition THEN :next_due_time 
            ELSE due_time
            END
            WHERE id = :delivery_id AND lease_token = :observed_token AND lease_expiry < now()
            RETURNING id 
            """
        ),{"status":status,"delivery_id":delivery.id,"observed_token":delivery.lease_token, "condition":status == 'pending',"next_due_time": next_due_time})
        
        updated_id = updated.scalar() 
        if updated_id is None:
            continue
            
        await session.execute(text(
        """
            UPDATE delivery_attempts
            SET outcome = 'unknown',
            error_summary = 'lease expired; outcome unknown',
            finished_at = now(),
            response_status = NULL
            WHERE delivery_id = :delivery_id AND OUTCOME is NULL
        """
        ),{"delivery_id": delivery.id })        
        count_reaped += 1
        
    return count_reaped