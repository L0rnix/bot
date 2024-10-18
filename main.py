import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone
import os
import sys
import aiohttp 
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configurez l'accès à Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets"]
creds = ServiceAccountCredentials.from_json_keyfile_name('emhfrance-c9ed939b57b4.json', scope)
client = gspread.authorize(creds)

# Ouvrir la feuille de calcul
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1sdv91bJ51PMeewBZYV_hGDgYsB0Xgt9JTkEb702_bpk/edit?usp=sharing").sheet1


# Initialisation des intents pour permettre au bot de lire les messages
intents = discord.Intents.default()
intents.messages = True  # Pour lire les messages
intents.guilds = True  # Pour gérer les serveurs (guilds)
intents.message_content = True  # Pour accéder au contenu des messages

# Configuration du bot avec un préfixe vide et intents
bot = commands.Bot(command_prefix="/!", intents=intents)

# ID de l'utilisateur autorisé à redémarrer le bot
Owner_id = 1282360757820063836
Admin_role_id = 1291429577612071044  # ID du rôle admin
Ban_channel_id = 1293896335203897396  # ID du canal spécifique pour les rapports manuels

# Événement déclenché lorsque le bot est prêt
@bot.event
async def on_ready():
    await bot.tree.sync()  # Synchroniser les commandes de type slash
    print(f'Logged in as {bot.user}')

    # Envoie un message indiquant que le bot est prêt
    channel = bot.get_channel(1295494514252845056)  # Remplacez par l'ID du canal où vous voulez envoyer le message
    await channel.send(f"{bot.user.name} est prêt.")

@bot.tree.command(name="scan", description="Scan test")
async def scan(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)  # Répondre avec un message d'attente
    
    now = datetime.now(timezone.utc)  # Utilisation de datetime avec fuseau horaire UTC
    past_24h = now - timedelta(days=1)  # Calcul de la date et heure il y a 24h
    message_count = 0
    user_message_counts = {}

    # Parcourt tous les canaux texte du serveur
    for channel in interaction.guild.text_channels:
        try:
            # Parcourt l'historique des messages du canal
            async for message in channel.history(limit=None, after=past_24h):
                # Ignore les messages envoyés par les bots
                if message.author.bot:
                    continue

                message_count += 1
                if message.author not in user_message_counts:
                    user_message_counts[message.author] = 1
                else:
                    user_message_counts[message.author] += 1
        except Exception as e:
            print(f"Erreur lors de la récupération des messages dans {channel.name}: {e}")

    # Vérifie si aucun message n'a été trouvé
    if message_count == 0:
        await interaction.followup.send("Il n'y a pas de messages dans les dernières 24 heures sur le serveur.")
        return

    # Trouve l'utilisateur ayant envoyé le plus de messages
    top_user = max(user_message_counts, key=user_message_counts.get)
    top_user_count = user_message_counts[top_user]

    # Crée un embed pour le résultat
    embed = discord.Embed(title="Statistiques des Messages",
                          description="Voici les statistiques des messages des dernières 24 heures :",
                          color=0xff0000)  # Choisir une couleur

    # Ajoute des champs à l'embed
    embed.add_field(name="Nombre total de messages", value=message_count, inline=False)
    embed.add_field(name="Top utilisateur", value=f"{top_user} avec {top_user_count} messages", inline=False)

    # Envoie l'embed en réponse
    try:
        await interaction.followup.send(embed=embed)
    except discord.HTTPException as e:
        print(f"Erreur lors de l'envoi de l'embed: {e}")
        await interaction.followup.send("Une erreur s'est produite lors de l'envoi des statistiques. Veuillez réessayer.")

            

# Commande slash pour redémarrer le bot
@bot.tree.command(name="restart", description="Redémarre le bot.")
async def restart(interaction: discord.Interaction):
    # Vérifie si l'utilisateur est autorisé
    if interaction.user.id != Owner_id:
        await interaction.response.send_message("Vous n'avez pas l'autorisation de redémarrer le bot.", ephemeral=True)
        return

    await interaction.response.send_message("Redémarrage du bot...", ephemeral=True)
    
    # Redémarrage du bot
    os.execv(sys.executable, ['python'] + sys.argv)

