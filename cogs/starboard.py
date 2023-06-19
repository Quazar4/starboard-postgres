import hikari
import lightbulb
import asyncpg

class Starboard(lightbulb.Plugin):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def create_starboard_table(self):
        async with self.bot.postgres_pool.acquire() as connection:
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS starboard (
                    message_id BIGINT PRIMARY KEY,
                    starboard_message_id BIGINT,
                    star_count INT
                )
            ''')

    @lightbulb.listener(lightbulb.Events.STARTED)
    async def on_started(self, event: lightbulb.BotStartedEvent):
        print("Starboard is ready!")
        await self.create_starboard_table()

    @lightbulb.listener(hikari.GuildMessageReactionAddEvent)
    async def on_reaction_add(self, event: hikari.GuildMessageReactionAddEvent):
        if str(event.emoji) == '⭐' and not event.member.is_bot:
            async with self.bot.postgres_pool.acquire() as connection:
                query = 'SELECT * FROM starboard WHERE message_id = $1'
                starboard_entry = await connection.fetchrow(query, event.message_id)

                if not starboard_entry:
                    channel = await self.bot.rest.fetch_channel(event.channel_id)
                    message = await channel.fetch_message(event.message_id)

                    starboard_channel = await self.bot.rest.fetch_channel_id(event.guild_id, name='starboard')
                    if not starboard_channel:
                        starboard_channel = await self.bot.rest.create_guild_text_channel(
                            event.guild_id,
                            name='starboard',
                            category_id=your_category_id  # Replace with the actual category ID
                        )

                    starboard_message = await self.bot.rest.create_message(
                        starboard_channel.id,
                        f'Stars: {event.message.reactions[0].count} {message.jump_link}'
                    )

                    query = '''
                        INSERT INTO starboard (message_id, starboard_message_id, star_count)
                        VALUES ($1, $2, $3)
                    '''
                    await connection.execute(query, event.message_id, starboard_message.id, event.message.reactions[0].count)
                else:
                    star_count = starboard_entry['star_count'] + 1
                    starboard_channel = await self.bot.rest.fetch_channel_id(event.guild_id, name='starboard')
                    if starboard_channel:
                        starboard_message = await self.bot.rest.fetch_message(starboard_channel.id, starboard_entry['starboard_message_id'])
                        await starboard_message.edit(content=f'Stars: {star_count} {starboard_message.jump_link}')

                    query = 'UPDATE starboard SET star_count = $1 WHERE message_id = $2'
                    await connection.execute(query, star_count, event.message_id)

    @lightbulb.listener(hikari.GuildMessageReactionRemoveEvent)
    async def on_reaction_remove(self, event: hikari.GuildMessageReactionRemoveEvent):
        if str(event.emoji) == '⭐':
            async with self.bot.postgres_pool.acquire() as connection:
                query = 'SELECT * FROM starboard WHERE message_id = $1'
                starboard_entry = await connection.fetchrow(query, event.message_id)

                if starboard_entry:
                    star_count = starboard_entry['star_count'] - 1
                    starboard_channel = await self.bot.rest.fetch_channel_id(event.guild_id, name='starboard')
                    if starboard_channel:
                        starboard_message = await self.bot.rest.fetch_message(starboard_channel.id, starboard_entry['starboard_message_id'])
                        await starboard_message.edit(content=f'Stars: {star_count} {starboard_message.jump_link}')

                    if star_count <= 0:
                        query = 'DELETE FROM starboard WHERE message_id = $1'
                        await connection.execute(query, event.message_id)
                    else:
                        query = 'UPDATE starboard SET star_count = $1 WHERE message_id = $2'
                        await connection.execute(query, star_count, event.message_id)

def load(bot: lightbulb.Bot):
    bot.add_plugin(Starboard(bot))
