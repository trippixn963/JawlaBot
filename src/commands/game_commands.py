import discord
import logging
from discord import app_commands
import asyncio

logger = logging.getLogger(__name__)

def setup_game_commands(tree: discord.app_commands.CommandTree, bot):
    """Setup game-related slash commands"""
    
    @tree.command(name="start", description="Start a new game")
    @app_commands.describe(
        game_type="Type of game to start",
        players="Number of players (optional, defaults to game minimum)"
    )
    async def start_game(interaction: discord.Interaction, game_type: str, players: int = None):
        """Start a new game"""
        channel_id = interaction.channel.id
        
        # Check if game already exists
        if bot.game_manager.get_game(channel_id):
            await interaction.response.send_message("❌ A game is already running in this channel!", ephemeral=True)
            return
        
        # Create new game
        game = bot.game_manager.create_game(game_type, channel_id, str(interaction.user.id), interaction.user.display_name)
        
        if not game:
            available_games = ", ".join(bot.game_manager.get_available_game_types())
            await interaction.response.send_message(
                f"❌ Unknown game type '{game_type}'! Available games: {available_games}", 
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"🎮 {game_type.title()} Game Created!",
            description=f"**{interaction.user.display_name}** started a new {game_type} game!",
            color=0x00ff00
        )
        
        embed.add_field(name="Players", value=f"1/{game.max_players} - {interaction.user.display_name}", inline=False)
        embed.add_field(name="How to Join", value=f"Use `/join` to join the game", inline=False)
        embed.add_field(name="How to Start", value=f"Game starts automatically when {game.min_players} players join, or creator uses `/start` with fewer players (bots will fill empty slots)", inline=False)
        
        logger.info(f"🎮 New {game_type} game created by {interaction.user.display_name} in channel {channel_id}")
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="join", description="Join an existing game")
    async def join_game(interaction: discord.Interaction):
        """Join an existing game"""
        channel_id = interaction.channel.id
        
        game = bot.game_manager.get_game(channel_id)
        if not game:
            available_games = ", ".join(bot.game_manager.get_available_game_types())
            await interaction.response.send_message(
                f"❌ No game is running in this channel! Use `/start <game_type>` to create one. Available games: {available_games}", 
                ephemeral=True
            )
            return
        
        if game.state != "waiting":
            await interaction.response.send_message("❌ Game has already started!", ephemeral=True)
            return
        
        if game.add_player(str(interaction.user.id), interaction.user.display_name):
            player_count = len(game.players)
            players_list = game.get_players_list()
            
            embed = discord.Embed(
                title="✅ Player Joined!",
                description=f"**{interaction.user.display_name}** joined the {game.game_type} game!",
                color=0x00ff00
            )
            
            embed.add_field(name=f"Players ({player_count}/{game.max_players})", value=players_list, inline=False)
            
            if game.can_start():
                embed.add_field(name="Status", value="🎉 Game is ready to start!", inline=False)
                await interaction.response.send_message(embed=embed)
                
                # Auto-start if enough players
                if player_count >= game.min_players:
                    await asyncio.sleep(2)
                    game.start_game()
                    
                    # Show game-specific start message
                    if game.game_type == "tarneeb":
                        from src.games.tarneeb.game_state_embed import GameStateEmbed
                        team_embed = GameStateEmbed.create_teams_embed(game)
                        await interaction.channel.send(embed=team_embed)
                        
                        await asyncio.sleep(2)
                        await game.continue_bidding(interaction.channel, bot)
            else:
                embed.add_field(name="Status", value=f"Waiting for {game.min_players-player_count} more players...", inline=False)
                await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ You're already in this game or the game is full!", ephemeral=True)
    
    @tree.command(name="hand", description="Show your current hand (DM)")
    async def show_hand(interaction: discord.Interaction):
        """Show your current hand (DM)"""
        channel_id = interaction.channel.id
        
        game = bot.game_manager.get_game(channel_id)
        if not game:
            await interaction.response.send_message("❌ No game is running in this channel!", ephemeral=True)
            return
        
        player = game.get_player(str(interaction.user.id))
        
        if not player:
            await interaction.response.send_message("❌ You're not in this game!", ephemeral=True)
            return
        
        # Game-specific hand display
        if game.game_type == "tarneeb":
            from src.games.tarneeb.player import Player
            from src.games.tarneeb.card_ui import CardUI
            
            player_obj = game.get_player_object(str(interaction.user.id))
            if not player_obj or not player_obj.hand:
                await interaction.response.send_message("❌ You don't have any cards yet!", ephemeral=True)
                return
            
            # Send hand via DM
            try:
                hand_str = CardUI.format_hand(player_obj.hand)
                embed = discord.Embed(
                    title="🃏 Your Hand",
                    description=hand_str,
                    color=0x0099ff
                )
                
                if game.tarneeb_suit:
                    suit_names = {'♠': 'Spades', '♥': 'Hearts', '♦': 'Diamonds', '♣': 'Clubs'}
                    embed.add_field(name="Tarneeb Suit", value=f"{game.tarneeb_suit} {suit_names[game.tarneeb_suit]}", inline=True)
                
                await interaction.user.send(embed=embed)
                await interaction.response.send_message("📨 Your hand has been sent to your DMs!", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("❌ I can't send you a DM! Please enable DMs from server members.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Hand display not implemented for this game type!", ephemeral=True)
    
    @tree.command(name="stop", description="Stop the current game (creator only)")
    async def stop_game(interaction: discord.Interaction):
        """Stop the current game (creator only)"""
        channel_id = interaction.channel.id
        
        game = bot.game_manager.get_game(channel_id)
        if not game:
            await interaction.response.send_message("❌ No game is running in this channel!", ephemeral=True)
            return
        
        if str(interaction.user.id) != game.creator_id:
            await interaction.response.send_message("❌ Only the game creator can stop the game!", ephemeral=True)
            return
        
        bot.game_manager.end_game(channel_id, f"Stopped by {interaction.user.display_name}")
        
        embed = discord.Embed(
            title="🛑 Game Stopped",
            description=f"Game stopped by {interaction.user.display_name}",
            color=0xff0000
        )
        
        logger.info(f"🛑 Game stopped by {interaction.user.display_name} in channel {channel_id}")
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="end", description="End the current game (any player)")
    async def end_game_command(interaction: discord.Interaction):
        """End the current game (any player)"""
        channel_id = interaction.channel.id
        
        game = bot.game_manager.get_game(channel_id)
        if not game:
            await interaction.response.send_message("❌ No game is running in this channel!", ephemeral=True)
            return
        
        player = game.get_player(str(interaction.user.id))
        
        if not player:
            await interaction.response.send_message("❌ You're not in this game!", ephemeral=True)
            return
        
        bot.game_manager.end_game(channel_id, f"Ended by {interaction.user.display_name}")
        
        embed = discord.Embed(
            title="🏁 Game Ended",
            description=f"Game ended by {interaction.user.display_name}",
            color=0xff6600
        )
        
        if game.state in ["playing", "finished"] and hasattr(game, 'teams_scores') and any(game.teams_scores):
            embed.add_field(name="Final Scores", value=f"Team 1: {game.teams_scores[0]}\nTeam 2: {game.teams_scores[1]}", inline=False)
        
        logger.info(f"🏁 Game ended by {interaction.user.display_name} in channel {channel_id}")
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="games", description="Show all available game types")
    async def show_games(interaction: discord.Interaction):
        """Show all available game types"""
        available_games = bot.game_manager.get_available_game_types()
        
        embed = discord.Embed(
            title="🎮 Available Games",
            description="Here are all the games you can play:",
            color=0x0099ff
        )
        
        game_descriptions = {
            'tarneeb': 'Syrian Tarneeb - 4-player team card game with bidding and trump selection'
        }
        
        for game_type in available_games:
            description = game_descriptions.get(game_type, f"{game_type.title()} - Card game")
            embed.add_field(name=f"🎯 {game_type.title()}", value=description, inline=False)
        
        embed.add_field(name="How to Play", value="Use `/start <game_type>` to start a game", inline=False)
        
        await interaction.response.send_message(embed=embed) 