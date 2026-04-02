from datetime import datetime


def get_time():
    return {
        "tool": "get_time",
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