# Fonction pour obtenir des informations d'un utilisateur Roblox
async def get_roblox_user_info(username: str):
    url = f"https://users.roblox.com/v1/users/search?keyword={username}"
    async with aiohttp.ClientSession() as session:
        for attempt in range(2):  # Maximum 2 tentatives
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data']:
                        user_info = data['data'][0]
                        return user_info['id'], user_info['displayName']  # Renvoie l'ID et le nom affiché
                    else:
                        return None, None  # Aucun utilisateur trouvé
                elif response.status == 429:  # Trop de requêtes
                    print("Erreur de requête: 429. Attente avant de réessayer.")
                    await asyncio.sleep(1)  # Attendre 1 seconde avant de réessayer
                else:
                    print(f"Erreur de requête: {response.status}")
                    return None, None  # Autre erreur de requête
    return None, None  # Retourner None si toutes les tentatives échouent

# Événement pour traiter les messages envoyés dans le canal spécifique
@bot.event
async def on_message(message):
    # Ignore les messages envoyés par des bots
    if message.author.bot:
        return
    
    # Vérifie si le message provient du canal spécifique
    if message.channel.id == Ban_channel_id:
        content = message.content.strip()

        # Vérifie si le message correspond au format attendu
        if ("Pseudo" in content and "Raison" in content) and ("Durée" in content or "Duration" in content):
            # Extraire les informations du message
            lines = content.splitlines()
            pseudo = ""
            duration = ""
            reason = ""
            roblox_id = ""

            for line in lines:
                if "Pseudo" in line:
                    pseudo = line.split(":", 1)[1].strip()
                elif "Durée" in line or "Duration" in line:
                    duration = line.split(":", 1)[1].strip()
                elif "Raison" in line or "Reason" in line:
                    reason = line.split(":", 1)[1].strip()
                elif "ID" in line:
                    roblox_id = line.split(":", 1)[1].strip() if ":" in line else ""

            # Si toutes les informations sont présentes
            if pseudo and duration and reason:
                # Enregistre le rapport dans Google Sheets
                row = [pseudo, duration, reason, message.author.display_name, "", roblox_id]
                sheet.append_row(row)

                # Répondre pour confirmer l'ajout dans Google Sheets
                await message.channel.send(f"Le rapport pour **{pseudo}** a été ajouté a la BDD")
    
    # Ne pas oublier de permettre aux autres commandes de fonctionner
    await bot.process_commands(message)

