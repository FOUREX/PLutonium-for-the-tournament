import disnake
import sqlite3

from json import dumps, loads
from datetime import datetime
from disnake.ext import commands

from config import config


ADMIN_ROLE_ID = config["ADMIN_ROLE_ID"]
MEMBER_ROLE_ID = config["MEMBER_ROLE_ID"]

intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

conn = sqlite3.connect("database.db")
cur = conn.cursor()


def create_database():
    sql = """CREATE TABLE IF NOT EXISTS commands(
        name TEXT,
        display_name TEXT,
        leader_id INTEGER,
        member_1_id INTEGER,
        member_2_id INTEGER,
        member_3_id INTEGER,
        member_4_id INTEGER,
        member_5_id INTEGER,
        members_info TEXT,
        category_id INTEGER,
        leader_role_id INTEGER,
        member_role_id INTEGER,
        created_by_user_id INTEGER,
        created_at TEXT
    )"""

    cur.execute(sql)
    conn.commit()


@bot.event
async def on_ready():
    create_database()

    print("Готов")


@bot.slash_command(description="Створює команду")
async def create_command(inter: disnake.ApplicationCommandInteraction, command_name: str, leader: disnake.Member,
                         leader_first_name: str, leader_last_name: str, leader_group: int):
    await inter.response.defer()

    command_name = command_name[:24]

    admin_role = inter.guild.get_role(ADMIN_ROLE_ID)
    if admin_role not in inter.user.roles:
        embed = disnake.Embed(title=f"Тільки організатор може створювати команди", color=disnake.Color.red())
        await inter.followup.send(embed=embed)

        return

    cur.execute("SELECT * FROM commands WHERE name = ?", (command_name.lower(),))
    if cur.fetchone() is not None:
        embed = disnake.Embed(title=f"Команда з цим іменем вже існує", color=disnake.Color.yellow())
        await inter.followup.send(embed=embed)

        return

    cur.execute("SELECT * FROM commands WHERE leader_id = ?", (leader.id,))
    if cur.fetchone() is not None:
        embed = disnake.Embed(title=f"{leader.name} вже є лідером команди", color=disnake.Color.yellow())
        await inter.followup.send(embed=embed)

        return

    # -------------------------

    member_role = inter.guild.get_role(MEMBER_ROLE_ID)

    command_leader_role = await inter.guild.create_role(name=command_name + " leader", colour=disnake.Colour.green(),
                                                        reason="Створена команда")
    command_member_role = await inter.guild.create_role(name=command_name, hoist=True,
                                                        colour=disnake.Colour.dark_green(), reason="Створена команда")

    await leader.add_roles(command_leader_role, command_member_role, member_role)

    # -------------------------

    overwrites = {
        inter.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
        command_member_role: disnake.PermissionOverwrite(view_channel=True)
    }

    categories_count = len(inter.guild.categories)

    command_category = await inter.guild.create_category(command_name, overwrites=overwrites,
                                                         position=categories_count+1, reason="Створена команда")

    # -------------------------

    await inter.guild.create_text_channel("Чач", category=command_category,
                                          reason="Створена команда")
    await inter.guild.create_voice_channel("Гс", category=command_category,
                                           reason="Створена команда")

    # -------------------------

    members_info = {
        leader.id: {
            "first_name": leader_first_name,
            "last_name": leader_last_name,
            "group": leader_group
        }
    }

    members_info = dumps(members_info, ensure_ascii=False)

    # -------------------------

    sql = ("INSERT INTO commands(name, display_name, leader_id, member_1_id, members_info, category_id, "
           "leader_role_id, member_role_id, created_by_user_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")

    cur.execute(sql, (
        command_name.lower(), command_name, leader.id, leader.id, members_info, command_category.id,
        command_leader_role.id, command_member_role.id, inter.user.id, datetime.now()
    ))
    conn.commit()

    embed = disnake.Embed(title=f"Створена команда {command_name.upper()}", description=f"Лідер: {leader.mention}",
                          color=disnake.Color.green())

    await inter.followup.send(embed=embed)


