# Errors — separating validation from transform lets us DLQ vs retry later.

class ValidationError(Exception):
    """Message failed schema validation. Non-retryable → DLQ"""


class ConfigError(Exception):
    """Routing config missing or malformed. Retryable in real impl (config reload)."""


class TransformError(Exception):
    """Transform failed for a specific destination. Non-retryable → DLQ."""
