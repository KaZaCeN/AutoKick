import discord
import asyncio
from discord.ext import commands, tasks
import json
import sys
from datetime import datetime
import typing

intents = discord.Intents.default()
intents.members = True
intents.messages = True

def tpfx(code=0):
    '''Return the current time to use in volatile logging'''
    # Codes (integers)
    # 3 - fatal
    # 2 - error
    # 1 - warning
    # 0 - info (default)
    t = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if code == 3:
        tag = "[FATAL] "
    elif code == 2:
        tag = "[ERROR] "
    elif code == 1:
        tag = "[WARN]  "
    else:
        tag = "[INFO]  "

    return (tag + t + ">")

# Attempt to read a bot config file (called bot_config.json). If the file does not exist, create it and quit.
try:
    with open('bot_config.json','r') as cfg_file:
        bot_config = json.load(cfg_file)
except FileNotFoundError:
    bot_config = {
        "token":"TU_TOKEN_AQUI",
        "prefix":"!!",
        "good_rxn":"🟩",
        "bad_rxn":"🟥"
    }
    with open('bot_config.json','w') as cfg_file:
        json.dump(bot_config, cfg_file)
        print("{} Generado el archivo bot_config.json, por favor, actualicelo antes de ejecutar de nuevo".format(tpfx(3)))
    sys.exit()

# Attempt to read a server config file (called server_config.json). If the file does not exist, create an empty dictionary in memory.
try:
    with open('server_config.json','r') as cfg_file:
        server_config = json.load(cfg_file)
except FileNotFoundError:
    server_config = {}

# Setup for Discord bot - 
bot = commands.Bot(command_prefix=commands.when_mentioned_or(bot_config["prefix"]),intents=intents)
bot.remove_command('help')

def write_server_config():
    '''Dump the server config in memory to a file'''
    with open('server_config.json','w') as cfg_file:
        json.dump(server_config, cfg_file)

async def no_pm(ctx):
    '''Check to make sure the user is not using specific commands in PMs'''
    if ctx.guild is None:
        raise commands.errors.NoPrivateMessage()
    return ctx.guild

async def perms(ctx):
    '''Check to make sure the user has the Manage Guild permission for certain commands'''
    gperms = ctx.author.guild_permissions
    if not gperms.manage_guild:
        raise commands.errors.MissingPermissions(["Manage Guild"])
    return gperms.manage_guild

# When the bot is fully logged in and the cache is created, log it.
@bot.event
async def on_ready():
    print("{} {} ha iniciado sesion correctamente y esta listo.".format(tpfx(),bot.user))

# If the bot disconnects from Discord, log it.
@bot.event
async def on_disconnect():
    print("{} Desconectado de Discord".format(tpfx(1)))

# If the bot resumes its connection to Discord, log it.
@bot.event
async def on_resumed():
    print("{} Reconectado a Discord".format(tpfx()))

@bot.command(name="help")
async def _help(ctx, cmd=None):
    '''Help command. Self-explanatory'''
    await ctx.message.add_reaction(bot_config["good_rxn"])
    if cmd == None:
        await ctx.send('''```Para ayuda sobre un comando en específico, escribe {}help <nombre_del_comando>
help - muestra este comando
timeout <tiempo_en_minutos> - registra el tiempo de espera antes de expulsar los usuarios sin roles.
toggle - activa o desactiva la expulsión automatica de usuarios sin roles```'''.format(bot_config["prefix"]))
    elif cmd.lower() == "timeout":
        await ctx.send('''```timeout - registra el tiempo de espera antes de expulsar los usuarios sin roles.
argument <tiempo_en_minuto> - registra el tiempo de espera antes de expulsar los usuarios sin roles. Si no se especifica, muestra el valor actual.
nota - solo los usuarios con el permiso de Gestionar Servidor pueden usar este comando.
nota - este comando no se puede usar en PMs.
ejemplo - {}timeout 20```'''.format(bot_config["prefix"]))
    elif cmd.lower() == "toggle":
        await ctx.send('''```toggle - activa o desactiva la expulsión automatica de usuarios sin roles
nota - solo los usuarios con el permiso de Gestionar Servidor pueden usar este comando.
nota - este comando no se puede usar en PMs.
ejemplo - {}toggle```'''.format(bot_config["prefix"]))
    else:
        await ctx.send("No hay ayuda disponible para este comando.")

@bot.command(name="timeout", aliases=["delay"])
@commands.check(no_pm)
@commands.check(perms)
async def _timeout(ctx, timeout: typing.Optional[int] = None):
    '''Set the timeout for a specific server. Timeout values must be greater than or equal to 1 minute. Only users with the Manage Guild permission can use this command.'''
    if timeout == None:
        await ctx.message.add_reaction(bot_config["good_rxn"])
        await ctx.send("\{}La espera actual es de **{}** minutos.".format(bot_config["good_rxn"],server_config[str(ctx.guild.id)]["timeout"]))
        return

    int_timeout = int(timeout)

    if int_timeout < 1:
        await ctx.message.add_reaction(bot_config["bad_rxn"])
        await ctx.send("\{}La espera no debe ser menor de 1.".format(bot_config["bad_rxn"]))
        return

    try:
        old_timeout = server_config[str(ctx.guild.id)]["timeout"]
    except KeyError:
        old_timeout = -1

    server_config[str(ctx.guild.id)] = {}
    server_config[str(ctx.guild.id)]["timeout"] = int_timeout
    server_config[str(ctx.guild.id)]["enabled"] = True
    write_server_config()
    print("{} Espera actualizada en el servidor {} (ID: {}) - {} -> {} - Invocado por {} (ID: {})".format(tpfx(),ctx.guild.name,ctx.guild.id,old_timeout,timeout,ctx.author.name,ctx.author.id))
    await ctx.message.add_reaction(bot_config["good_rxn"])