@bot.slash_command(description="Додає учасника в команду")
async def command_add_member(inter: disnake.ApplicationCommandInteraction, leader: disnake.Member,
                             member: disnake.Member, first_name: str, last_name: str, group: int):
    await inter.response.defer()

    admin_role = inter.guild.get_role(ADMIN_ROLE_ID)
    if admin_role not in inter.user.roles:
        embed = disnake.Embed(title=f"Тільки організатор може додавати учасників до команди", color=disnake.Color.red())
        await inter.followup.send(embed=embed)

        return

    cur.execute("SELECT name, member_2_id, member_3_id, member_4_id, member_5_id, members_info, member_role_id "
                "FROM commands WHERE leader_id = ?",
                (leader.id,))

    if (temp := cur.fetchone()) is None:
        embed = disnake.Embed(title=f"{leader.name} не є лідером команди", color=disnake.Color.yellow())
        await inter.followup.send(embed=embed)

        return

    if None not in temp:
        embed = disnake.Embed(title=f"Команда має максимальну кількість учасників", color=disnake.Color.yellow())
        await inter.followup.send(embed=embed)

        return

    cur.execute("SELECT * FROM commands WHERE leader_id = ?", (member.id, ))
    if cur.fetchone() is not None:
        embed = disnake.Embed(title=f"{member.name} лідер іншої команди", color=disnake.Color.yellow())
        await inter.followup.send(embed=embed)

        return

    if member.id in temp:
        embed = disnake.Embed(title=f"{member.name} вже є учасником команди", color=disnake.Color.yellow())
        await inter.followup.send(embed=embed)

        return

    cur.execute("SELECT * FROM commands WHERE member_2_id = ? OR member_3_id = ? OR member_4_id = ? OR member_5_id = ?",
                (member.id, member.id, member.id, member.id))

    if cur.fetchone() is not None:
        embed = disnake.Embed(title=f"{member.name} учасник іншої команди", color=disnake.Color.yellow())
        await inter.followup.send(embed=embed)

        return

    command_name, *members_ids, members_info, member_role_id = temp
    members_info = loads(members_info)
    role = inter.guild.get_role(member_role_id)
    member_role = inter.guild.get_role(MEMBER_ROLE_ID)
    member_index = 2

    members_info[member.id] = {
        "first_name": first_name,
        "last_name": last_name,
        "group": group
    }

    members_info = dumps(members_info, ensure_ascii=False)

    for i in members_ids:
        if i is not None:
            member_index += 1
        else:
            break

    await member.add_roles(role, member_role)

    cur.execute(f"UPDATE commands SET member_{member_index}_id = ?, members_info = ? WHERE leader_id = ?", # noqa
                (member.id, members_info, leader.id))
    conn.commit()

    embed = disnake.Embed(title=f"{member.name} тепер учасник команди {command_name.upper()}",
                          color=disnake.Color.green())

    await inter.followup.send(embed=embed)


@bot.slash_command(description="Видаляє команду за її назвою")
async def delete_command_by_name(inter: disnake.ApplicationCommandInteraction, command_name: str):
    await inter.response.defer()

    cur.execute("SELECT category_id, leader_role_id, member_role_id FROM commands WHERE name = ?",
                (command_name.lower(), ))

    if (temp := cur.fetchone()) is None:
        embed = disnake.Embed(title=f"Команди з цим іменем не існує", color=disnake.Color.yellow())
        await inter.followup.send(embed=embed)

        return

    command_category_id, leader_role_id, member_role_id, *_ = temp

    command_category = inter.guild.get_channel(command_category_id)
    leader_role = inter.guild.get_role(leader_role_id)
    member_role = inter.guild.get_role(member_role_id)

    for channel in command_category.channels:
        await channel.delete(reason="Команда видалена")

    await command_category.delete(reason="Команда видалена")
    await leader_role.delete(reason="Команда видалена")
    await member_role.delete(reason="Команда видалена")

    cur.execute("DELETE FROM commands WHERE name = ?", (command_name.lower(), ))
    conn.commit()

    embed = disnake.Embed(title=f"Видалена команда {command_name.upper()}", color=disnake.Color.green())

    await inter.followup.send(embed=embed)


