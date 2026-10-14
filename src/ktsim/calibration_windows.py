"""Read explicitly selected calibration windows; never choose a sample automatically."""

import json
from pathlib import Path


def load_calibration_windows(path):
    path = Path(path)
    if not path.exists():
        return {}
    windows = json.loads(path.read_text())
    if not isinstance(windows, dict) or set(windows) - {"sna", "tna", "tti"}:
        raise ValueError("Calibration windows must map known categories to window definitions")
    for category, window in windows.items():
        bounds = window.get("week_range") if isinstance(window, dict) else None
        if (
            not isinstance(bounds, list)
            or len(bounds) != 2
            or any(type(value) is not int for value in bounds)
            or not 1 <= bounds[0] <= bounds[1] <= 400
        ):
            raise ValueError(f"{category}: week_range must be two integer calendar weeks in 1–400")
        length = bounds[1] - bounds[0] + 1
        if length < 156 or window.get("length", length) != length:
            raise ValueError(
                f"{category}: window length must match its bounds and be at least 156 weeks"
            )
    return windows
