import os
from dotenv import load_dotenv
import asyncio
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from hookrelay.worker.signing import verify_signature

load_dotenv()
app = FastAPI()

RECEIVER_SECRET = os.environ["HOOKRELAY_RECEIVER_SECRET"]


RECEIPTS: list[dict] = []

@app.post("/receive")
async def receive(request: Request):
    raw_body = await request.body()
    
    signature_header = request.headers.get("x-webhook-signature")
    
    if signature_header is None:
        return Response(status_code=401)
    
    verified = verify_signature(RECEIVER_SECRET, signature_header, raw_body)
    
    if not verified:
        return Response(status_code= 401)
    
    behavior = request.headers.get("x-test-behavior")

    if behavior == "status_500":
        return Response(status_code=500)

    if behavior == "huge":
        return Response(content=b"x" * (2 * 1024 * 1024), media_type="application/octet-stream")

    if behavior == "gzip":
        return Response(content=b"anything", headers={"content-encoding": "gzip"})

    if behavior == "stall":
        await asyncio.sleep(10)
        return Response(status_code=200)
    
    if behavior == "trickle":
        async def stream():
            for _ in range(60):
                yield b"x"
                await asyncio.sleep(2)
        return StreamingResponse(stream(), media_type="application/octet-stream")
        
    if behavior == "redirect":
        return Response(status_code=302, headers={"location": "http://evil.example.com/"})
    
    RECEIPTS.append({
        "delivery_id": request.headers.get("x-delivery-id"),
        "body": raw_body
    })
    return Response(status_code=200)


@app.get("/receipts")
async def list_receipts():
    return {
        "count": len(RECEIPTS),
        "receipts": [
            {"delivery_id": r["delivery_id"], "body_size": len(r["body"])}
            for r in RECEIPTS
        ],
    }

# Test-only endpoint. Not for production use.
@app.post("/receipts/reset")
async def reset_receipts():
    RECEIPTS.clear()
    return {"status": "cleared"}