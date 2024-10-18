import discord
from discord.ext import commands
import aiohttp
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

# Configure l'accès à Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets"]
creds = ServiceAccountCredentials.from_json_keyfile_name('emhfrance-c9ed939b57b4.json', scope)
client = gspread.authorize(creds)

# Ouvrir la feuille de calcul
sheet_url = "https://docs.google.com/spreadsheets/d/1sdv91bJ51PMeewBZYV_hGDgYsB0Xgt9JTkEb702_bpk/edit?usp=sharing"
try:
    sheet = client.open_by_url(sheet_url).sheet1
except Exception as e:
    print(f"Erreur lors de l'ouverture de la feuille de calcul : {e}")

# Initialisation des intents pour permettre au bot de lire les messages
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Configuration du bot
bot = commands.Bot(command_prefix="", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    channel = bot.get_channel(1295494514252845056)  # Remplace par l'ID du canal
    await channel.send(f"{bot.user.name} est prêt.")

# Fonction pour extraire les informations de bannissement
def extract_ban_info(message_content):
    # Séparation par ligne pour traiter chaque ligne individuellement
    lines = message_content.splitlines()
    ban_info = {}
    
    for line in lines:
        # Séparer la ligne par le caractère ":"
        if ":" in line:
            key, value = line.split(":", 1)  # Limiter la séparation à 1
            key = key.strip()  # Supprimer les espaces autour de la clé
            value = value.strip()  # Supprimer les espaces autour de la valeur
            
            if key.lower() == "pseudo":
                ban_info["Pseudo"] = value
            elif key.lower() == "duration":
                ban_info["Duration"] = value
            elif key.lower() == "raison":
                ban_info["Raison"] = value

    return ban_info

# Fonction pour enregistrer les informations dans Google Sheets
def save_to_google_sheets(ban_info):
    try:
        # Supprime les espaces des deux premiers champs
        pseudo = ban_info.get("Pseudo", "").replace(" ", "")
        duration = ban_info.get("Duration", "").replace(" ", "")
        raison = ban_info.get("Raison", "")

        # Ajoute les informations aux colonnes appropriées
        row = [pseudo, duration, raison]
        sheet.append_row(row)
        print(f"Informations enregistrées : {row}")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement dans Google Sheets : {e}")

@bot.command(name='process_bans')
async def process_bans(ctx):
    channel_id = 1293896335203897396  # Remplace par l'ID du salon à lire
    channel = bot.get_channel(channel_id)

    if not channel:
        await ctx.send("Canal introuvable.")
        return

    # Parcourt l'historique des messages du canal
    async for message in channel.history(limit=100):  # Change `limit` si nécessaire
        if message.author.bot:
            continue

        # Affiche le contenu du message pour le débogage
        print(f"Contenu du message : {message.content}")

        # Extraction des informations de bannissement
        ban_info = extract_ban_info(message.content)

        # Affichage des informations extraites dans la console
        print(f"Pseudo: {ban_info.get('Pseudo', 'Non spécifié')}")
        print(f"Duration: {ban_info.get('Duration', 'Non spécifié')}")
        print(f"Raison: {ban_info.get('Raison', 'Non spécifié')}")
        print("-" * 30)

        # Enregistrement des informations dans Google Sheets
        save_to_google_sheets(ban_info)

    await ctx.send("Traitement des bans terminé.")

# Lancer le bot avec ton token
bot.run('MTI5NTQ5MjQ3OTk2OTI2Nzc5NA.GrKd-F.1kcuaKOlHXRaAkpVuIKRx6FaQItrTmv2JBkFK4')
