import asyncio, pytest
from inference.scheduler import InferenceScheduler
def test_queue_rejects_when_full():
    async def go():
        s=InferenceScheduler(1,1)
        await s.queue.put((None,(),None))
        with pytest.raises(RuntimeError): await s.run(lambda:1)
    asyncio.run(go())
