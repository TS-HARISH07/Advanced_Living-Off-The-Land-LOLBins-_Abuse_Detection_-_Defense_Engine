import time
from collections import defaultdict

# process_name -> list of timestamps
_memory = defaultdict(list)

# Time window in seconds (memory duration)
MEMORY_WINDOW = 120  # 2 minutes

def update_memory(process_name):
    now = time.time()

    # Clean old entries
    _memory[process_name] = [
        t for t in _memory[process_name]
        if now - t <= MEMORY_WINDOW
    ]

    # Add new occurrence
    _memory[process_name].append(now)

    return len(_memory[process_name])

def memory_risk_boost(count):
    """
    Increase risk based on repetition
    """
    if count >= 3:
        return 30
    elif count == 2:
        return 15
    return 0
