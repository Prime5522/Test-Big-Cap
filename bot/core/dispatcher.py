"""Per-channel ordered work queues – keeps posting order and respects flood limits
while different channels are processed fully in parallel."""
import asyncio
import logging

log = logging.getLogger("dispatcher")


class Dispatcher:
    IDLE_TIMEOUT = 120

    def __init__(self):
        self._queues: dict[int, asyncio.Queue] = {}

    def submit(self, chat_id: int, fn, *args):
        q = self._queues.get(chat_id)
        if q is None:
            q = self._queues[chat_id] = asyncio.Queue(maxsize=10000)
            asyncio.create_task(self._worker(chat_id, q))
        try:
            q.put_nowait((fn, args))
        except asyncio.QueueFull:
            log.warning("queue full for %s – dropping job", chat_id)

    async def _worker(self, chat_id: int, q: asyncio.Queue):
        while True:
            try:
                fn, args = await asyncio.wait_for(q.get(), self.IDLE_TIMEOUT)
            except asyncio.TimeoutError:
                if q.empty():
                    self._queues.pop(chat_id, None)
                    return
                continue
            try:
                await fn(*args)
            except Exception:
                log.exception("job failed in %s", chat_id)


dispatcher = Dispatcher()
