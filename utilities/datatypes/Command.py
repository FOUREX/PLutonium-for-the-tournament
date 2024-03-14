from . import User


class Command:
    def __init__(
        self,
        name: str,
        display_name: str,
        leader_id: int,
        leader_role_id: int,
        member_role_id: int,
        category_id: int,
        created_by_id: int,
        created_at: int,
        *,
        members: list[User] | None = None
    ):
        self.name = name
        self.display_name = display_name
        self.leader_id = leader_id
        self.leader_role_id = leader_role_id
        self.member_role_id = member_role_id
        self.category_id = category_id
        self.created_by_id = created_by_id
        self.created_at = created_at
        self.members: list[User] = [] if not members else members
