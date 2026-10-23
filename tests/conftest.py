import asyncio
import os
import pytest
import uvicorn

os.environ["HOOKRELAY_RECEIVER_SECRET"] = "test-secret"
os.environ["HOOKRELAY_ENDPOINT_LOCAL_RECEIVER_SECRET"] = "test-secret"

@pytest.fixture(scope = 'session', autouse=True)
async def receiver_server():
    
    config = uvicorn.Config(
        "hookrelay.receiver.app:app",
        host="127.0.0.1",
        port=8001,
        log_level="warning"
    )
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    
    while not server.started:
        await asyncio.sleep(0.05)
    
    yield
    
    server.should_exit = True
    await task