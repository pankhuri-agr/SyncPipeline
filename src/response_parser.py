def classify_status(outcome: str, attempt: int) -> str:
    """
    Find the status based on the outcome and attempt number
    """
    MAX_ATTEMPTS = 3
    if outcome == "SUCCESS":
        return "DONE"
    if outcome == "PERMANENT":
        return "PERMANENT"
    if attempt >= MAX_ATTEMPTS:
        return "PERMANENT"
    return "RETRY"
