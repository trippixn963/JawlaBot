import discord
from typing import List

class GameStateEmbed:
    """Create embeds for game state display"""
    
    @staticmethod
    def create_teams_embed(game) -> discord.Embed:
        """Create embed showing team composition"""
        embed = discord.Embed(
            title="👥 Team Composition",
            color=0x00ff00
        )
        
        team1_players = [game.player_objects[0].name, game.player_objects[2].name]
        team2_players = [game.player_objects[1].name, game.player_objects[3].name]
        
        embed.add_field(
            name="🔵 Team 1",
            value="\n".join([f"{'🤖' if game.player_objects[0].is_bot else '👤'} {team1_players[0]}", 
                           f"{'🤖' if game.player_objects[2].is_bot else '👤'} {team1_players[1]}"]),
            inline=True
        )
        
        embed.add_field(
            name="🔴 Team 2",
            value="\n".join([f"{'🤖' if game.player_objects[1].is_bot else '👤'} {team2_players[0]}", 
                           f"{'🤖' if game.player_objects[3].is_bot else '👤'} {team2_players[1]}"]),
            inline=True
        )
        
        return embed
    
    @staticmethod
    def create_game_state_embed(game) -> discord.Embed:
        """Create embed showing current game state"""
        embed = discord.Embed(
            title="🎮 Game State",
            color=0x0099ff
        )
        
        embed.add_field(name="Round", value=str(game.round_number), inline=True)
        embed.add_field(name="State", value=game.state.title(), inline=True)
        
        if game.current_bid > 0:
            embed.add_field(name="Current Bid", value=f"{game.current_bid} tricks", inline=True)
            
        if game.highest_bidder:
            embed.add_field(name="Highest Bidder", value=game.highest_bidder.name, inline=True)
            
        if game.tarneeb_suit:
            suit_names = {'♠': 'Spades', '♥': 'Hearts', '♦': 'Diamonds', '♣': 'Clubs'}
            embed.add_field(name="Tarneeb Suit", value=f"{game.tarneeb_suit} {suit_names[game.tarneeb_suit]}", inline=True)
        
        # Show current turn
        if game.state in ["bidding", "playing"]:
            current_player = game.player_objects[game.current_turn_index]
            embed.add_field(name="Current Turn", value=f"{'🤖' if current_player.is_bot else '👤'} {current_player.name}", inline=True)
        
        return embed
    
    @staticmethod
    def create_scores_embed(game) -> discord.Embed:
        """Create embed showing team scores"""
        embed = discord.Embed(
            title="🏆 Team Scores",
            color=0xffd700
        )
        
        embed.add_field(name="🔵 Team 1", value=str(game.teams_scores[0]), inline=True)
        embed.add_field(name="🔴 Team 2", value=str(game.teams_scores[1]), inline=True)
        embed.add_field(name="Target", value="31 points", inline=True)
        
        # Show individual trick counts if in playing phase
        if game.state == "playing" and any(game.tricks_won.values()):
            tricks_text = []
            for i, player in enumerate(game.player_objects):
                team_color = "🔵" if i % 2 == 0 else "🔴"
                bot_icon = "🤖" if player.is_bot else "👤"
                tricks_text.append(f"{team_color} {bot_icon} {player.name}: {game.tricks_won.get(player.id, 0)}")
            
            embed.add_field(name="Tricks Won This Round", value="\n".join(tricks_text), inline=False)
        
        return embed
    
    @staticmethod
    def create_playing_embed(game, current_player) -> discord.Embed:
        """Create embed for playing phase"""
        embed = discord.Embed(
            title="🃏 Playing Phase",
            description=f"**{current_player.name}**'s turn to play",
            color=0x0099ff
        )
        
        suit_names = {'♠': 'Spades', '♥': 'Hearts', '♦': 'Diamonds', '♣': 'Clubs'}
        
        if game.lead_suit:
            embed.add_field(name="Lead Suit", value=f"{game.lead_suit} {suit_names[game.lead_suit]}", inline=True)
        
        embed.add_field(name="Tarneeb Suit", value=f"{game.tarneeb_suit} {suit_names[game.tarneeb_suit]}", inline=True)
        
        # Show cards played in current trick
        if game.played_cards:
            cards_played = []
            for player, card in game.played_cards:
                card_str = f"{card[0]}{card[1]}"
                cards_played.append(f"**{player.name}**: {card_str}")
            
            embed.add_field(name="Cards Played", value="\n".join(cards_played), inline=False)
        
        if not current_player.is_bot:
            embed.add_field(name="Instructions", value="Click 'Show My Cards' button to see your options", inline=False)
        
        return embed
    
    @staticmethod
    def create_round_end_embed(game, result_msg: str, team_tricks: List[int]) -> discord.Embed:
        """Create embed for round end results"""
        embed = discord.Embed(
            title="🏁 Round Complete",
            description=result_msg,
            color=0x00ff00
        )
        
        embed.add_field(name="Bid", value=f"{game.current_bid} tricks by {game.highest_bidder.name}", inline=False)
        embed.add_field(name="Team 1 Tricks", value=str(team_tricks[0]), inline=True)
        embed.add_field(name="Team 2 Tricks", value=str(team_tricks[1]), inline=True)
        embed.add_field(name="Total Tricks", value="13", inline=True)
        
        embed.add_field(name="Updated Scores", value=f"Team 1: {game.teams_scores[0]}\nTeam 2: {game.teams_scores[1]}", inline=False)
        
        return embed 