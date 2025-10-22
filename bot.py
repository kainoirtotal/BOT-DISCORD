import os
import asyncio
import datetime as dt
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# =========================================
#             LOAD CONFIG
# =========================================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # pour sync instantanée (id de ton serveur)

# =========================================
#             BOT & INTENTS
# =========================================
intents = discord.Intents.default()
intents.members = True          # gérer rôles / welcome
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================
#             UTILS
# =========================================
def mention_roles(member: discord.Member) -> str:
    roles = [r.mention for r in member.roles if r.name != "@everyone"]
    return ", ".join(roles) if roles else "Aucun"

# Petites citations (showcase simple)
QUOTES = [
    "Code, ship, learn, repeat.",
    "Fait > Parfait.",
    "Chaque jour un commit.",
    "Les petits outils changent de grands workflows.",
    "Keep it simple, ship it fast."
]

# =========================================
#             COMMANDES DE BASE
# =========================================
@app_commands.command(name="ping", description="Teste la latence du bot.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 {round(bot.latency*1000)} ms", ephemeral=True)

@app_commands.command(name="say", description="Faire parler le bot.")
@app_commands.describe(message="Texte", ephemere="Visible uniquement par toi ?")
async def say(interaction: discord.Interaction, message: str, ephemere: bool = False):
    await interaction.response.send_message(message, ephemeral=ephemere)

@app_commands.command(name="remind", description="Rappel après X minutes.")
@app_commands.describe(minutes="1 à 1440", message="Contenu du rappel")
async def remind(interaction: discord.Interaction, minutes: app_commands.Range[int,1,1440], message: str):
    await interaction.response.send_message(f"⏰ Rappel dans {minutes} min : « {message} »", ephemeral=True)
    await asyncio.sleep(minutes*60)
    try:
        await interaction.followup.send(f"🔔 Rappel : {message}", ephemeral=True)
    except:
        try:
            await interaction.user.send(f"🔔 Rappel : {message}")
        except:
            pass

# =========================================
#             SHOWCASE COMMANDS
# =========================================
@app_commands.command(name="help", description="Affiche les commandes disponibles.")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 Aide du bot", color=discord.Color.blurple())
    sections = {
        "Général": {"ping","say","remind","quote","avatar","userinfo","serverinfo"},
        "Admin": {"clear","kick","ban","load","setupverify","prsalon"},
    }
    # Génère dynamiquement depuis tree
    names = {c.name: c for c in bot.tree.get_commands()}
    def list_cmd(keys): return " · ".join(f"`/{k}`" for k in keys if k in names)
    embed.add_field(name="🧰 Général", value=list_cmd(sections["Général"]) or "—", inline=False)
    embed.add_field(name="🛡️ Admin", value=list_cmd(sections["Admin"]) or "—", inline=False)
    embed.set_footer(text="KAIHUB.fr • Slash commands")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@app_commands.command(name="userinfo", description="Infos rapides sur un utilisateur.")
@app_commands.describe(user="Utilisateur (optionnel)")
async def userinfo(interaction: discord.Interaction, user: discord.Member | None = None):
    m = user or interaction.user
    e = discord.Embed(title=f"👤 {m.display_name}", color=discord.Color.green(), timestamp=dt.datetime.utcnow())
    e.set_thumbnail(url=m.display_avatar.url)
    e.add_field(name="ID", value=str(m.id))
    e.add_field(name="Compte créé", value=discord.utils.format_dt(m.created_at, "D"))
    if isinstance(m, discord.Member):
        if m.joined_at:
            e.add_field(name="A rejoint", value=discord.utils.format_dt(m.joined_at, "D"))
        e.add_field(name="Rôles", value=mention_roles(m) or "Aucun", inline=False)
    await interaction.response.send_message(embed=e, ephemeral=True)

@app_commands.command(name="serverinfo", description="Infos sur le serveur.")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    e = discord.Embed(title=f"🏰 {g.name}", color=discord.Color.blurple(), timestamp=dt.datetime.utcnow())
    e.set_thumbnail(url=g.icon.url if g.icon else discord.Embed.Empty)
    e.add_field(name="Membres", value=str(g.member_count))
    e.add_field(name="Salons texte", value=str(len(g.text_channels)))
    e.add_field(name="Salons vocaux", value=str(len(g.voice_channels)))
    e.add_field(name="Rôles", value=str(len(g.roles)))
    e.add_field(name="Créé le", value=discord.utils.format_dt(g.created_at, "D"))
    await interaction.response.send_message(embed=e, ephemeral=True)

@app_commands.command(name="avatar", description="Affiche l'avatar d'un utilisateur.")
@app_commands.describe(user="Utilisateur (optionnel)")
async def avatar(interaction: discord.Interaction, user: discord.User | None = None):
    u = user or interaction.user
    e = discord.Embed(title=f"Avatar de {u.display_name}", color=discord.Color.dark_theme())
    e.set_image(url=u.display_avatar.url)
    await interaction.response.send_message(embed=e)

