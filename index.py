import asyncio
from typing import Union
import aiomysql
import discord
from discord.ext import commands
from dislash import InteractionClient, ActionRow, Button, ButtonStyle
import json
with open('env.json', 'r') as f:
    env=json.load(f)
COLOUR=env['COLOUR']
DB_PASSWORD=env['database']['password']
DB_USER=env['database']['user']
DB_HOST=env['database']['host']
TOKEN=env['TOKEN']
def get_prefix():
    with open('env.json', 'r') as f:
        env = json.load(f)
        return env['PREFIX']
def fetch_prefix(bot, message):
    with open('env.json', 'r') as f:
        env = json.load(f)
        pr=env['PREFIX']
        return commands.when_mentioned_or(pr)(bot, message)

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=fetch_prefix,intents=intents, case_insensitive=True)
bot.remove_command('help')
slash = InteractionClient(bot)

@bot.event
async def on_ready():
    print("Bot ready")
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="over tutors"))


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)
    if message.content == f'<@!{bot.user.id}>' or message.content == f'<@{bot.user.id}>':
        prefix=get_prefix()
        embed = discord.Embed(colour=COLOUR, description=f'The current server prefix is\t`{prefix}` ')
        await message.channel.send(embed=embed)

@bot.command(description='Help Command',usage='help [command]')
async def help(ctx, *, arg=None):
    prefix=get_prefix()
    if not arg:
        embed=discord.Embed(colour=COLOUR,title='Help')
        for i in bot.commands:
            embed.add_field(name=f"​`{prefix}{i.name}`",value=f"​{i.description}")
        await ctx.send(embed=embed)
    else:
        cmnd = bot.get_command(arg.lower())
        if not cmnd:
            embed = discord.Embed(colour=COLOUR,
                                  description=f"<:sypher_cross:833930332604465181> Command Not Found\nUse `{prefix}help` for help\nUse `{prefix}help [command]` for command help")

            await ctx.send(embed=embed)
        elif cmnd.description:
            embed = discord.Embed(colour=COLOUR)
            embed.set_author(name=f"​{cmnd.name}", icon_url=bot.user.avatar_url_as(format='png'))
            embed.add_field(name="• Description", value=f"​{cmnd.description}", inline=False)

            if cmnd.aliases:
                embed.add_field(name="• Aliases", value=f"[ {','.join(cmnd.aliases)} ]", inline=False)
            use = cmnd.usage
            embed.add_field(name="• Usage", value=f"​`{prefix}{use}`", inline=False)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(colour=COLOUR,
                                  description=f"<:sypher_cross:833930332604465181> Command Not Found\nUse `{prefix}help` for help\nUse `{prefix}help [command]` for command help")

            await ctx.send(embed=embed)

@bot.command(description='To change the bot prefix',usage='prefix {prefix}')
@commands.has_guild_permissions(administrator=True)
async def prefix(ctx,prfx=None):
    if not prfx:
        await ctx.send("<:sypher_cross:833930332604465181> Please provide a new prefix to replace")
        return
    with open('env.json', 'r') as f:
        p= json.load(f)
        p['PREFIX']=prfx
    with open('env.json', 'w') as f:
        json.dump(p, f, indent=4)
    await ctx.send(f"<:sypher_tick:833930333434019882> The prefix has been changed to `{prfx}`")
    return

@bot.command(description='Setup a channel for counter logging',usage='log')
@commands.has_guild_permissions(administrator=True,manage_guild=True)
async def log(ctx):
    pool = await aiomysql.create_pool(host=DB_HOST,
                                      user=DB_USER,
                                      password=DB_PASSWORD, db='counter',port=3306, autocommit=True)
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(f'''UPDATE settings SET log_channel='{ctx.channel.id}';''')
                await conn.commit()
            except:
                pass
    pool.close()
    await pool.wait_closed()
    embed=discord.Embed(description=f"<:sypher_tick:833930333434019882> <#{ctx.channel.id}> has been set as the logging channel for counting",colour=COLOUR)
    await ctx.send(embed=embed)