@_timeout.error
async def _timeout_error(ctx, error):
    if isinstance(error, commands.errors.NoPrivateMessage):
        await ctx.message.add_reaction(bot_config["bad_rxn"])
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.message.add_reaction(bot_config["bad_rxn"])
        await ctx.send("\{}Debes tener el permiso de `Gestionar Servidor` para usar este comando.".format(bot_config["bad_rxn"]))
    else:
        raise(error)

@bot.command(name="toggle")
@commands.check(no_pm)
@commands.check(perms)
async def _toggle(ctx):
    '''Toggle whether or not to enforce the timeout value for a specific server. Only users with the Manage Guild permission can use this command.'''
    try:
        if server_config[str(ctx.guild.id)]["enabled"] == True:
            server_config[str(ctx.guild.id)]["enabled"] = False
        elif server_config[str(ctx.guild.id)]["enabled"] == False:
            server_config[str(ctx.guild.id)]["enabled"] = True
        print("{} Activador cambiado en el servidor {} (ID {}). {}, invocado por {} (ID {})".format(tpfx(),ctx.guild.name,ctx.guild.id,server_config[str(ctx.guild.id)]["enabled"],ctx.author.name,ctx.author.id))
        write_server_config()

        await ctx.message.add_reaction(bot_config["good_rxn"])
        if server_config[str(ctx.guild.id)]["enabled"] == True:
            await ctx.send("\{}**Activado** este servidor".format(bot_config["good_rxn"]))
        elif server_config[str(ctx.guild.id)]["enabled"] == False:
            await ctx.send("\{}**Desactivado** este servidor".format(bot_config["good_rxn"]))
    except KeyError:
        server_config[str(ctx.guild.id)] = {}
        server_config[str(ctx.guild.id)]["timeout"] = 20
        server_config[str(ctx.guild.id)]["enabled"] = True
        print("{} Activador cambiado en el servidor (sin registro) {} (ID {}). {}, invocado por {} (ID {})".format(tpfx(),ctx.guild.name,ctx.guild.id,server_config[str(ctx.guild.id)]["enabled"],ctx.author.name,ctx.author.id))
        write_server_config()

        await ctx.message.add_reaction(bot_config["good_rxn"])
        await ctx.send("\{}Activado este servidor con una espera de **20** minutos".format(bot_config["good_rxn"]))

@_toggle.error
async def _toggle_error(ctx, error):
    if isinstance(error, commands.errors.NoPrivateMessage):
        await ctx.message.add_reaction(bot_config["bad_rxn"])
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.message.add_reaction(bot_config["bad_rxn"])
        await ctx.send("\{}Debes tener el permiso de `Gestionar Servidor` para usar este comando.".format(bot_config["bad_rxn"]))
    else:
        raise(error)

# When a user joins, after x minutes, check if they have any roles. If they don't, kick them.
@bot.event
async def on_member_join(member):
    try:
        server_config[str(member.guild.id)]
    except KeyError:
        return

    if server_config[str(member.guild.id)]["enabled"] == False:
        return


    # If you want to add a message when the user joins, do it here.
    # An example message is given below. Feel free to uncomment it.

    #await member.send("Welcome, {}, to {}!".format(member.name,member.guild.name))

    print("{} {} (ID: {}) se ha unido al servidor {} (ID: {}), esperando {} minutos para expulsarlo".format(tpfx(),member.name,member.id,member.guild.name,member.guild.id,server_config[str(member.guild.id)]["timeout"]))
    await asyncio.sleep(int((server_config[str(member.guild.id)]["timeout"]))*60)

    if len(member.roles) == 1: #If a user "has no roles", they actually have the @everyone role, so the length of the roles is 1.

        # If you want to send the member a message before they get kicked, such as a "here's the resaon you were kicked" or "here's an invite to try again", do that here.
        # An example message is given below. Feel free to uncomment it.

        await member.send("Has sido expulsado de {} por no realizar la verificacion en {} horas. Si deseas entrar puedes volver a usar el enlace de invitacion.".format(member.guild.name,(server_config[str(member.guild.id)]["timeout"]/60)))

        await member.kick(reason="Sin realizar la verificacion tras {} horas".format(server_config[str(member.guild.id)]["timeout"]/60))
        print("{} {} (ID: {}) expulsado del servidor {} (ID: {}) al no tener ningun rol tras {} minutos".format(tpfx(),member.name,member.id,member.guild.name,member.guild.id,server_config[str(member.guild.id)]["timeout"]))
    
    elif len(member.roles) > 1:
        
        print("{} {} (ID: {}) tiene un rol en el servidor {} (ID: {}). Hilo finalizado.".format(tpfx(),member.name,member.id,member.guild.name,member.guild.id))


# Start the Discord bot.
bot.run(bot_config["token"])