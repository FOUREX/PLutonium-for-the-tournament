import disnake
from disnake.ext import commands

from utilities.database import Database
from utilities.datatypes import Match
from utilities.datatypes import Command


Inter = disnake.ApplicationCommandInteraction


class SelectWinnerView(disnake.ui.View):
    def __init__(self, match: Match, panel: disnake.Message, notice: disnake.Message):
        super().__init__(timeout=None)
        self.match = match
        self.panel = panel
        self.notice = notice

        self.commands: list[Command] = [self.match.first_command, self.match.second_command]

    async def startup(self):
        for i, component in enumerate(self.children):
            component: disnake.Button = component
            component.label = self.commands[i].display_name

        await self.panel.edit(view=self)

    async def on_button_click(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await inter.response.defer()

        winner = self.commands[0] if self.commands[0].name == button.label.lower() else self.commands[1]

        embed = self.panel.embeds[0]
        embed.description = embed.description.replace("не визначений", f"`{winner.display_name}`")

        await self.panel.edit(embed=embed, view=None)

        await self.notice.reply(
            f"# Перемогу отримує команда {button.label}\n<@&{winner.member_role_id}>"
        )

    @disnake.ui.button(label="Команда 1", style=disnake.ButtonStyle.success)
    async def first_command(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await self.on_button_click(button, inter)

    @disnake.ui.button(label="Команда 2", style=disnake.ButtonStyle.success)
    async def second_command(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await self.on_button_click(button, inter)


class PanelView(disnake.ui.View):
    def __init__(self, db: Database, notice: disnake.Message, match_id: int):
        super().__init__(timeout=None)
        self.db = db
        self.notice = notice

        self.match = self.db.get_match(match_id)
        self.panel: disnake.Message = ...

    @disnake.ui.button(label="Завершити", style=disnake.ButtonStyle.danger)
    async def end_match(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await inter.response.defer()

        view = SelectWinnerView(self.match, self.panel, self.notice)

        await self.panel.edit(view=view)
        await view.startup()


class Dota2Tournament(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: Database = self.bot.database

    @commands.slash_command(description="Створює команду")
    async def prepare_dota_match(self, inter: Inter, first_command_leader: disnake.Member,
                                 second_command_leader: disnake.Member, prepare_time: int = 10):
        await inter.response.defer()

        # Checks

        if not self.db.user_is_admin(inter.user):
            return await inter.followup.send(
                embed=disnake.Embed(title="Тільки організатор може починати матч", color=disnake.Color.red())
            )

        if not (first_command := self.db.get_command(first_command_leader.id, require_members=False)):
            return await inter.followup.send(
                embed=disnake.Embed(title=f"{first_command_leader.name} не є лідером команди",
                                    color=disnake.Color.yellow())
            )

        if not (second_command := self.db.get_command(second_command_leader.id, require_members=False)):
            return await inter.followup.send(
                embed=disnake.Embed(title=f"{second_command_leader.name} не є лідером команди",
                                    color=disnake.Color.yellow())
            )

        # Send in tournament channel

        tournament_channel = inter.guild.get_channel(self.db.get_tournament_channel_id())
        first_command_leader = inter.guild.get_member(first_command.leader_id)
        second_command_leader = inter.guild.get_member(second_command.leader_id)
        first_command_role = inter.guild.get_role(first_command.member_role_id)
        second_command_role = inter.guild.get_role(second_command.member_role_id)
        first_command_category = inter.guild.get_channel(first_command.category_id)
        second_command_category = inter.guild.get_channel(second_command.category_id)

        notice = await tournament_channel.send(
            f"# Через {prepare_time} хвилин початок матчу між {first_command.display_name} та {second_command.display_name}\n"
            f"{first_command_role.mention} {second_command_role.mention}"
        )

        # Startup panel

        await inter.followup.send("Створення матчу...", delete_after=1)
        panel: disnake.Message = await inter.channel.send("Створення матчу...")

        match_id = self.db.create_match(first_command, second_command, panel.id, notice.id, inter.user.id)

        embed = (disnake.Embed(
            title="Панель управління матчем\nDOTA2",
            description=f"ID: `{match_id}`\nКуратор: {inter.user.mention}\nПереможець: не визначений",
            color=disnake.Color.blue())
        )
        embed.add_field(
            f"Команда {first_command.display_name}",
            f"Лідер: {first_command_leader.mention}\nКанал: {first_command_category.channels[0].mention}",
            inline=False
        )
        embed.add_field(
            f"Команда {second_command.display_name}",
            f"Лідер: {second_command_leader.mention}\nКанал: {second_command_category.channels[0].mention}",
            inline=False
        )

        view = PanelView(self.db, notice, match_id)

        panel = await panel.edit(content=None, embed=embed, view=view)

        view.panel = panel


def setup(bot: commands.Bot):
    bot.add_cog(Dota2Tournament(bot))
