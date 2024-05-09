import disnake
from disnake.ext import commands

from utilities.database import Database
from utilities.datatypes import Match
from utilities.datatypes import Command


Inter = disnake.ApplicationCommandInteraction  # Я заєбався


class MapPickView(disnake.ui.View):
    def __init__(self, match: Match, panel: disnake.Message):
        super().__init__(timeout=None)
        self.match = match
        self.panel = panel

        self.sides: list[Command] = [self.match.first_command, self.match.second_command]
        self.messages: list[disnake.Message] = [..., ...]
        self.side = False

        self.maps_left = len(self.children)

    async def startup(self):
        for component in self.children:
            component.disabled = False

        await self.messages[self.side].edit(view=self)

    async def update(self):
        for component in self.children:
            component.disabled = True

        embed = disnake.Embed(
            title="Вибір мапи", description="Лідери команд по черзі виключають мапи", color=disnake.Color.blue()
        )
        embed.add_field("Зараз вибирає команда", self.sides[not self.side].display_name)

        await self.messages[self.side].edit(embed=embed, view=self)

        for component in self.children:
            component: disnake.ui.Button = component

            if component.style != disnake.ButtonStyle.danger:
                component.disabled = False

        await self.messages[not self.side].edit(embed=embed, view=self)

        self.side = not self.side

        if self.maps_left != 1:
            return

        picked_map = ""

        for component in self.children:
            component: disnake.ui.Button = component

            if component.style != disnake.ButtonStyle.success:
                continue

            picked_map = component.label
            break

        embed = self.panel.embeds[0]
        embed.description = embed.description.replace("не вибрана", f"`{picked_map}`")

        await self.panel.edit(embed=embed)

        for message in self.messages:
            await message.edit(
                embed=disnake.Embed(title=f"Вибрана мапа {picked_map}", color=disnake.Color.blue()), view=None
            )

    async def on_button_click(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await inter.response.defer()

        if inter.user.id != self.sides[self.side].leader_id and inter.user.id != 396639087731277825:
            return

        button.style = disnake.ButtonStyle.danger
        self.maps_left -= 1

        await self.update()

    @disnake.ui.button(label="Mirage", style=disnake.ButtonStyle.success, disabled=True)
    async def mirage(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await self.on_button_click(button, inter)

    @disnake.ui.button(label="Inferno", style=disnake.ButtonStyle.success, disabled=True)
    async def inferno(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await self.on_button_click(button, inter)

    @disnake.ui.button(label="Overpass", style=disnake.ButtonStyle.success, disabled=True)
    async def overpass(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await self.on_button_click(button, inter)

    @disnake.ui.button(label="Nuke", style=disnake.ButtonStyle.success, disabled=True)
    async def nuke(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await self.on_button_click(button, inter)

    @disnake.ui.button(label="Vertigo", style=disnake.ButtonStyle.success, disabled=True)
    async def vertigo(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await self.on_button_click(button, inter)

    @disnake.ui.button(label="Ancient", style=disnake.ButtonStyle.success, disabled=True)
    async def ancient(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await self.on_button_click(button, inter)

    @disnake.ui.button(label="Anubis", style=disnake.ButtonStyle.success, disabled=True)
    async def anubis(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await self.on_button_click(button, inter)


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

    @disnake.ui.button(label="Запустити вибір мап", style=disnake.ButtonStyle.primary)
    async def start_map_pick(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await inter.response.defer()

        first_command_channel = inter.guild.get_channel(self.match.first_command.category_id).channels[0]
        second_command_channel = inter.guild.get_channel(self.match.second_command.category_id).channels[0]

        embed = disnake.Embed(
            title="Вибір мапи", description="Лідери команд по черзі виключають мапи", color=disnake.Color.blue()
        )
        embed.add_field("Зараз вибирає команда", self.match.first_command.display_name)

        view = MapPickView(self.match, self.panel)

        view.messages[0] = await first_command_channel.send(f"<@&{self.match.first_command.leader_role_id}>", embed=embed, view=view)
        view.messages[1] = await second_command_channel.send(f"<@&{self.match.second_command.leader_role_id}>", embed=embed, view=view)

        await view.startup()

        button.disabled = True

        await inter.edit_original_message(view=self)

    @disnake.ui.button(label="Завершити", style=disnake.ButtonStyle.danger)
    async def end_match(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await inter.response.defer()

        view = SelectWinnerView(self.match, self.panel, self.notice)

        await self.panel.edit(view=view)
        await view.startup()


class CS2Tournament(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: Database = self.bot.database

    @commands.slash_command(description="Створює команду")
    async def prepare_cs_match(self, inter: Inter, first_command_leader: disnake.Member,
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
            title="Панель управління матчем\nCS2",
            description=f"ID: `{match_id}`\nКуратор: {inter.user.mention}\nМапа: не вибрана\nПереможець: не визначений",
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
    bot.add_cog(CS2Tournament(bot))
