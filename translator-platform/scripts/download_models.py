#!/usr/bin/env python3
"""
Model Download Script

Downloads IndicTrans2 and Faster-Whisper models for the Translator Platform.
Run this script after setting up the environment to download required models.

Usage:
    python scripts/download_models.py [--models indictrans2 whisper] [--cache-dir ./models]
"""

import argparse
import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download
from huggingface_hub.utils import HfHubHTTPError

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def download_indictrans2(cache_dir: Path) -> bool:
    """Download IndicTrans2 distilled model."""
    model_path = cache_dir / "indictrans2"
    model_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading IndicTrans2 model to {model_path}...")

    try:
        # Download the distilled IndicTrans2 model
        # This is a placeholder - actual model ID would be from AI4Bharat
        snapshot_download(
            repo_id="ai4bharat/indictrans2-en-indic-dist-200M",
            local_dir=str(model_path),
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        print("IndicTrans2 model downloaded successfully!")
        return True
    except HfHubHTTPError as e:
        print(f"Failed to download IndicTrans2: {e}")
        print("Please check if the model repository exists and is accessible.")
        return False
    except Exception as e:
        print(f"Unexpected error downloading IndicTrans2: {e}")
        return False


def download_whisper(cache_dir: Path, model_size: str = "base") -> bool:
    """Download Faster-Whisper model."""
    model_path = cache_dir / "whisper" / model_size
    model_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading Whisper {model_size} model to {model_path}...")

    try:
        # Faster-Whisper models are from Systran
        snapshot_download(
            repo_id=f"Systran/faster-whisper-{model_size}",
            local_dir=str(model_path),
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        print(f"Whisper {model_size} model downloaded successfully!")
        return True
    except HfHubHTTPError as e:
        print(f"Failed to download Whisper {model_size}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error downloading Whisper: {e}")
        return False


def verify_models(cache_dir: Path) -> dict:
    """Verify downloaded models."""
    results = {}

    # Check IndicTrans2
    indictrans2_path = cache_dir / "indictrans2"
    if indictrans2_path.exists():
        # Check for essential files
        required_files = ["config.json", "tokenizer.json", "model.bin"]
        results["indictrans2"] = all(
            (indictrans2_path / f).exists() for f in required_files
        )
    else:
        results["indictrans2"] = False

    # Check Whisper
    whisper_path = cache_dir / "whisper" / "base"
    if whisper_path.exists():
        required_files = ["model.bin", "tokenizer.json", "config.json"]
        results["whisper"] = all(
            (whisper_path / f).exists() for f in required_files
        )
    else:
        results["whisper"] = False

    return results


def main():
    parser = argparse.ArgumentParser(description="Download AI models for Translator Platform")
    parser.add_argument(
        "--models",
        nargs="+",
        choices=["indictrans2", "whisper", "all"],
        default=["all"],
        help="Models to download",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(settings.MODEL_CACHE_DIR),
        help="Cache directory for models",
    )
    parser.add_argument(
        "--whisper-size",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        help="Whisper model size",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing models",
    )

    args = parser.parse_args()

    cache_dir = args.cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"Model cache directory: {cache_dir}")
    print("=" * 50)

    if args.verify_only:
        print("Verifying existing models...")
        results = verify_models(cache_dir)
        for model, status in results.items():
            print(f"  {model}: {'✓ Found' if status else '✗ Missing'}")
        return

    models_to_download = args.models
    if "all" in models_to_download:
        models_to_download = ["indictrans2", "whisper"]

    success = True

    if "indictrans2" in models_to_download:
        success &= download_indictrans2(cache_dir)

    if "whisper" in models_to_download:
        success &= download_whisper(cache_dir, args.whisper_size)

    print("=" * 50)
    if success:
        print("All models downloaded successfully!")
        print("\nVerifying models...")
        results = verify_models(cache_dir)
        for model, status in results.items():
            print(f"  {model}: {'✓ Verified' if status else '✗ Verification failed'}")
    else:
        print("Some models failed to download. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()