"""
Model Loader

Lazy loading and management of translation models with CPU optimization.
"""

import os
import logging
import asyncio
from typing import Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from ctranslate2 import Translator as CTranslate2Translator

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a loaded model."""

    name: str
    model_type: str  # "indictrans2", "whisper", etc.
    path: str
    device: str
    loaded: bool = False
    load_time: float = 0.0
    memory_usage_mb: float = 0.0


class ModelLoader:
    """
    Manages loading and caching of AI models.

    Features:
    - Lazy loading (load on first use)
    - Model warmup
    - INT8 quantization support
    - CPU thread configuration
    - Shared model instances
    - Memory monitoring
    """

    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._tokenizers: Dict[str, Any] = {}
        self._model_info: Dict[str, ModelInfo] = {}
        self._load_locks: Dict[str, asyncio.Lock] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize model loader."""
        if self._initialized:
            return

        # Configure CPU threads
        self._configure_cpu()

        # Create model cache directory
        cache_dir = Path(settings.MODEL_CACHE_DIR)
        cache_dir.mkdir(parents=True, exist_ok=True)

        self._initialized = True
        logger.info("Model loader initialized")

    def _configure_cpu(self) -> None:
        """Configure CPU settings for optimal inference."""
        # Set torch threads
        torch.set_num_threads(settings.CPU_THREADS)
        torch.set_num_interop_threads(settings.CPU_THREADS)

        # Disable torch gradient computation for inference
        torch.set_grad_enabled(False)

        logger.info(f"CPU configured: {settings.CPU_THREADS} threads")

    def _get_lock(self, model_name: str) -> asyncio.Lock:
        """Get or create load lock for model."""
        if model_name not in self._load_locks:
            self._load_locks[model_name] = asyncio.Lock()
        return self._load_locks[model_name]

    async def load_translation_models(self) -> None:
        """Load IndicTrans2 translation models."""
        await self._load_indictrans2()

    async def _load_indictrans2(self) -> None:
        """Load IndicTrans2 distilled model using CTranslate2 for CPU optimization."""
        model_name = "indictrans2"
        model_path = Path(settings.INDIC_TRANS2_MODEL_PATH)

        if not model_path.exists():
            logger.warning(f"IndicTrans2 model not found at {model_path}, using fallback")
            self._model_info[model_name] = ModelInfo(
                name=model_name,
                model_type="indictrans2",
                path=str(model_path),
                device=settings.MODEL_DEVICE,
                loaded=False,
            )
            return

        lock = self._get_lock(model_name)
        async with lock:
            if model_name in self._models:
                return

            try:
                logger.info(f"Loading IndicTrans2 model from {model_path}")

                # Load with CTranslate2 for optimized CPU inference
                translator = CTranslate2Translator(
                    str(model_path),
                    device=settings.MODEL_DEVICE,
                    compute_type="int8" if settings.ENABLE_INT8_QUANTIZATION else "float32",
                    inter_threads=settings.CPU_THREADS,
                    intra_threads=1,
                )

                # Load tokenizer
                from transformers import AutoTokenizer
                tokenizer = AutoTokenizer.from_pretrained(
                    str(model_path / "tokenizer"),
                    trust_remote_code=True,
                )

                self._models[model_name] = translator
                self._tokenizers[model_name] = tokenizer
                self._model_info[model_name] = ModelInfo(
                    name=model_name,
                    model_type="indictrans2",
                    path=str(model_path),
                    device=settings.MODEL_DEVICE,
                    loaded=True,
                    load_time=0.0,  # Would track actual load time
                )

                logger.info("IndicTrans2 model loaded successfully")

            except Exception as e:
                logger.error(f"Failed to load IndicTrans2 model: {e}")
                self._model_info[model_name] = ModelInfo(
                    name=model_name,
                    model_type="indictrans2",
                    path=str(model_path),
                    device=settings.MODEL_DEVICE,
                    loaded=False,
                )
                raise

    async def load_whisper_model(self) -> None:
        """Load Faster-Whisper model for speech recognition."""
        model_name = "whisper"
        model_path = Path(settings.WHISPER_MODEL_PATH)

        if not model_path.exists():
            logger.warning(f"Whisper model not found at {model_path}")
            return

        lock = self._get_lock(model_name)
        async with lock:
            if model_name in self._models:
                return

            try:
                from faster_whisper import WhisperModel

                logger.info(f"Loading Whisper model from {model_path}")

                model = WhisperModel(
                    str(model_path),
                    device=settings.MODEL_DEVICE,
                    compute_type="int8" if settings.ENABLE_INT8_QUANTIZATION else "float32",
                    cpu_threads=settings.CPU_THREADS,
                )

                self._models[model_name] = model
                self._model_info[model_name] = ModelInfo(
                    name=model_name,
                    model_type="whisper",
                    path=str(model_path),
                    device=settings.MODEL_DEVICE,
                    loaded=True,
                )

                logger.info("Whisper model loaded successfully")

            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                self._model_info[model_name] = ModelInfo(
                    name=model_name,
                    model_type="whisper",
                    path=str(model_path),
                    device=settings.MODEL_DEVICE,
                    loaded=False,
                )

    def get_model(self, model_name: str) -> Optional[Any]:
        """Get loaded model by name."""
        return self._models.get(model_name)

    def get_tokenizer(self, model_name: str) -> Optional[Any]:
        """Get loaded tokenizer by name."""
        return self._tokenizers.get(model_name)

    def is_model_loaded(self, model_name: str) -> bool:
        """Check if model is loaded."""
        info = self._model_info.get(model_name)
        return info.loaded if info else False

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get model information."""
        return self._model_info.get(model_name)

    def list_models(self) -> Dict[str, ModelInfo]:
        """List all models and their status."""
        return self._model_info.copy()

    async def unload_model(self, model_name: str) -> bool:
        """
        Unload a model to free memory.

        Args:
            model_name: Model to unload

        Returns:
            True if unloaded
        """
        if model_name in self._models:
            del self._models[model_name]
        if model_name in self._tokenizers:
            del self._tokenizers[model_name]
        if model_name in self._model_info:
            self._model_info[model_name].loaded = False

        # Force garbage collection
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info(f"Unloaded model: {model_name}")
        return True

    async def warmup_model(self, model_name: str, sample_input: str = "Hello world") -> float:
        """
        Warm up a model with a sample inference.

        Args:
            model_name: Model to warm up
            sample_input: Sample input text

        Returns:
            Warmup time in milliseconds
        """
        model = self.get_model(model_name)
        if not model:
            raise ValueError(f"Model {model_name} not loaded")

        import time
        start = time.time()

        # Run a dummy inference
        if model_name == "indictrans2":
            tokenizer = self.get_tokenizer(model_name)
            if tokenizer:
                inputs = tokenizer(sample_input, return_tensors="pt")
                _ = model.generate(**inputs)

        warmup_time = (time.time() - start) * 1000
        logger.info(f"Model {model_name} warmed up in {warmup_time:.2f}ms")
        return warmup_time


# Global model loader instance
_model_loader: Optional[ModelLoader] = None


async def get_model_loader() -> ModelLoader:
    """Get or create global model loader instance."""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
        await _model_loader.initialize()
    return _model_loader