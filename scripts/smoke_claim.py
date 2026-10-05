import asyncio
from hookrelay.db.session import session_scope
from hookrelay.worker.claim import claim_one_delivery


async def main():
    async with session_scope() as session:
        claimed = await claim_one_delivery(session)
    if claimed is None:
        print("no due deliveries")
    else:
        print(f"claimed: {claimed.delivery_id}")
        print(f"  attempt_number: {claimed.attempt_number}")
        print(f"  attempt_id: {claimed.attempt_id}")
        print(f"  lease_token: {claimed.lease_token[:8]}...")
        print(f"  lease_expiry: {claimed.lease_expiry}")
        print(f"  payload: {claimed.payload}")


if __name__ == "__main__":
    asyncio.run(main())