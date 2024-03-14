class User:
    def __init__(self,
                 id: int,
                 first_name: str,
                 last_name: str,
                 group_number: int,
                 command: str,
                 reserved: bool):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.group_number = group_number
        self.command = command
        self.reserved = reserved
