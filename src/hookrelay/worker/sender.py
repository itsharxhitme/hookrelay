import httpx2
import time
import asyncio
from datetime import datetime, timezone
from typing import Optional
from hookrelay.domain import ClaimedWork, SendResult
from hookrelay.worker.signing import build_signature_header, current_timestamp

class SecureWebhookSender:
    
    def __init__(
        self,
        max_response_bytes: int = 64*1024,
        total_deadline_seconds: float = 10.0,
        connect_timeout_seconds: float = 3.0,
        read_timeout_seconds: float = 3.0
    ):
        self.max_response_bytes = max_response_bytes
        self.total_deadline_seconds = total_deadline_seconds
        
        self.httpx_timeout = httpx2.Timeout(
            connect=connect_timeout_seconds,
            read=read_timeout_seconds,
            write=read_timeout_seconds,
            pool=connect_timeout_seconds
        )
    
    
    async def send(self, work:ClaimedWork,url: str, secret: str, extra_headers : dict | None = None) -> SendResult:
        
        started_at = datetime.now(timezone.utc)
        timestamp = current_timestamp()
        signature_header = build_signature_header(secret, work.delivery_id, timestamp, work.payload)
        
        
        headers = {
            "Content-Type" : "application/json",
            "X-Webhook-Signature": signature_header,
            "X-Delivery-ID": work.delivery_id
        }
        if extra_headers:
            headers = headers | extra_headers
            
        try:
            
            async with asyncio.timeout(self.total_deadline_seconds):
                async with httpx2.AsyncClient(follow_redirects=False, trust_env=False,timeout=self.httpx_timeout) as client:
                    
                        async with client.stream(
                            "POST", url, headers=headers, content=work.payload
                        ) as response:
                        
                            content_encoding = response.headers.get("content-encoding", "identity").lower()
                            if content_encoding != "identity":
                                return self._build_result(
                                    work.delivery_id,False, None,f"Unsupported content-encoding: {content_encoding}",started_at=started_at,finished_at=datetime.now(timezone.utc)
                            )
                        
                    
                            bytes_read = 0
                        
                        
                            async for chunk in response.aiter_bytes(chunk_size=4096):
                                bytes_read += len(chunk)
                                if bytes_read > self.max_response_bytes:
                                    
                                    return self._build_result(
                                        work.delivery_id,
                                        False,
                                        None,
                                        f"Response exceeded maximum limit of {self.max_response_bytes} bytes",
                                        started_at=started_at,
                                        finished_at=datetime.now(timezone.utc)
                                    )

                            error_message = None if response.is_success else f"HTTP Status {response.status_code}"
                            return self._build_result(
                                work.delivery_id,
                                response.is_success,
                                response.status_code,
                                error_message,
                                started_at,
                                datetime.now(timezone.utc) 
                            )
                            
        except TimeoutError:
            return self._build_result(work.delivery_id,False,None,"Hard timeout reached (total deadline breached)", started_at,datetime.now(timezone.utc))
        except httpx2.TimeoutException as exc:
            return self._build_result(work.delivery_id,False,None,f"Network timeout: {type(exc).__name__}",started_at,datetime.now(timezone.utc))
        except httpx2.RequestError as exc:
            return self._build_result(work.delivery_id,False,None,f"Transport error: {str(exc)}",started_at,datetime.now(timezone.utc))
        except Exception as exc:
            return self._build_result(work.delivery_id,False,None,f"Unexpected: {str(exc)}",started_at,datetime.now(timezone.utc))
    
    def _build_result(
        self,
        delivery_id:str,
        is_success:bool,
        status_code: Optional[int],
        error_summary: Optional[str],
        started_at: datetime,
        finished_at: datetime 
    )  -> SendResult:
        
        return SendResult(
            delivery_id=delivery_id,
            is_success=is_success,
            status_code=status_code,
            error_summary=error_summary[:200] if error_summary else None,
            started_at=started_at,
            finished_at=finished_at
        )