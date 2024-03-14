from . import Command


class Match:
    def __init__(
        self,
        _id: int,
        first_command: Command | None,
        second_command: Command | None,
        panel_id: int,
        notice_id: int,
        created_by_id: int
    ):
        self.id = _id
        self.first_command = first_command
        self.second_command = second_command
        self.panel_id = panel_id
        self.notice_id = notice_id
        self.created_by_id = created_by_id
