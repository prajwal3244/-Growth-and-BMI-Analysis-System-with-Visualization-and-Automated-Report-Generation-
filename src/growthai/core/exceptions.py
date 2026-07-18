"""Domain-specific exceptions.

Using a small exception hierarchy (instead of raising bare ``ValueError``)
lets the API layer map failures to precise HTTP responses and lets tests
assert on intent rather than message strings.
"""

from __future__ import annotations


class GrowthAIError(Exception):
    """Base class for all GrowthAI domain errors."""


class InvalidMeasurementError(GrowthAIError):
    """Raised when a measurement is physiologically impossible or malformed."""


class ReferenceDataError(GrowthAIError):
    """Raised when reference data cannot be loaded or a lookup is unsupported."""


class UnsupportedStandardError(ReferenceDataError):
    """Raised when a growth standard (WHO/CDC/IAP) is not available."""


class ModelNotTrainedError(GrowthAIError):
    """Raised when a prediction is requested before a model is trained/loaded."""