@bot.slash_command(description="Видаляє команду")
async def delete_command(inter: disnake.ApplicationCommandInteraction, leader: disnake.Member):
    await inter.response.defer()

    cur.execute("SELECT name, category_id, leader_role_id, member_role_id FROM commands WHERE leader_id = ?",
                (leader.id,))

    if (temp := cur.fetchone()) is None:
        embed = disnake.Embed(title=f"{leader.name} не є лідером команди", color=disnake.Color.yellow())
        await inter.followup.send(embed=embed)

        return

    command_name, command_category_id, leader_role_id, member_role_id, *_ = temp

    command_category = inter.guild.get_channel(command_category_id)
    leader_role = inter.guild.get_role(leader_role_id)
    member_role = inter.guild.get_role(member_role_id)

    for channel in command_category.channels:
        await channel.delete(reason="Команда видалена")

    await command_category.delete(reason="Команда видалена")
    await leader_role.delete(reason="Команда видалена")
    await member_role.delete(reason="Команда видалена")

    cur.execute("DELETE FROM commands WHERE name = ?", (command_name.lower(), ))
    conn.commit()

    embed = disnake.Embed(title=f"Видалена команда {command_name.upper()}", color=disnake.Color.green())

    await inter.followup.send(embed=embed)


@bot.slash_command(description="Інформація про команду")
async def command_info(inter: disnake.ApplicationCommandInteraction, leader: disnake.Member):
    await inter.response.defer()

    cur.execute("SELECT display_name, leader_id, member_1_id, member_2_id, member_3_id, member_4_id, member_5_id, "
                "members_info, created_by_user_id, created_at FROM commands WHERE leader_id = ?", (leader.id, ))

    if (temp := cur.fetchone()) is None:
        embed = disnake.Embed(title=f"{leader.name} не є лідером команди", color=disnake.Color.yellow())
        await inter.followup.send(embed=embed)

        return

    (display_name, leader_id, member_1_id, member_2_id, member_3_id, member_4_id, member_5_id, members_info,
     created_by_user_id, created_at, *_) = temp

    member_1: disnake.Member = inter.guild.get_member(member_1_id)
    member_2: disnake.Member = inter.guild.get_member(member_2_id)
    member_3: disnake.Member = inter.guild.get_member(member_3_id)
    member_4: disnake.Member = inter.guild.get_member(member_4_id)
    member_5: disnake.Member = inter.guild.get_member(member_5_id)
    members = [member_1, member_2, member_3, member_4, member_5]
    leader = member_1

    members_info = loads(members_info)
    created_by_user: disnake.Member = inter.guild.get_member(created_by_user_id)
    created_at = datetime.fromisoformat(created_at)

    _members = ""
    for i, member in enumerate(members):
        if member is None:
            break

        _members += f"{i}. {member.mention}\n"

    embed = disnake.Embed(
        title=f"Команда {display_name.upper()}",
        description=f"Лідер: {leader.mention}",
        color=disnake.Color.green()
    )
    embed.add_field("Учасники", _members, inline=False)
    embed.set_footer(text=created_by_user.display_name, icon_url=created_by_user.avatar.url)
    embed.timestamp = created_at

    await inter.followup.send(embed=embed)


@bot.slash_command(description="Список команд")
async def commands_list(inter: disnake.ApplicationCommandInteraction):
    await inter.response.defer()

    cur.execute("SELECT display_name, leader_id FROM commands")

    temp = cur.fetchmany(25)

    embed = disnake.Embed(title=f"Список команд",
                          description=f"Кількість команд: {len(temp)}",
                          color=disnake.Color.green())

    for (display_name, leader_id) in temp:
        leader = inter.guild.get_member(leader_id)

        embed.add_field(name=f"**{display_name}**", value=f"Лідер: {leader.mention}", inline=False)

    await inter.followup.send(embed=embed)


bot.run(token=config["token"])
