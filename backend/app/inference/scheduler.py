"""
Inference Scheduler

Bounded inference queue with concurrent request handling and deduplication.
"""

import asyncio
import logging
import time
import hashlib
import json
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from uuid import uuid4
from collections import OrderedDict
from contextlib import asynccontextmanager

from app.core.config import settings
from app.inference.model_loader import get_model_loader

logger = logging.getLogger(__name__)


@dataclass
class InferenceRequest:
    """Inference request data."""

    id: str
    model_name: str
    input_data: Dict[str, Any]
    future: asyncio.Future
    created_at: float = field(default_factory=time.time)
    priority: int = 0


@dataclass
class InferenceStats:
    """Inference scheduler statistics."""

    total_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    deduplicated_requests: int = 0
    queue_overflows: int = 0
    avg_latency_ms: float = 0.0
    current_queue_size: int = 0
    active_workers: int = 0


class InferenceScheduler:
    """
    Bounded inference scheduler with queue management.

    Features:
    - Bounded request queue
    - Concurrent worker pool
    - Request deduplication
    - Priority queue support
    - Timeout handling
    - Statistics tracking
    - Graceful shutdown
    """

    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(
            maxsize=settings.INFERENCE_QUEUE_MAX_SIZE
        )
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._stats = InferenceStats()
        self._cache: OrderedDict = OrderedDict()  # LRU cache for deduplication
        self._cache_max_size = 1000
        self._model_loader = None
        self._inference_functions: Dict[str, Callable] = {}

    async def initialize(self) -> None:
        """Initialize scheduler and start workers."""
        if self._running:
            return

        self._model_loader = await get_model_loader()
        self._register_inference_functions()
        await self._start_workers()
        self._running = True
        logger.info(f"Inference scheduler started with {settings.MAX_CONCURRENT_INFERENCE} workers")

    def _register_inference_functions(self) -> None:
        """Register model-specific inference functions."""
        self._inference_functions = {
            "indictrans2": self._run_indictrans2_inference,
            "whisper": self._run_whisper_inference,
        }

    async def _start_workers(self) -> None:
        """Start worker tasks."""
        for i in range(settings.MAX_CONCURRENT_INFERENCE):
            worker = asyncio.create_task(self._worker_loop(i))
            self._workers.append(worker)

    async def _worker_loop(self, worker_id: int) -> None:
        """Main worker loop."""
        logger.debug(f"Worker {worker_id} started")
        while self._running:
            try:
                # Get request from queue with timeout
                request = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )

                self._stats.active_workers += 1
                self._stats.current_queue_size = self._queue.qsize()

                await self._process_request(request, worker_id)

                self._stats.active_workers -= 1
                self._stats.current_queue_size = self._queue.qsize()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                self._stats.active_workers -= 1

        logger.debug(f"Worker {worker_id} stopped")

    async def _process_request(self, request: InferenceRequest, worker_id: int) -> None:
        """Process a single inference request."""
        start_time = time.time()

        try:
            # Check cache for deduplication
            cache_key = self._get_cache_key(request.model_name, request.input_data)
            if cache_key in self._cache:
                # Move to end (LRU)
                result = self._cache.pop(cache_key)
                self._cache[cache_key] = result
                self._stats.deduplicated_requests += 1
                logger.debug(f"Cache hit for request {request.id}")
                request.future.set_result(result)
                return

            # Run inference
            inference_func = self._inference_functions.get(request.model_name)
            if not inference_func:
                raise ValueError(f"No inference function for model: {request.model_name}")

            result = await inference_func(request.input_data)

            # Cache result
            self._cache[cache_key] = result
            if len(self._cache) > self._cache_max_size:
                self._cache.popitem(last=False)  # Remove oldest

            request.future.set_result(result)
            self._stats.completed_requests += 1

        except Exception as e:
            logger.error(f"Inference failed for request {request.id}: {e}")
            request.future.set_exception(e)
            self._stats.failed_requests += 1

        finally:
            # Update average latency
            latency = (time.time() - start_time) * 1000
            total_completed = self._stats.completed_requests + self._stats.failed_requests
            if total_completed > 0:
                self._stats.avg_latency_ms = (
                    (self._stats.avg_latency_ms * (total_completed - 1) + latency)
                    / total_completed
                )

    def _get_cache_key(self, model_name: str, input_data: Dict[str, Any]) -> str:
        """Generate cache key for request deduplication."""
        # Create deterministic hash of input
        content = json.dumps(input_data, sort_keys=True)
        return f"{model_name}:{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    async def _run_indictrans2_inference(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run IndicTrans2 translation inference."""
        model = self._model_loader.get_model("indictrans2")
        tokenizer = self._model_loader.get_tokenizer("indictrans2")

        if not model or not tokenizer:
            # Fallback for testing
            return {"translation": f"[FALLBACK] {input_data.get('text', '')}"}

        text = input_data.get("text", "")
        source_lang = input_data.get("source_lang", "eng_Latn")
        target_lang = input_data.get("target_lang", "kan_Knda")

        # Tokenize
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

        # Generate translation
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.lang_code_to_id.get(target_lang, tokenizer.eos_token_id),
                max_length=512,
                num_beams=4,
                early_stopping=True,
            )

        # Decode
        translation = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

        return {"translation": translation}

    async def _run_whisper_inference(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Whisper speech recognition inference."""
        model = self._model_loader.get_model("whisper")

        if not model:
            return {"text": "[FALLBACK] Speech recognition not available", "language": "en"}

        audio_path = input_data.get("audio_path")
        language = input_data.get("language")

        if not audio_path:
            raise ValueError("audio_path required for Whisper inference")

        segments, info = model.transcribe(audio_path, language=language, beam_size=5)

        text = " ".join([segment.text for segment in segments])

        return {
            "text": text.strip(),
            "language": info.language,
            "language_probability": info.language_probability,
        }

    async def submit(
        self,
        model_name: str,
        input_data: Dict[str, Any],
        timeout: Optional[float] = None,
        priority: int = 0,
    ) -> Dict[str, Any]:
        """
        Submit inference request to queue.

        Args:
            model_name: Model to use
            input_data: Input data for model
            timeout: Request timeout in seconds
            priority: Request priority (higher = more urgent)

        Returns:
            Inference result

        Raises:
            asyncio.TimeoutError: If request times out
            RuntimeError: If queue is full
        """
        if not self._running:
            await self.initialize()

        self._stats.total_requests += 1

        # Create future for result
        future = asyncio.get_event_loop().create_future()

        request = InferenceRequest(
            id=str(uuid4()),
            model_name=model_name,
            input_data=input_data,
            future=future,
            priority=priority,
        )

        try:
            # Add to queue (negative priority for max-heap behavior)
            await asyncio.wait_for(
                self._queue.put((-priority, request)),
                timeout=timeout or settings.INFERENCE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            self._stats.queue_overflows += 1
            raise RuntimeError("Inference queue full, request timed out")

        # Wait for result
        try:
            result = await asyncio.wait_for(future, timeout=timeout or settings.INFERENCE_TIMEOUT)
            return result
        except asyncio.TimeoutError:
            future.cancel()
            raise

    def get_stats(self) -> InferenceStats:
        """Get scheduler statistics."""
        self._stats.current_queue_size = self._queue.qsize()
        return self._stats

    async def shutdown(self) -> None:
        """Gracefully shutdown scheduler."""
        logger.info("Shutting down inference scheduler...")
        self._running = False

        # Wait for workers to finish
        for worker in self._workers:
            worker.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        # Clear queue
        while not self._queue.empty():
            try:
                _, request = self._queue.get_nowait()
                if not request.future.done():
                    request.future.set_exception(RuntimeError("Scheduler shutting down"))
            except asyncio.QueueEmpty:
                break

        logger.info("Inference scheduler stopped")


# Global scheduler instance
_scheduler: Optional[InferenceScheduler] = None


async def get_inference_scheduler() -> InferenceScheduler:
    """Get or create global inference scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = InferenceScheduler()
        await _scheduler.initialize()
    return _scheduler