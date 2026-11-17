"""
CPU Optimizer

Utilities for optimizing CPU inference performance.
"""

import os
import logging
import torch
import psutil
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CPUInfo:
    """CPU information."""

    physical_cores: int
    logical_cores: int
    max_frequency_mhz: float
    current_frequency_mhz: float
    cache_size_mb: int
    architecture: str


@dataclass
class OptimizationConfig:
    """CPU optimization configuration."""

    num_threads: int
    interop_threads: int
    use_mkldnn: bool
    use_numa: bool
    affinity_mask: Optional[list] = None


def get_cpu_info() -> CPUInfo:
    """Get detailed CPU information."""
    try:
        # Physical and logical cores
        physical_cores = psutil.cpu_count(logical=False) or 1
        logical_cores = psutil.cpu_count(logical=True) or 1

        # Frequency
        freq = psutil.cpu_freq()
        max_freq = freq.max if freq else 0.0
        current_freq = freq.current if freq else 0.0

        # Architecture
        import platform
        arch = platform.machine()

        # Cache size (approximate)
        cache_size = 0
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "cache size" in line.lower():
                        parts = line.split(":")
                        if len(parts) > 1:
                            cache_str = parts[1].strip()
                            if "KB" in cache_str:
                                cache_size = int(cache_str.replace("KB", "").strip())
                            elif "MB" in cache_str:
                                cache_size = int(float(cache_str.replace("MB", "").strip()) * 1024)
                            break
        except Exception:
            pass

        return CPUInfo(
            physical_cores=physical_cores,
            logical_cores=logical_cores,
            max_frequency_mhz=max_freq,
            current_frequency_mhz=current_freq,
            cache_size_mb=cache_size // 1024,
            architecture=arch,
        )
    except Exception as e:
        logger.warning(f"Could not get CPU info: {e}")
        return CPUInfo(
            physical_cores=4,
            logical_cores=8,
            max_frequency_mhz=3000.0,
            current_frequency_mhz=2500.0,
            cache_size_mb=8,
            architecture="unknown",
        )


def get_optimal_config(cpu_info: Optional[CPUInfo] = None) -> OptimizationConfig:
    """
    Get optimal CPU configuration for inference.

    Args:
        cpu_info: Optional CPU info (auto-detected if not provided)

    Returns:
        OptimizationConfig with recommended settings
    """
    if cpu_info is None:
        cpu_info = get_cpu_info()

    # Use configured threads or auto-detect
    num_threads = settings.CPU_THREADS or min(cpu_info.physical_cores, 8)
    interop_threads = min(num_threads, 4)

    # MKL-DNN (oneDNN) optimization for Intel CPUs
    use_mkldnn = "intel" in cpu_info.architecture.lower() or "x86" in cpu_info.architecture.lower()

    # NUMA awareness for multi-socket systems
    use_numa = cpu_info.physical_cores > 16

    return OptimizationConfig(
        num_threads=num_threads,
        interop_threads=interop_threads,
        use_mkldnn=use_mkldnn,
        use_numa=use_numa,
    )


def apply_optimization_config(config: OptimizationConfig) -> None:
    """
    Apply CPU optimization configuration.

    Args:
        config: Optimization configuration to apply
    """
    # Set PyTorch threads
    torch.set_num_threads(config.num_threads)
    torch.set_num_interop_threads(config.interop_threads)

    # Enable MKL-DNN if available
    if config.use_mkldnn:
        try:
            torch.backends.mkldnn.enabled = True
            logger.info("MKL-DNN enabled")
        except Exception as e:
            logger.warning(f"Could not enable MKL-DNN: {e}")

    # Set environment variables for other libraries
    os.environ["OMP_NUM_THREADS"] = str(config.num_threads)
    os.environ["MKL_NUM_THREADS"] = str(config.num_threads)
    os.environ["NUMEXPR_NUM_THREADS"] = str(config.num_threads)

    if config.use_numa:
        os.environ["OMP_PROC_BIND"] = "true"
        os.environ["OMP_PLACES"] = "cores"

    logger.info(
        f"CPU optimization applied: threads={config.num_threads}, "
        f"interop={config.interop_threads}, mkldnn={config.use_mkldnn}, numa={config.use_numa}"
    )


def optimize_for_inference() -> OptimizationConfig:
    """
    Apply all CPU optimizations for inference workloads.

    Returns:
        Applied optimization configuration
    """
    cpu_info = get_cpu_info()
    config = get_optimal_config(cpu_info)
    apply_optimization_config(config)
    return config


def get_memory_info() -> Dict[str, Any]:
    """Get system memory information."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "percent_used": mem.percent,
        "swap_total_gb": round(swap.total / (1024**3), 2),
        "swap_used_gb": round(swap.used / (1024**3), 2),
    }


def check_system_requirements() -> Dict[str, Any]:
    """
    Check if system meets minimum requirements.

    Returns:
        Dictionary with check results
    """
    cpu_info = get_cpu_info()
    mem_info = get_memory_info()

    checks = {
        "cpu_cores": {
            "required": 4,
            "available": cpu_info.physical_cores,
            "pass": cpu_info.physical_cores >= 4,
        },
        "memory_gb": {
            "required": 8,
            "available": mem_info["total_gb"],
            "pass": mem_info["total_gb"] >= 8,
        },
        "available_memory_gb": {
            "required": 4,
            "available": mem_info["available_gb"],
            "pass": mem_info["available_gb"] >= 4,
        },
    }

    all_pass = all(check["pass"] for check in checks.values())

    return {
        "meets_requirements": all_pass,
        "checks": checks,
        "cpu_info": {
            "physical_cores": cpu_info.physical_cores,
            "logical_cores": cpu_info.logical_cores,
            "architecture": cpu_info.architecture,
        },
        "memory_info": mem_info,
    }


def print_system_info() -> None:
    """Print system information for debugging."""
    cpu_info = get_cpu_info()
    mem_info = get_memory_info()
    req = check_system_requirements()

    print("\n" + "=" * 50)
    print("SYSTEM INFORMATION")
    print("=" * 50)
    print(f"CPU: {cpu_info.architecture}")
    print(f"  Physical cores: {cpu_info.physical_cores}")
    print(f"  Logical cores: {cpu_info.logical_cores}")
    print(f"  Max frequency: {cpu_info.max_frequency_mhz:.0f} MHz")
    print(f"  Cache: {cpu_info.cache_size_mb} MB")
    print(f"Memory:")
    print(f"  Total: {mem_info['total_gb']:.1f} GB")
    print(f"  Available: {mem_info['available_gb']:.1f} GB")
    print(f"  Used: {mem_info['used_gb']:.1f} GB ({mem_info['percent_used']:.1f}%)")
    print(f"Requirements check: {'PASS' if req['meets_requirements'] else 'FAIL'}")
    for check_name, check in req["checks"].items():
        status = "✓" if check["pass"] else "✗"
        print(f"  {status} {check_name}: {check['available']} (required: {check['required']})")
    print("=" * 50 + "\n")