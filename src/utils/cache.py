"""Cache management utilities."""
from pathlib import Path
from datetime import datetime, timedelta
import json


CACHE_DIR = Path("data_files/cache")


def clear_old_cache(max_age_hours: int = 24) -> int:
    """
    Remove cache files older than specified hours.
    
    Args:
        max_age_hours: Maximum age of cache files to keep in hours
        
    Returns:
        Number of files removed
    """
    if not CACHE_DIR.exists():
        return 0
    
    removed = 0
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    
    for cache_file in CACHE_DIR.glob("*.json"):
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if mtime < cutoff:
            cache_file.unlink()
            removed += 1
    
    return removed


def get_cache_size_mb() -> float:
    """
    Get total cache size in megabytes.
    
    Returns:
        Total size in MB
    """
    if not CACHE_DIR.exists():
        return 0.0
    
    total_bytes = sum(f.stat().st_size for f in CACHE_DIR.glob("*.json"))
    return round(total_bytes / (1024 * 1024), 2)


def clear_all_cache() -> int:
    """
    Remove all cache files.
    
    Returns:
        Number of files removed
    """
    if not CACHE_DIR.exists():
        return 0
    
    removed = 0
    for cache_file in CACHE_DIR.glob("*.json"):
        cache_file.unlink()
        removed += 1
    
    return removed
