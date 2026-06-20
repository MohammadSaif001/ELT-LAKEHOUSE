import uuid

def generate_id() -> str:
    """
    Generate a unique 32-character hex ID.
    """
    return uuid.uuid4().hex
