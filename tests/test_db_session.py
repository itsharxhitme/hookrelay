import uuid
import pytest
from sqlalchemy import select, delete
from hookrelay.db.models import Tenant
from hookrelay.db.session import session_scope


async def test_session_scope_insert_and_query():
    tenant_id = uuid.uuid4().hex
    name = f"test-{tenant_id}"
    try:
        async with session_scope() as session:
            session.add(Tenant(id=tenant_id, name=name))

        async with session_scope() as session:
            result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = result.scalar_one()
            assert tenant.id == tenant_id
            assert tenant.name == name
    finally:
        async with session_scope() as session:
            await session.execute(delete(Tenant).where(Tenant.id == tenant_id))