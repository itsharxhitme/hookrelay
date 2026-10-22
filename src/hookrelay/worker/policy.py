from typing import Literal
from hookrelay.domain import SendResult
from datetime import datetime
import random

from datetime import datetime, timedelta
RetryClass = Literal['success', 'retryable', 'terminal']

MAX_ATTEMPTS = 5   # TODO(D24): move to endpoint config, snapshot to delivery
INITIAL_BACKOFF_SECONDS = 10
MAX_BACKOFF_SECONDS = 300
BACKOFF_MULTIPLIER = 2

def classify_result(result: SendResult) -> RetryClass:
    
    if result.is_success is True:
        return 'success'
    elif result.status_code is None:
        
        if result.error_summary and ('transport' in result.error_summary.lower() or 'timeout' in result.error_summary.lower()):
            return 'retryable'
        else:
            return 'terminal'
    elif result.status_code // 100 == 5:
        return 'retryable'
    elif result.status_code == 429:
        return 'retryable'
    else :
        return 'terminal'
    

def compute_next_due_time(
    attempt_number: int,
    now: datetime,
    rng: random.Random | None = None
) -> datetime:
    
    if attempt_number < 1:
        raise ValueError("attempt_number must be a positive integer starting at 1")
    
    if rng is None:
        rng = random
    
    base_delay = min(
    INITIAL_BACKOFF_SECONDS * (BACKOFF_MULTIPLIER ** (attempt_number - 1)),
    MAX_BACKOFF_SECONDS,
)
    
    delay = base_delay/2 + rng.uniform(0, base_delay/2)
    
    return now + timedelta(seconds=delay)