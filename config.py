from pathlib import Path

BASE_PATH = Path(__file__).parent.resolve()

# Упрощение трека
TRACK_SIMPLIFICATION_TOLERANCE_M = 10.0

# Небольшие замкнутого участки
MIN_SMALL_LOOP_LENGTH_M = 50.0
MAX_SMALL_LOOP_LENGTH_M = 1000.0

# Замкнутые участки
MIN_CLOSED_LOOP_LENGTH_M = 50.0
MAX_CLOSED_LOOP_LENGTH_M = 1_000.0
LOOP_CLOSURE_THRESHOLD_M = 25.0
