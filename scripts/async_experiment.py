import asyncio
import time

async def work_await():
    await asyncio.sleep(1)
    

async def work_blocking():
    time.sleep(1)

async def with_await():
    start =time.perf_counter()
    await asyncio.gather(work_await(), work_await(), work_await())
    print(f"await version: {time.perf_counter() - start:.2f}s")        

async def with_blocking():
    start = time.perf_counter()
    await asyncio.gather(work_blocking(),work_blocking(),work_blocking())
    print(f"blocking version: {time.perf_counter() - start:.2f}s")        
 

async def main():
    await with_await()
    await with_blocking()
    
if __name__ == "__main__":
    asyncio.run(main())    
    
        