# Commande slash pour générer un rapport de bannissement
@bot.tree.command(name="rapport", description="Génère un rapport de bannissement.")
@app_commands.describe(username="Nom d'utilisateur Roblox", duration="La durée du bannissement", reason="La raison du bannissement")
async def rapport(interaction: discord.Interaction, username: str, duration: str, reason: str):
    
    # Vérifie si l'utilisateur a le rôle admin
    if not any(role.id == Admin_role_id for role in interaction.user.roles):
        await interaction.response.send_message("Vous n'avez pas l'autorisation de générer un rapport.", ephemeral=True)
        return  

    await interaction.response.defer(thinking=True)  # Défer la réponse en attendant

    # Nettoyer le nom d'utilisateur
    username = username.strip()

    # Vérifier combien de fois l'utilisateur a été banni (dans Google Sheets)
    bans = sheet.col_values(1)  # Récupère la colonne des noms d'utilisateurs bannis
    ban_count = bans.count(username)  # Compte le nombre d'occurrences du pseudo

    if ban_count > 1:  # Si l'utilisateur a déjà été banni plusieurs fois
        # Envoyer un message privé à l'utilisateur qui a envoyé le rapport
        try:
            await interaction.user.send(f"L'utilisateur **{username}** a déjà été banni plusieurs fois. Veuillez appliquer un bannissement permanent.")
            # Message dans le chat
            await interaction.response.send_message(f"<@{interaction.user.id}>, **{username}** a déjà été banni plusieurs fois. Veuillez appliquer un bannissement permanent.", delete_after=300)
        except discord.Forbidden:
            # Si l'utilisateur a désactivé les DMs, renvoie juste dans le canal
            await interaction.response.send_message(f"<@{interaction.user.id}>, **{username}** a déjà été banni plusieurs fois. Veuillez appliquer un bannissement permanent.", delete_after=300)

        # Terminer la commande sans enregistrer un nouveau rapport
        return

    elif ban_count == 1:  # Si l'utilisateur a déjà été banni une fois
        # Envoyer un message privé à l'utilisateur qui a envoyé le rapport
        try:
            await interaction.user.send(f"L'utilisateur **{username}** a déjà été banni. Veuillez appliquer un bannissement permanent.")
            # Message dans le chat
            await interaction.response.send_message(f"<@{interaction.user.id}>, **{username}** a déjà été banni. Veuillez appliquer un bannissement permanent.", delete_after=300)
        except discord.Forbidden:
            # Si l'utilisateur a désactivé les DMs, renvoie juste dans le canal
            await interaction.response.send_message(f"<@{interaction.user.id}>, **{username}** a déjà été banni. Veuillez appliquer un bannissement permanent.", delete_after=300)

        # Terminer la commande sans enregistrer un nouveau rapport
        return

    # Essayer d'obtenir l'ID et le nom affiché Roblox, avec un maximum de 2 tentatives
    roblox_id, display_name = await get_roblox_user_info(username)

    # Si aucune info n'a été récupérée après 2 tentatives, utiliser None pour roblox_id et display_name
    if roblox_id is None and display_name is None:
        roblox_id = None
        display_name = None

    # Vérifiez si la durée est un nombre
    duration_with_days = f"{duration} jours" if duration.isdigit() else "Permanent"

    # Crée un embed avec les informations du rapport
    embed = discord.Embed(title="Rapport de Bannissement", color=0xff0000)
    
    if display_name and roblox_id:
        embed.add_field(name="Utilisateur Roblox", value=f"{username} (`{display_name}`) (ID: {roblox_id})", inline=False)
    else:
        embed.add_field(name="Utilisateur Roblox", value=f"{username}", inline=False)

    embed.add_field(name="Durée", value=duration_with_days, inline=False)
    embed.add_field(name="Raison", value=reason, inline=False)
    
    # Ajouter le pseudo de l'utilisateur qui a généré le rapport
    embed.set_footer(text=f"Rapporté par: {interaction.user.display_name}", icon_url=interaction.user.avatar.url)

    # Enregistre le rapport dans Google Sheets
    row = [username, duration_with_days, reason, interaction.user.display_name, display_name or '', roblox_id or '']
    sheet.append_row(row)

    # Envoyer un message confirmant l'ajout du rapport à la base de données
    await interaction.response.send_message(f"Le rapport pour **{username}** a été ajouté à la BDD.", delete_after=300)

    # Envoie l'embed dans le chat
    await interaction.followup.send(embed=embed)
    
# Commande slash pour stopper le bot
@bot.tree.command(name="stop", description="Stoppe le bot.")
async def stop(interaction: discord.Interaction):
    # Vérifie si l'utilisateur est autorisé
    if interaction.user.id != Owner_id:
        await interaction.response.send_message("Vous n'avez pas l'autorisation de stopper le bot.", ephemeral=True)
        return

    await interaction.response.send_message("Arrêt du bot...", ephemeral=True)
    
    # Arrêt du bot
    sys.exit()


# Lancer le bot avec ton token
bot.run('MTI5NTQ5MjQ3OTk2OTI2Nzc5NA.GrKd-F.1kcuaKOlHXRaAkpVuIKRx6FaQItrTmv2JBkFK4')