@app_commands.command(name="quote", description="Envoie une citation inspirante.")
async def quote(interaction: discord.Interaction):
    import random
    await interaction.response.send_message(f"💡 {random.choice(QUOTES)}")

# -------- Modération
@app_commands.command(name="clear", description="Supprime N messages dans ce salon.")
@app_commands.describe(amount="Nombre (1-100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: app_commands.Range[int,1,100]):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)  # type: ignore
    await interaction.followup.send(f"🧹 {len(deleted)} message(s) supprimé(s).", ephemeral=True)

@app_commands.command(name="kick", description="Expulse un membre.")
@app_commands.checks.has_permissions(kick_members=True)
@app_commands.describe(user="Membre à expulser", reason="Raison")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Aucune raison"):
    try:
        await user.kick(reason=reason)
        await interaction.response.send_message(f"👢 {user.mention} expulsé. Raison: {reason}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Je n'ai pas la permission d'expulser ce membre.", ephemeral=True)

@app_commands.command(name="ban", description="Bannit un membre.")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.describe(user="Membre à bannir", reason="Raison")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Aucune raison"):
    try:
        await user.ban(reason=reason)
        await interaction.response.send_message(f"⛔ {user.mention} banni. Raison: {reason}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Je n'ai pas la permission de bannir ce membre.", ephemeral=True)

# =========================================
#     SETUP SERVEUR / PERMISSIONS / VERIFY
# =========================================
@app_commands.command(name="load", description="Recrée la structure communautaire complète (wipe).")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.guild_only()
async def load_setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    guild: discord.Guild = interaction.guild  # type: ignore

    # wipe
    for ch in list(guild.channels):
        try: await ch.delete()
        except: pass
    for cat in list(guild.categories):
        try: await cat.delete()
        except: pass

    # roles
    mod_perms = discord.Permissions(manage_messages=True,kick_members=True,ban_members=True,manage_channels=True,manage_roles=True)
    role_mod = await guild.create_role(name="Modérateur", colour=discord.Color.blurple(), permissions=mod_perms, mentionable=True)
    role_membre = await guild.create_role(name="Membre", colour=discord.Color.dark_gray(), mentionable=True)
    role_nouveau = await guild.create_role(name="Nouveau", colour=discord.Color.light_grey(), mentionable=True)

    # categories
    cat_home  = await guild.create_category("🏠 accueil")
    cat_chat  = await guild.create_category("💬 discussions")
    cat_share = await guild.create_category("📚 ressources")
    cat_voice = await guild.create_category("🎙 vocaux")
    cat_staff = await guild.create_category("🛡 staff")

    # salons
    ch_rules   = await guild.create_text_channel("📜-règles", category=cat_home)
    ch_ann     = await guild.create_text_channel("📢-annonces", category=cat_home)
    ch_welcome = await guild.create_text_channel("👋-bienvenue", category=cat_home)
    await guild.create_text_channel("général", category=cat_chat)
    await guild.create_text_channel("dev", category=cat_chat)
    await guild.create_text_channel("off-topic", category=cat_chat)
    await guild.create_text_channel("tutos", category=cat_share)
    await guild.create_text_channel("freebies", category=cat_share)
    await guild.create_text_channel("showcase", category=cat_share)
    await guild.create_voice_channel("Salon vocal 1", category=cat_voice)
    await guild.create_voice_channel("Salon vocal 2", category=cat_voice)
   
        

    # permissions : seuls rules/annonces/bienvenue visibles par @everyone
    everyone = guild.default_role
    await ch_rules.edit(overwrites={everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=True)})
    await ch_ann.edit(  overwrites={everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False)})
    await ch_welcome.edit(overwrites={everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True)})

    # le reste : invisible à @everyone, visible aux Membres
    for cat in (cat_chat, cat_share, cat_voice):
        await cat.edit(overwrites={
            everyone: discord.PermissionOverwrite(view_channel=False),
            role_membre: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, connect=True, speak=True)
        })
    await cat_staff.edit(overwrites={
        everyone: discord.PermissionOverwrite(view_channel=False),
        role_mod: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    })

    await ch_rules.send("**Bienvenue !** 👋 Lis les règles, puis **réagis avec ✅** au message de vérification pour obtenir le rôle **Membre**.")
    await interaction.followup.send(f"✅ Structure recréée. Rôles: {role_mod.mention}, {role_membre.mention}, {role_nouveau.mention}", ephemeral=True)