@bot.command(description='Setup a role for counters',usage='counter {role}')
@commands.has_guild_permissions(administrator=True,manage_guild=True)
async def counter(ctx,role : Union[discord.Role,int,str]=None):
    if not role:
        await ctx.send("<:sypher_cross:833930332604465181> Please mention the role you want to set for counters")
        return
    elif type(role)==int:
        role=ctx.guild.get_role(role)
        if not role:
            await ctx.send("<:sypher_cross:833930332604465181> The id provided does not correspond to a role in this server")
            return
    elif type(role)==str:
        role=discord.utils.get(ctx.guild.roles,name=role)
        if not role:
            await ctx.send("<:sypher_cross:833930332604465181> The name provided does not correspond to a role in this server")
            return
    pool = await aiomysql.create_pool(host=DB_HOST,
                                      user=DB_USER,
                                      password=DB_PASSWORD, db='counter',port=3306, autocommit=True)
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(f'''UPDATE settings SET counter_role='{role.id}';''')
                await conn.commit()
            except:
                pass
    pool.close()
    await pool.wait_closed()
    embed=discord.Embed(colour=COLOUR,description=f"<:sypher_tick:833930333434019882> <@&{role.id}> has been set as the counter role")
    await ctx.send(embed=embed)



@slash.message_command(name="count",description='Adds a count to a members record',usage='count')
async def count(ctx):
    await ctx.reply(type=5)
    author=ctx.message.author
    pool = await aiomysql.create_pool(host=DB_HOST,
                                      user=DB_USER,
                                      password=DB_PASSWORD, db='counter', port=3306, autocommit=True)
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(f'''SELECT * FROM settings''')
                r=await cursor.fetchall()
            except:
                pass
            counter_role=ctx.guild.get_role(int(r[0][1]))
            if not counter_role in ctx.author.roles:
                embed=discord.Embed(description=f"<:sypher_cross:833930332604465181> You require <@&{counter_role.id}> role to use this command",colour=COLOUR)
                await ctx.edit(embed=embed)
                return
            log_channel=await bot.fetch_channel(int(r[0][0]))
            try:
                await cursor.execute(f'''SELECT * FROM counts where user='{author.id}';''')
                p=await cursor.fetchall()
                if not p:
                    await cursor.execute(f'''INSERT INTO counts values('{author.id}',1,'{str(author)}');''')
                    await conn.commit()
                else:
                    count =p[0][1]+1
                    await cursor.execute(f'''UPDATE counts SET count={count},username='{str(author)}' where user='{author.id}';''')
                    await conn.commit()

            except:
                pass
            await ctx.message.add_reaction('👍🏻')
            await ctx.delete()
            embed=discord.Embed(colour=COLOUR,description=f"**{ctx.author}** added **1** coin to **{author}** for [this]({ctx.message.jump_url}) answer")
            await log_channel.send(embed=embed)
    pool.close()
    await pool.wait_closed()
@bot.command(aliases=['lb'],description='Get the leaderboard',usage='leaderboard')
async def leaderboard(ctx):
    pool = await aiomysql.create_pool(host=DB_HOST,
                                      user=DB_USER,
                                      password=DB_PASSWORD, db='counter', port=3306, autocommit=True)
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(f'''SELECT * FROM counts ORDER BY count DESC''')
                r = await cursor.fetchall()
            except:
                pass
            page=1
            if len(r)%25==0:
                last_page=len(r)/25
            else:
                last_page=len(r)//25+1
            row_of_buttons_first = ActionRow(
                Button(
                    style=ButtonStyle.red,
                    label='next',
                    custom_id="next"
                )
            )
            row_of_buttons_mid = ActionRow(
                Button(
                    style=ButtonStyle.red,
                    label='previous',
                    custom_id="previous"
                ),
                Button(
                    style=ButtonStyle.red,
                    label='next',
                    custom_id="next"
                )
            )
            row_of_buttons_last = ActionRow(
                Button(
                    style=ButtonStyle.red,
                    label='previous',
                    custom_id="previous"
                )
            )
            if not r:
                embed = discord.Embed(colour=COLOUR,description="<:sypher_cross:833930332604465181> Record is empty")
                await ctx.send(embed=embed)
                return
            embed=discord.Embed(colour=COLOUR,title="Leaderboard")
            limit=25
            if len(r)<25:
                limit=len(r)

            for i in range(limit):
                embed.add_field(name=f"{r[i][2]}",value=f"🪙 {r[i][1]}",inline=False)
            if len(r)<25:
                msg = await ctx.send(
                    embed=embed
                )
                return
            msg = await ctx.send(
                embed=embed,
                components=[row_of_buttons_first]
            )

            # Wait for someone to click on them
            def check(inter):
                if inter.message.id == msg.id and inter.author.id==ctx.author.id:
                    return True

            while True:
                try:
                    inter = await ctx.wait_for_button_click(check,timeout=120.0)
                    await inter.reply(type=7)
                    # Send what you received
                    button_text = inter.clicked_button.label
                    if button_text=='next':
                        page=page+1
                    elif button_text=='previous':
                        page=page-1
                    embed = discord.Embed(colour=COLOUR, title="Leaderboard")
                    limit = page*25
                    if len(r) < limit:
                        limit = len(r)
                    for i in range((page - 1) * 25,limit):
                        embed.add_field(name=f"{r[i][2]}", value=f"🪙 {r[i][1]}",inline=False)
                    if page==last_page:
                        await msg.edit(
                            embed=embed,
                            components=[row_of_buttons_last]
                        )
                    elif page==1:
                        await msg.edit(
                        embed=embed,
                        components=[row_of_buttons_first]
                        )
                    else:
                        await msg.edit(
                            embed=embed,
                            components=[row_of_buttons_mid]
                        )
                except asyncio.TimeoutError:
                    return
    pool.close()
    await pool.wait_closed()


