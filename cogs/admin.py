import disnake
from disnake.ext import commands

from utilities.database import Database


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: Database = self.bot.database

    @commands.slash_command(description="Змінює роль адміністратора")
    async def set_admin_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role):
        if inter.user.id != 396639087731277825:
            await inter.response.send_message(
                embed=disnake.Embed(title="Не достатньо прав, лол", color=disnake.Color.red())
            )
            return

        self.db.set_admin_role_id(role.id)

        await inter.response.send_message(
            embed=disnake.Embed(title="Роль адміністратора встановлена", color=disnake.Color.green())
        )

    @commands.slash_command(description="Змінює роль учасника")
    async def set_member_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role):
        if not self.db.user_is_admin(inter.user):
            await inter.response.send_message(
                embed=disnake.Embed(title="Тільки організатор може змінювати роль учасника", color=disnake.Color.red())
            )
            return

        self.db.set_tournament_member_role_id(role.id)

        await inter.response.send_message(
            embed=disnake.Embed(title="Роль учасника встановлена", color=disnake.Color.green())
        )

    @commands.slash_command(description="Змінює канал турніру")
    async def set_tournament_channel(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        if not self.db.user_is_admin(inter.user):
            await inter.response.send_message(
                embed=disnake.Embed(title="Тільки організатор може змінювати канал турніру", color=disnake.Color.red())
            )
            return

        self.db.set_tournament_channel_id(channel.id)

        await inter.response.send_message(
            embed=disnake.Embed(title="Канал турніру встановлений", color=disnake.Color.green())
        )

    @commands.slash_command(description="Змінює канал турніру")
    async def set_max_members(self, inter: disnake.ApplicationCommandInteraction, value: int):
        if not self.db.user_is_admin(inter.user):
            await inter.response.send_message(
                embed=disnake.Embed(title="Тільки організатор може змінювати максимальну кількість учасників команд",
                                    color=disnake.Color.red())
            )
            return

        self.db.set_max_members(value)

        await inter.response.send_message(
            embed=disnake.Embed(title="Максимальна кількість учасників команд встановлена", color=disnake.Color.green())
        )

    @commands.slash_command(description="Yep")
    async def yep(self, inter: disnake.ApplicationCommandInteraction):
        print(str(self.db.user_is_admin(inter.user)))
        await inter.response.send_message(str(self.db.user_is_admin(inter.user)))


def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))
