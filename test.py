import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone
import os
import sys

# Initialisation des intents pour permettre au bot de lire les messages
intents = discord.Intents.default()
intents.messages = True  # Pour lire les messages
intents.guilds = True  # Pour gérer les serveurs (guilds)
intents.message_content = True  # Pour accéder au contenu des messages

# Configuration du bot avec un préfixe vide et intents
bot = commands.Bot(command_prefix="", intents=intents)

# ID de l'utilisateur autorisé à redémarrer le bot
ALLOWED_USER_ID = 1282360757820063836

# Événement déclenché lorsque le bot est prêt
@bot.event
async def on_ready():
    await bot.tree.sync()  # Synchroniser les commandes de type slash
    print(f'Logged in as {bot.user}')

    # Envoie un message indiquant que le bot est prêt
    channel = bot.get_channel(1295494514252845056)  # Remplacez par l'ID du canal où vous voulez envoyer le message
    await channel.send(f"{bot.user.name} est prêt.")

# Commande slash pour scanner les messages des dernières 24 heures sur tout le serveur
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
                          color=0x00ff00)  # Choisir une couleur

    # Ajoute des champs à l'embed
    embed.add_field(name="Nombre total de messages", value=message_count, inline=False)
    embed.add_field(name="Top utilisateur", value=f"{top_user} avec {top_user_count} messages", inline=False)

    # Envoie l'embed en réponse
    await interaction.followup.send(embed=embed)

# Commande slash pour redémarrer le bot
@bot.tree.command(name="restart", description="Redémarre le bot.")
async def restart(interaction: discord.Interaction):
    # Vérifie si l'utilisateur est autorisé
    if interaction.user.id != ALLOWED_USER_ID:
        await interaction.response.send_message("Vous n'avez pas l'autorisation de redémarrer le bot.", ephemeral=True)
        return

    await interaction.response.send_message("Redémarrage du bot...", ephemeral=True)
    
    # Redémarrage du bot
    os.execv(sys.executable, ['python'] + sys.argv)

# Ignore toutes les commandes qui ne sont pas définies
@bot.event
async def on_command_error(ctx, error):
    # Ignore l'erreur de commande non trouvée
    if isinstance(error, commands.CommandNotFound):
        return

# Lancer le bot avec ton token
bot.run('MTI5NTQ5MjQ3OTk2OTI2Nzc5NA.GrKd-F.1kcuaKOlHXRaAkpVuIKRx6FaQItrTmv2JBkFK4')
