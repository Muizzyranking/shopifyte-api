def response_message(msg):
    return {"message": str(msg)}


def response_with_data(msg, data):
    return {"message": str(msg), "data": data}


def error_message(msg):
    return response_message(f"Error: {str(msg)}")