@app_commands.command(name="setupverify", description="Poste l'embed de vérification dans 📜-règles.")
@app_commands.checks.has_permissions(manage_guild=True)
async def setup_verify(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    rules = discord.utils.get(interaction.guild.text_channels, name="📜-règles")  # type: ignore
    if not rules:
        await interaction.followup.send("❌ Salon 📜-règles introuvable.", ephemeral=True); return
    e = discord.Embed(
        title="📜 Règlement du serveur",
        description=("✅ Pour accéder à tous les salons, lis les règles puis **réagis avec ✅ ci-dessous.**\n\n"
                     "1️⃣ Respect • 2️⃣ Pas de spam • 3️⃣ Bons salons.\n\n"
                     "En validant, tu obtiens le rôle **Membre** 🎉"),
        color=discord.Color.blurple()
    )
    e.set_footer(text="Clique sur ✅ pour accepter les règles")
    msg = await rules.send(embed=e)
    await msg.add_reaction("✅")
    with open("verify_message_id.txt","w") as f: f.write(str(msg.id))
    await interaction.followup.send("✅ Embed de vérification envoyé.", ephemeral=True)

@app_commands.command(
    name="prsalon",
    description="Cache tout à @everyone (sauf 📜-règles/👋-bienvenue) et ouvre aux Membres."
)
@app_commands.checks.has_permissions(manage_channels=True)
async def prsalon(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    g = interaction.guild; everyone = g.default_role  # type: ignore
    role_membre = discord.utils.get(g.roles, name="Membre")
    if not role_membre:
        await interaction.followup.send("❌ Rôle **Membre** introuvable.", ephemeral=True); return
    ok=fail=0
    EXCEPT_NAMES = {"📜-règles","👋-bienvenue"}
    for ch in g.channels:  # type: ignore
        try:
            if ch.name in EXCEPT_NAMES: continue
            ovw_e = ch.overwrites_for(everyone); ovw_e.view_channel = False
            ovw_m = ch.overwrites_for(role_membre); ovw_m.view_channel = True
            if isinstance(ch, discord.TextChannel):
                ovw_m.send_messages = True; ovw_m.read_message_history = True
            if isinstance(ch, discord.VoiceChannel):
                ovw_m.connect = True; ovw_m.speak = True
            await ch.set_permissions(everyone, overwrite=ovw_e)
            await ch.set_permissions(role_membre, overwrite=ovw_m)
            ok += 1
        except Exception as e:
            print("[prsalon]", ch, e); fail += 1
    await interaction.followup.send(f"🔒 {ok} salon(s) masqué(s) à @everyone et ouvert(s) à **Membre** (⚠️ {fail} erreur(s)).", ephemeral=True)

# =========================================
#         RÉACTIONS → RÔLE MEMBRE
# =========================================
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.member is None or payload.member.bot: return
    try:
        with open("verify_message_id.txt") as f: mid = int(f.read().strip())
    except FileNotFoundError:
        return
    if payload.message_id == mid and str(payload.emoji) == "✅":
        role = discord.utils.get(payload.member.guild.roles, name="Membre")
        if role: await payload.member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    g = bot.get_guild(payload.guild_id); 
    if not g: return
    m = g.get_member(payload.user_id)
    if not m or m.bot: return
    try:
        with open("verify_message_id.txt") as f: mid = int(f.read().strip())
    except FileNotFoundError:
        return
    if payload.message_id == mid and str(payload.emoji) == "✅":
        role = discord.utils.get(g.roles, name="Membre")
        if role and role in m.roles: await m.remove_roles(role)

# =========================================
#          WELCOME AUTO (role Nouveau)
# =========================================
@bot.event
async def on_member_join(member: discord.Member):
    role_nouveau = discord.utils.get(member.guild.roles, name="Nouveau")
    if role_nouveau:
        try: await member.add_roles(role_nouveau, reason="Nouveau membre")
        except: pass
    ch = discord.utils.get(member.guild.text_channels, name="👋-bienvenue")
    if ch:
        try: await ch.send(f"Bienvenue {member.mention} 🎉 Va lire 📜-règles et clique sur ✅ pour accéder au serveur !")
        except: pass

# =========================================
#          SYNC & PRÉSENCE
# =========================================
@bot.event
async def on_ready():
    print(f"✅ Connecté comme {bot.user} (ID: {bot.user.id})")
    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"⚡ {len(synced)} commande(s) synchronisées sur la guilde {GUILD_ID}")
        else:
            synced = await bot.tree.sync()
            print(f"🌍 {len(synced)} commande(s) globales synchronisées")
    except Exception as e:
        print("❌ Erreur sync:", e)
    await bot.change_presence(activity=discord.Game(name="KAIHUB.fr • /help"))

# =========================================
#           ENREGISTREMENTS
# =========================================
bot.tree.add_command(ping)
bot.tree.add_command(say)
bot.tree.add_command(remind)
bot.tree.add_command(help_cmd)
bot.tree.add_command(userinfo)
bot.tree.add_command(serverinfo)
bot.tree.add_command(avatar)
bot.tree.add_command(quote)
bot.tree.add_command(clear)
bot.tree.add_command(kick)
bot.tree.add_command(ban)
bot.tree.add_command(load_setup)
bot.tree.add_command(setup_verify)
bot.tree.add_command(prsalon)

# =========================================
#               RUN
# =========================================
if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("❌ DISCORD_TOKEN manquant dans .env")
    bot.run(TOKEN)
