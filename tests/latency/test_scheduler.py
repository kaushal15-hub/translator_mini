import asyncio
from inference.scheduler import InferenceScheduler
def test_scheduler_runs_function():
    async def go():
        s=InferenceScheduler(4,1)
        return await s.run(lambda x:x+1,4)
    assert asyncio.run(go())==5
