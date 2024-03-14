from .DatabaseResponseType import DatabaseResponseType


class DatabaseResponse:
    def __init__(self, ok: bool = True, _type: DatabaseResponseType = DatabaseResponseType.NONE, message: str = ""):
        self.ok = ok
        self.type = _type
        self.message = message
