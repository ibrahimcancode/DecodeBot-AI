import time


def get_session_duration(session) -> str:
    if session.start_time is None:
        return "0s"
    elapsed = time.monotonic() - session.start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"
