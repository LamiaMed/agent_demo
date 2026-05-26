_CLIENTS = {
    "1": {"id": "1", "name": "Alice Martin", "email": "alice@example.com", "company": "Acme Corp"},
    "2": {"id": "2", "name": "Bob Dupont", "email": "bob@example.com", "company": "Globex"},
    "3": {"id": "3", "name": "Claire Bernard", "email": "claire@example.com", "company": "Initech"},
    "4": {"id": "4", "name": "David Lefevre", "email": "david@example.com", "company": "Umbrella"},
    "5": {"id": "5", "name": "Francis Garcia", "email": "francis.garcia81000@gmail.com", "company": "Perso"},
}


def get_client_with_name(name: str) -> dict:
    """Return a fictional client by name (case-insensitive, partial match)."""
    needle = name.lower()
    for client in _CLIENTS.values():
        if needle in client["name"].lower():
            return client
    return {"error": f"Client with name '{name}' not found"}


def get_client(id: str) -> dict:
    """Return a fictional client by id."""
    if id not in _CLIENTS:
        return {"error": f"Client {id} not found"}
    return _CLIENTS[id]

def get_client_by_email(email: str) -> dict:
    """Return a fictional client by email (case-insensitive)."""
    email_needle = email.lower().strip()
    for client in _CLIENTS.values():
        if client.get("email", "").lower().strip() == email_needle:
            return client
    return {"error": f"Client with email '{email}' not found"}