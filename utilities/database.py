import sqlite3
from datetime import datetime

from disnake import Member

from utilities.datatypes import Command, User, Match


class Database:
    def __init__(self, db_dir: str = "database.db"):
        self.db_dir = db_dir

        self.conn = sqlite3.connect(db_dir)
        self.cur = self.conn.cursor()

    def create_databases(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS Commands (
            name TEXT PRIMARY KEY,
            display_name TEXT,
            leader_id INTEGER,
            leader_role_id INTEGER,
            member_role_id INTEGER,
            category_id INTEGER,
            created_by_id INTEGER,
            created_at NUMERIC,
            FOREIGN KEY (leader_id) REFERENCES Users(id)
        )""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            group_number INTEGER,
            command TEXT,
            reserved BOOLEAN,
            FOREIGN KEY (command) REFERENCES Commands(name)
        )""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS Matches (
            id INTEGER PRIMARY KEY,
            first_command TEXT,
            second_command TEXT,
            panel_id INTEGER,
            notice_id INTEGER,
            created_by_id INTEGER,
            FOREIGN KEY (first_command) references Commands(name),
            FOREIGN KEY (second_command) references Commands(name)
        )""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS Config (
            name TEXT,
            value INTEGER
        )""")

        self.conn.commit()

    def check_config(self):
        self.cur.execute("SELECT * FROM config")

        if len(self.cur.fetchall()) < 4:
            # noinspection SqlWithoutWhere
            self.cur.execute("DELETE FROM config")

            self.cur.executemany(
                "INSERT INTO config(name) VALUES (?)",
                (("max_members", ), ("admin_role_id", ), ("member_role_id", ), ("tournament_channel_id", ))
            )
            self.conn.commit()

    # ===============================
    # COMMANDS UTILS
    # ===============================

    def create_command(
        self,
        name: str,
        display_name: str,
        leader_id: int,
        leader_role_id: int,
        member_role_id: int,
        category_id: int,
        created_by_id: int,
        created_at: int
    ):
        sql = """
            INSERT INTO Commands(
                name, display_name, leader_id, leader_role_id, member_role_id,
                category_id, created_by_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.cur.execute(
            sql,
            (
                name, display_name, leader_id, leader_role_id, member_role_id,
                category_id, created_by_id, created_at
            )
        )
        self.conn.commit()

    def get_command(self, command: int | str | Command, *, require_members: bool = True) -> Command | None:
        """
        :param command: leader ID or command name
        :param require_members: need to get command members from DB
        """

        if isinstance(command, Command):  # Жесть
            return command

        sql = """
            SELECT
                name, display_name, leader_id, leader_role_id, member_role_id,
                category_id, created_by_id, created_at
            FROM Commands
            WHERE 'column_name' = ?
            LIMIT 1
        """

        if isinstance(command, int):
            sql = sql.replace("'column_name'", "leader_id")
        elif isinstance(command, str):
            sql = sql.replace("'column_name'", "name")
            command = command.lower()
        else:
            return None

        self.cur.execute(sql, (command, ))

        if not (temp := self.cur.fetchone()):
            return None

        if require_members:
            members = self.get_command_members(temp[0])
        else:
            members = []

        return Command(*temp, members=members)

    def get_all_commands(self, limit: int = -1) -> list[Command]:
        sql = """
            SELECT
                name, display_name, leader_id, leader_role_id, member_role_id,
                category_id, created_by_id, created_at
            FROM Commands
            LIMIT ?
        """

        self.cur.execute(sql, (limit, ))

        if not (temp := self.cur.fetchall()):
            return []

        return [Command(*data) for data in temp]

    def command_add_member(
            self,
            command: int | str | Command,
            member_id: int,
            first_name: str,
            last_name: str,
            group_number: int,
            reserved: bool | None = None
    ) -> bool:
        command = self.get_command(command)

        if not command:
            return False

        if reserved is None:
            reserved = len(command.members) > self.get_max_members()

        if self.user_is_exists(member_id):
            sql = """
                UPDATE Users
                SET command = ?, reserved = ?
                WHERE id = ?
            """

            self.cur.execute(sql, (command.name, reserved, member_id))
            self.conn.commit()

            return True

        sql = """
            INSERT INTO Users(id, first_name, last_name, group_number, command, reserved)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        self.cur.execute(sql, (member_id, first_name, last_name, group_number, command.name, reserved))
        self.conn.commit()

        return True

    def delete_command(self, command: int | str | Command) -> bool:
        command = self.get_command(command, require_members=False)

        if not command:
            return False

        sql_clear_users_command = """
            UPDATE Users
            SET command = NULL, reserved = NULL
            WHERE command = ?
        """

        sql_delete_command = """
            DELETE FROM Commands
            WHERE leader_id = ?
        """

        self.cur.execute(sql_clear_users_command, (command.name, ))
        self.cur.execute(sql_delete_command, (command.leader_id,))
        self.conn.commit()

        return True

    # ===============================
    # USERS/MEMBERS UTILS
    # ===============================

    def create_user(
        self,
        _id: int,
        first_name: str,
        last_name: str,
        group_number: int,
        command: str,
        reserved: bool = False
    ):
        if self.user_is_exists(_id):
            sql = """
                UPDATE Users
                SET group_number = ?, command = ?, reserved = ?
                WHERE id = ?
            """

            self.cur.execute(
                sql, (group_number, command, reserved, _id)
            )

        else:
            sql = """
                INSERT INTO Users(
                    id, first_name, last_name, group_number, command, reserved
                ) VALUES (?, ?, ?, ?, ?, ?)
            """

            self.cur.execute(
                sql, (_id, first_name, last_name, group_number, command, reserved)
            )

        self.conn.commit()

    def get_command_member(self, command: str) -> User | None:
        ...  # TODO: get_command_member

    def get_command_members(self, command: int | str | Command) -> list[User]:
        command = self.get_command(command, require_members=False)

        sql = """
            SELECT id, first_name, last_name, group_number, command, reserved
            FROM Users
            WHERE command = ?
            ORDER BY reserved
        """

        self.cur.execute(sql, (command.name, ))

        if not (temp := self.cur.fetchall()):
            return []

        return [User(*data) for data in temp]

    # ===============================
    # MATCHES UTILS
    # ===============================

    def create_match(
        self,
        first_command: str | Command | None,
        second_command: str | Command | None,
        panel_id: int,
        notice_id: int,
        created_by_id: int
    ) -> int:
        """
        :return: Match ID
        """

        match_id = int(datetime.now().timestamp())

        first_command = first_command.name if isinstance(first_command, Command) else first_command
        second_command = second_command.name if isinstance(second_command, Command) else second_command

        sql = """
            INSERT INTO Matches(id, first_command, second_command, panel_id, notice_id, created_by_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        self.cur.execute(sql, (match_id, first_command, second_command, panel_id, notice_id, created_by_id))
        self.conn.commit()

        return match_id

    def get_match(self, match_id: int) -> Match | None:
        sql = """
            SELECT id, first_command, second_command, panel_id, notice_id, created_by_id
            FROM Matches
            WHERE id = ?
            LIMIT 1
        """

        self.cur.execute(sql, (match_id,))

        if not (temp := list(self.cur.fetchone())):
            return None

        temp[1] = self.get_command(temp[1])
        temp[2] = self.get_command(temp[2])

        return Match(*temp)

    # ===============================
    # CONFIG UTILS
    # ===============================

    def get_max_members(self) -> int:
        return self.cur.execute("SELECT value FROM config WHERE name = 'max_members'").fetchone()[0]

    def get_admin_role_id(self) -> int:
        return self.cur.execute("SELECT value FROM config WHERE name = 'admin_role_id'").fetchone()[0]

    def get_tournament_member_role_id(self) -> int:
        return self.cur.execute("SELECT value FROM config WHERE name = 'member_role_id'").fetchone()[0]

    def get_tournament_channel_id(self) -> int:
        return self.cur.execute("SELECT value FROM config WHERE name = 'tournament_channel_id'").fetchone()[0]

    def set_max_members(self, value: int) -> None:
        self.cur.execute("UPDATE config SET value = ? WHERE name = 'max_members'", (value, ))
        self.conn.commit()

    def set_admin_role_id(self, value: int) -> None:
        self.cur.execute("UPDATE config SET value = ? WHERE name = 'admin_role_id'", (value, ))
        self.conn.commit()

    def set_tournament_member_role_id(self, value: int) -> None:
        self.cur.execute("UPDATE config SET value = ? WHERE name = 'member_role_id'", (value, ))
        self.conn.commit()

    def set_tournament_channel_id(self, value: int) -> None:
        self.cur.execute("UPDATE config SET value = ? WHERE name = 'tournament_channel_id'", (value, ))
        self.conn.commit()

    # ===============================
    # DATABASE CHECKS
    # ===============================

    def user_is_admin(self, member: Member):
        admin_role_id = self.get_admin_role_id()

        for role in member.roles:
            if role.id == admin_role_id:
                return True

        return False

    def user_is_exists(self, user_id: int) -> bool:
        return self.cur.execute("SELECT * FROM Users WHERE id = ? LIMIT 1", (user_id,)).fetchone() is not None

    def user_is_leader(self, leader_id: int) -> bool:
        return self.cur.execute("SELECT * FROM Commands WHERE leader_id = ? LIMIT 1", (leader_id,)).fetchone() is not None

    def user_has_command(self, user_id) -> bool:
        return self.cur.execute("SELECT * FROM Users WHERE id = ? AND command IS NOT NULL LIMIT 1", (user_id,)).fetchone() is not None

    def command_is_exists(self, name: str) -> bool:
        return self.cur.execute("SELECT * FROM Commands WHERE name = ? LIMIT 1", (name, )).fetchone() is not None