@bot.command(description='Get the number of answers of a particular tutor',usage='counts [member]')
async def counts(ctx,member:Union[discord.Member,int,str]=None):
    if not member:
        member=ctx.author
    if type(member)==int:
        member=ctx.guild.get_member(member)
        if not member:
            await ctx.send("<:sypher_cross:833930332604465181> Member Not Found")
            return
    elif type(member)==str:
        member=discord.utils.get(ctx.guild.members,name=member)
        if not member:
            await ctx.send("<:sypher_cross:833930332604465181> Member Not Found")
            return
    pool = await aiomysql.create_pool(host=DB_HOST,
                                      user=DB_USER,
                                      password=DB_PASSWORD, db='counter', port=3306, autocommit=True)
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(f'''SELECT * FROM counts where user='{member.id}';''')
                r = await cursor.fetchall()
            except:
                pass
            if not r:
                embed = discord.Embed(
                    description=f"<:sypher_cross:833930332604465181> **{member}** has not answered any questions yet",colour=COLOUR)
                await ctx.send(embed=embed)
                return
            embed=discord.Embed(colour=COLOUR,description=f"**{member}** has answered **{r[0][1]}** questions")
            await ctx.send(embed=embed)

@bot.command(description='clear the current records to restart counting',usage='clear [member]')
@commands.has_guild_permissions(administrator=True,manage_guild=True)
async def clear(ctx,member:Union[discord.Member,int,str]=None):
    all=False
    if not member:
        all=True
    if type(member)==int:
        member=ctx.guild.get_member(member)
        if not member:
            await ctx.send("<:sypher_cross:833930332604465181> Member Not Found")
            return
    elif type(member)==str:
        member=discord.utils.get(ctx.guild.members,name=member)
        if not member:
            await ctx.send("<:sypher_cross:833930332604465181> Member Not Found")
            return
    pool = await aiomysql.create_pool(host=DB_HOST,
                                      user=DB_USER,
                                      password=DB_PASSWORD, db='counter', port=3306, autocommit=True)
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if not all:
                try:
                    await cursor.execute(f'''DELETE FROM counts where user='{member.id}';''')
                    await conn.commit()
                    await ctx.send(f"🗑 The record of **{member}** has been cleared")
                except:
                    pass

            else:
                try:
                    await cursor.execute(f'''DELETE FROM counts;''')
                    await conn.commit()
                    await ctx.send(f"🗑 The entire record has been cleared")
                except:
                    pass


    pool.close()
    await pool.wait_closed()

@bot.event
async def on_command_error(ctx,error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MaxConcurrencyReached):
        return
    if isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(colour=COLOUR,
                              description=f"<:sypher_cross:833930332604465181> I am missing these permissions: `{'`|`'.join(error.missing_perms)}`")
        await ctx.send(embed=embed)
        return
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(colour=COLOUR,
                              description=f"<:sypher_cross:833930332604465181> You do not have the following permissions: `{'`|`'.join(error.missing_perms)}`")
        await ctx.send(embed=embed)
        return
    if isinstance(error, commands.errors.MemberNotFound):
        embed = discord.Embed(colour=COLOUR,
                              description=f"<:sypher_cross:833930332604465181> Member not found")
        await ctx.send(embed=embed)
        return
    if isinstance(error, commands.errors.ChannelNotFound):
        embed = discord.Embed(colour=COLOUR,
                              description=f"<:sypher_cross:833930332604465181> Channel not found")
        await ctx.send(embed=embed)
        return


bot.run(TOKEN)
