"""
Common utilities for scrapers.

This module provides shared functionality to eliminate code duplication
across multiple scrapers while maintaining site-specific customizations.
"""

from .title_processing import (
    TitleProcessor,
    SearchStrategies, 
    URLValidators,
    VolumeExtractors,
    normalize_title,
    extract_volume_number
)

__all__ = [
    'TitleProcessor',
    'SearchStrategies', 
    'URLValidators',
    'VolumeExtractors',
    'normalize_title',
    'extract_volume_number'
]"""
Common utilities for scrapers.

This module provides shared functionality to eliminate code duplication
across multiple scrapers while maintaining site-specific customizations.
"""

from .title_processing import (
    TitleProcessor,
    SearchStrategies, 
    URLValidators,
    VolumeExtractors,
    normalize_title,
    extract_volume_number
)

__all__ = [
    'TitleProcessor',
    'SearchStrategies', 
    'URLValidators',
    'VolumeExtractors',
    'normalize_title',
    'extract_volume_number'
]