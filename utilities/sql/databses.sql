CREATE TABLE IF NOT EXISTS Commands (
    name TEXT PRIMARY KEY,
    display_name TEXT,
    leader_id INTEGER,
    leader_role_id INTEGER,
    member_role_id INTEGER,
    category_id INTEGER,
    created_by_id INTEGER,
    created_at NUMERIC,
    FOREIGN KEY (leader_id) REFERENCES Users(id)
);

CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    group_number INTEGER,
    command TEXT,
    reserved BOOLEAN,
    FOREIGN KEY (command) REFERENCES Commands(name)
);

CREATE TABLE IF NOT EXISTS Config (
    max_members INTEGER,
    admin_role_id INTEGER,
    member_role_id INTEGER,
    tournament_channel_id INTEGER
);

CREATE TABLE IF NOT EXISTS Matches (
    id INTEGER PRIMARY KEY,
    first_command TEXT,
    second_command TEXT,
    panel_id INTEGER,
    notice_id INTEGER,
    created_by_id INTEGER,
    FOREIGN KEY (first_command) references Commands(name),
    FOREIGN KEY (second_command) references Commands(name)
);
