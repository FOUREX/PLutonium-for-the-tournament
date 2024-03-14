from datetime import datetime

import disnake
from disnake.ext import commands

from utilities.database import Database


class Commands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: Database = self.bot.database

    @commands.slash_command(description="Створює команду")
    async def create_command(self, inter: disnake.ApplicationCommandInteraction, command_name: str,
                             leader: disnake.Member, leader_first_name: str, leader_last_name: str, leader_group: int):
        await inter.response.defer()

        # Checks

        if not self.db.user_is_admin(inter.user):
            await inter.followup.send(
                embed=disnake.Embed(title="Тільки організатор може створювати команди", color=disnake.Color.red())
            )
            return

        if self.db.command_is_exists(command_name.lower()):
            await inter.followup.send(
                embed=disnake.Embed(title="Команда з цим іменем вже існує", color=disnake.Color.yellow())
            )
            return

        if self.db.user_has_command(leader.id):
            await inter.followup.send(
                embed=disnake.Embed(title=f"{leader.name} учасник іншої команди", color=disnake.Color.yellow())
            )
            return

        # Creating and assigning roles

        tournament_member_role = inter.guild.get_role(self.db.get_tournament_member_role_id())

        leader_role = await inter.guild.create_role(
            name=command_name + " leader",
            colour=disnake.Colour.green(),
            reason="Створена команда"
        )

        member_role = await inter.guild.create_role(
            name=command_name, hoist=True,
            colour=disnake.Colour.dark_green(),
            reason="Створена команда"
        )

        await leader.add_roles(leader_role, member_role, tournament_member_role)

        # Creating command category and channels

        overwrites = {
            inter.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
            member_role: disnake.PermissionOverwrite(view_channel=True)
        }

        categories_count = len(inter.guild.categories)

        command_category = await inter.guild.create_category(command_name, overwrites=overwrites,
                                                             position=categories_count + 1, reason="Створена команда")

        await inter.guild.create_text_channel("Чач", category=command_category,
                                              reason="Створена команда")
        await inter.guild.create_voice_channel("Гс", category=command_category,
                                               reason="Створена команда")

        # Creating database entries

        self.db.create_user(
            leader.id, leader_first_name, leader_last_name, leader_group,
            command_name.lower(), False
        )

        self.db.create_command(
            command_name.lower(), command_name, leader.id, leader_role.id, member_role.id,
            command_category.id, inter.user.id, int(datetime.now().timestamp())
        )

        # Send success message

        embed = disnake.Embed(
            title=f"Створена команда {command_name.upper()}", description=f"Лідер: {leader.mention}",
            color=disnake.Color.green()
        )

        await inter.followup.send(embed=embed)

    @commands.slash_command(description="Додає учасника в команду")
    async def command_add_member(self, inter: disnake.ApplicationCommandInteraction, leader: disnake.Member,
                                 member: disnake.Member, first_name: str, last_name: str,
                                 group: int, reserved: bool = None):
        await inter.response.defer()

        # Checks

        if not self.db.user_is_admin(inter.user):
            await inter.followup.send(
                embed=disnake.Embed(title="Тільки організатор може додавати учасників до команди", color=disnake.Color.red())
            )
            return

        if not self.db.get_command(leader.id):
            await inter.followup.send(
                embed=disnake.Embed(title=f"{leader.name} не є лідером команди", color=disnake.Color.yellow())
            )
            return

        if self.db.user_has_command(member.id):
            await inter.followup.send(
                embed=disnake.Embed(title=f"{member.name} вже є учасником команди", color=disnake.Color.yellow())
            )
            return

        command = self.db.get_command(leader.id, require_members=False)

        command_member_role = inter.guild.get_role(command.member_role_id)
        tournament_member_role = inter.guild.get_role(self.db.get_tournament_member_role_id())

        await member.add_roles(command_member_role, tournament_member_role)

        self.db.command_add_member(
            command, member.id, first_name, last_name, group, reserved
        )

        embed = disnake.Embed(title=f"{member.name} тепер учасник команди",
                              color=disnake.Color.green())

        await inter.followup.send(embed=embed)

    @commands.slash_command(description="Видаляє команду")  # TODO: Clear user command in DB Users
    async def delete_command(self, inter: disnake.ApplicationCommandInteraction, leader: disnake.Member):
        await inter.response.defer()

        # Checks

        if not self.db.user_is_admin(inter.user):
            await inter.followup.send(
                embed=disnake.Embed(title="Тільки організатор може видаляти команди", color=disnake.Color.red())
            )
            return

        if not (command := self.db.get_command(leader.id)):
            await inter.followup.send(
                embed=disnake.Embed(title=f"{leader.name} не є лідером команди", color=disnake.Color.yellow())
            )
            return

        # Deleting roles and channels

        command_category = inter.guild.get_channel(command.category_id)
        command_leader_role = inter.guild.get_role(command.leader_role_id)
        command_member_role = inter.guild.get_role(command.member_role_id)
        tournament_member_role = inter.guild.get_role(self.db.get_tournament_member_role_id())

        for command_member in command.members:
            member = inter.guild.get_member(command_member.id)

            if not member:
                continue

            await member.remove_roles(tournament_member_role, reason=f"Команда видалена {inter.user.name}")

        for channel in command_category.channels:
            await channel.delete(reason=f"Команда видалена {inter.user.name}")

        await command_category.delete(reason=f"Команда видалена {inter.user.name}")
        await command_leader_role.delete(reason=f"Команда видалена {inter.user.name}")
        await command_member_role.delete(reason=f"Команда видалена {inter.user.name}")

        # Deleting database entries

        self.db.delete_command(command)

        # Send success message

        embed = disnake.Embed(title=f"Видалена команда {command.display_name}", color=disnake.Color.green())

        await inter.followup.send(embed=embed)

    @commands.slash_command(description="Видаляє команду за її назвою")
    async def delete_command_by_name(self, inter: disnake.ApplicationCommandInteraction, command_name: str):
        await inter.response.defer()

        # Checks

        if not self.db.user_is_admin(inter.user):
            await inter.followup.send(
                embed=disnake.Embed(title="Тільки організатор може видаляти команди", color=disnake.Color.red())
            )
            return

        if not (command := self.db.get_command(command_name)):
            await inter.followup.send(
                embed=disnake.Embed(title=f"Команди {command_name} не існує", color=disnake.Color.yellow())
            )
            return

        # Deleting roles and channels

        command_category = inter.guild.get_channel(command.category_id)
        command_leader_role = inter.guild.get_role(command.leader_role_id)
        command_member_role = inter.guild.get_role(command.member_role_id)
        tournament_member_role = inter.guild.get_role(self.db.get_tournament_member_role_id())

        for command_member in command.members:
            member = inter.guild.get_member(command_member.id)

            if not member:
                continue

            await member.remove_roles(tournament_member_role, reason=f"Команда видалена {inter.user.name}")

        for channel in command_category.channels:
            await channel.delete(reason=f"Команда видалена {inter.user.name}")

        await command_category.delete(reason=f"Команда видалена {inter.user.name}")
        await command_leader_role.delete(reason=f"Команда видалена {inter.user.name}")
        await command_member_role.delete(reason=f"Команда видалена {inter.user.name}")

        # Deleting database entries

        self.db.delete_command(command)

        # Send success message

        embed = disnake.Embed(title=f"Видалена команда {command.display_name}", color=disnake.Color.green())

        await inter.followup.send(embed=embed)

    @commands.slash_command(description="Інформація про команду")
    async def command_info(self, inter: disnake.ApplicationCommandInteraction, leader: disnake.Member):
        await inter.response.defer()

        if not (command := self.db.get_command(leader.id)):
            await inter.followup.send(
                embed=disnake.Embed(title="Команда не знайдена", color=disnake.Color.yellow())
            )
            return

        created_by_user = inter.guild.get_member(command.created_by_id)
        members = ""
        reserved = ""

        for i, command_member in enumerate(command.members):
            if command_member.reserved:
                reserved += f"{i+1}. <@{command_member.id}>\n"
            else:
                members += f"{i+1}. <@{command_member.id}>\n"  # get_user може повернути None і все піде нахуй :(

        embed = disnake.Embed(
            title=f"Команда {command.display_name}",
            description=f"Лідер: <@{command.leader_id}>",
            color=disnake.Color.green()
        )

        embed.add_field("Учасники", members)

        if reserved:
            embed.add_field("Резерв", reserved)

        embed.set_footer(text=created_by_user.display_name, icon_url=created_by_user.avatar.url)
        embed.timestamp = datetime.fromtimestamp(command.created_at)

        await inter.followup.send(embed=embed)

    @commands.slash_command(description="Повна інформація про команду")
    async def command_full_info(self, inter: disnake.ApplicationCommandInteraction, leader: disnake.Member):
        await inter.response.defer()

        if not self.db.user_is_admin(inter.user):
            await inter.followup.send(
                embed=disnake.Embed(title=f"Тільки організатор може переглядати повну інформацію про команду",
                                    color=disnake.Color.red())
            )
            return

        if not (command := self.db.get_command(leader.id)):
            await inter.followup.send(
                embed=disnake.Embed(title="Команда не знайдена", color=disnake.Color.yellow())
            )
            return

        created_by_user = inter.guild.get_member(command.created_by_id)
        members = ""
        reserved = ""

        for i, command_member in enumerate(command.members):
            if command_member.reserved:
                reserved += (f"{i + 1}. <@{command_member.id}>\n"
                             f"{command_member.first_name} {command_member.last_name} {command_member.group_number} група\n")
            else:
                members += (f"{i + 1}. <@{command_member.id}>\n"
                            f"{command_member.first_name} {command_member.last_name} {command_member.group_number} група\n")  # get_user може повернути None і все піде нахуй :(

        embed = disnake.Embed(
            title=f"Команда {command.display_name}",
            description=f"Лідер: <@{command.leader_id}>",
            color=disnake.Color.green()
        )

        embed.add_field("Учасники", members, inline=False)

        if reserved:
            embed.add_field("Резерв", reserved, inline=False)

        embed.set_footer(text=created_by_user.display_name, icon_url=created_by_user.avatar.url)
        embed.timestamp = datetime.fromtimestamp(command.created_at)

        await inter.user.send(embed=embed)

        embed = disnake.Embed(
            title=f"Інформація про команду {command.display_name} відправлена в особисті повідомлення",
            color=disnake.Color.green()
        )

        await inter.followup.send(embed=embed)

    @commands.slash_command(description="Список команд")
    async def commands_list(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()

        all_commands = self.db.get_all_commands(limit=25)

        embed = disnake.Embed(
            title=f"Список команд",
            description=f"Кількість команд: {len(all_commands)}",
            color=disnake.Color.green()
        )

        for command in all_commands:
            embed.add_field(name=f"**{command.display_name}**", value=f"Лідер: <@{command.leader_id}>", inline=False)

        await inter.followup.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Commands(bot))
