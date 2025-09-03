def response_message(msg):
    return {"message": str(msg)}


def response_with_data(msg, data):
    return {"message": str(msg), "data": data}


def error_message(msg):
    return response_message(f"Error: {str(msg)}")


def get_seconds(hours: float = 0, minutes: float = 0, seconds: float = 0) -> int:
    return int((hours * 3600) + (minutes * 60) + seconds)
