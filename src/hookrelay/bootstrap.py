import asyncio
from sqlalchemy import text
from hookrelay.config import get_required
from hookrelay.db.session import session_scope

TENANT_ID = "local-tenant"
TENANT_NAME = "Local Development"
ENDPOINT_ID = "local-endpoint"
ENDPOINT_URL = "http://127.0.0.1:8001/receive"
SECRET_REF = "HOOKRELAY_ENDPOINT_LOCAL_RECEIVER_SECRET"

async def bootstrap() -> None:
    get_required(SECRET_REF)
    async with session_scope() as session:
        
        await session.execute(
            text("""
                INSERT INTO tenants (id, name)
                VALUES (:id, :name)
                ON CONFLICT (id) DO NOTHING
            """),
            {"id": TENANT_ID, "name": TENANT_NAME},
            )
        await session.execute(
            text("""
                INSERT INTO endpoints (id, tenant_id, url ,signing_secret_ref, enabled)
                V (:id, :tenant_id, :url, :signing_secret_ref, true)
                ON CONFLICT (id) DO NOTHING
                 """),
            {"id":ENDPOINT_ID, "tenant_id":TENANT_ID, "url":ENDPOINT_URL, "signing_secret_ref":SECRET_REF}
            
        )
    print(f"Bootstrap complete: tenant={TENANT_ID} endpoint={ENDPOINT_ID}")

if __name__ == "__main__":
    asyncio.run(bootstrap())
    