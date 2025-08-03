import discord
import logging
from discord import app_commands

logger = logging.getLogger(__name__)

def setup_info_commands(tree: discord.app_commands.CommandTree, bot):
    """Setup info-related slash commands"""
    
    @tree.command(name="game_state", description="Show current game state")
    async def show_game_state(interaction: discord.Interaction):
        """Show current game state"""
        channel_id = interaction.channel.id
        
        game = bot.game_manager.get_game(channel_id)
        if not game:
            await interaction.response.send_message("❌ No game is running in this channel!", ephemeral=True)
            return
        
        embed = game.get_game_state_embed()
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="scores", description="Show current team scores")
    async def show_scores(interaction: discord.Interaction):
        """Show current team scores"""
        channel_id = interaction.channel.id
        
        game = bot.game_manager.get_game(channel_id)
        if not game:
            await interaction.response.send_message("❌ No game is running in this channel!", ephemeral=True)
            return
        
        # Game-specific score display
        if game.game_type == "tarneeb":
            from src.games.tarneeb.game_state_embed import GameStateEmbed
            embed = GameStateEmbed.create_scores_embed(game)
        else:
            embed = discord.Embed(
                title="🏆 Scores",
                description="Score display not implemented for this game type",
                color=0xffd700
            )
        
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="rules", description="Show game rules")
    @app_commands.describe(game_type="Type of game to show rules for")
    async def show_rules(interaction: discord.Interaction, game_type: str = None):
        """Show game rules"""
        # If no game type specified, check current channel
        if not game_type:
            channel_id = interaction.channel.id
            game = bot.game_manager.get_game(channel_id)
            if game:
                game_type = game.game_type
            else:
                available_games = ", ".join(bot.game_manager.get_available_game_types())
                await interaction.response.send_message(
                    f"❌ No game running in this channel! Specify a game type or use `/rules <game_type>`. Available games: {available_games}", 
                    ephemeral=True
                )
                return
        
        # Game-specific rules
        if game_type == "tarneeb":
            embed = discord.Embed(
                title="📋 Tarneeb Rules",
                description="Syrian Tarneeb card game rules",
                color=0x0099ff
            )
            
            embed.add_field(
                name="🎯 Objective",
                value="First team to reach 31 points wins!",
                inline=False
            )
            
            embed.add_field(
                name="👥 Teams",
                value="4 players in 2 teams:\n• Team 1: Players 1 & 3\n• Team 2: Players 2 & 4",
                inline=False
            )
            
            embed.add_field(
                name="💰 Bidding",
                value="Players bid on how many tricks their team can win (1-7).\nHighest bidder chooses the tarneeb (trump) suit.",
                inline=False
            )
            
            embed.add_field(
                name="🃏 Playing",
                value="• Must follow suit if possible\n• Tarneeb (trump) cards beat all other suits\n• Highest card of led suit wins (if no trump)\n• Winner of trick leads next",
                inline=False
            )
            
            embed.add_field(
                name="📊 Scoring",
                value="• If bidding team makes their bid: they get points equal to bid\n• If they fail: other team gets points equal to bid\n• First team to 31 points wins!",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="📋 Game Rules",
                description=f"Rules for {game_type.title()}",
                color=0x0099ff
            )
            embed.add_field(
                name="Not Available",
                value=f"Rules for {game_type.title()} are not available yet.",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="stats", description="Show bot statistics")
    async def show_stats(interaction: discord.Interaction):
        """Show bot statistics"""
        stats = bot.game_manager.get_game_stats()
        
        embed = discord.Embed(
            title="📊 Bot Statistics",
            description="Current bot activity",
            color=0x0099ff
        )
        
        embed.add_field(name="Total Active Games", value=str(stats['total_games']), inline=True)
        embed.add_field(name="Total Players", value=str(stats['total_players']), inline=True)
        
        # Games by type
        if stats['games_by_type']:
            games_by_type = "\n".join([f"• {game_type.title()}: {count}" for game_type, count in stats['games_by_type'].items()])
            embed.add_field(name="Games by Type", value=games_by_type, inline=False)
        
        # Games by state
        if stats['games_by_state']:
            games_by_state = "\n".join([f"• {state.title()}: {count}" for state, count in stats['games_by_state'].items()])
            embed.add_field(name="Games by State", value=games_by_state, inline=False)
        
        await interaction.response.send_message(embed=embed) 