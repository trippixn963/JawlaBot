import discord
import logging
from typing import Dict, List, Optional, Type
from datetime import datetime

from .games.base_game import BaseGame
from .games.tarneeb.tarneeb_game import TarneebGame

logger = logging.getLogger(__name__)

class GameManager:
    """Manages all active games across the bot"""
    
    def __init__(self):
        self.active_games: Dict[int, BaseGame] = {}  # channel_id -> game
        self.game_types = {
            'tarneeb': TarneebGame
        }
        
        logger.info("🎮 Game Manager initialized")
    
    def create_game(self, game_type: str, channel_id: int, creator_id: str, creator_name: str) -> Optional[BaseGame]:
        """Create a new game of the specified type"""
        if game_type not in self.game_types:
            logger.error(f"❌ Unknown game type: {game_type}")
            return None
        
        if channel_id in self.active_games:
            logger.warning(f"⚠️ Game already exists in channel {channel_id}")
            return None
        
        # Create the game
        game_class = self.game_types[game_type]
        game = game_class(channel_id, creator_id, creator_name)
        self.active_games[channel_id] = game
        
        logger.info(f"🎮 Created {game_type} game in channel {channel_id}")
        return game
    
    def get_game(self, channel_id: int) -> Optional[BaseGame]:
        """Get game by channel ID"""
        return self.active_games.get(channel_id)
    
    def end_game(self, channel_id: int, reason: str = "Game ended") -> bool:
        """End a game in the specified channel"""
        if channel_id not in self.active_games:
            return False
        
        game = self.active_games[channel_id]
        game.end_game(reason)
        del self.active_games[channel_id]
        
        logger.info(f"🏁 Ended game in channel {channel_id}: {reason}")
        return True
    
    def get_active_games_count(self) -> int:
        """Get total number of active games"""
        return len(self.active_games)
    
    def get_games_by_type(self, game_type: str) -> List[BaseGame]:
        """Get all active games of a specific type"""
        return [game for game in self.active_games.values() if game.game_type == game_type]
    
    def get_user_games(self, user_id: str) -> List[BaseGame]:
        """Get all games where user is a player"""
        user_games = []
        for game in self.active_games.values():
            if game.is_player_in_game(user_id):
                user_games.append(game)
        return user_games
    
    def cleanup_finished_games(self):
        """Clean up games that have finished"""
        finished_channels = []
        for channel_id, game in self.active_games.items():
            if game.state == "finished":
                finished_channels.append(channel_id)
        
        for channel_id in finished_channels:
            del self.active_games[channel_id]
            logger.info(f"🧹 Cleaned up finished game in channel {channel_id}")
    
    def get_game_stats(self) -> Dict:
        """Get statistics about active games"""
        stats = {
            'total_games': len(self.active_games),
            'games_by_type': {},
            'games_by_state': {},
            'total_players': 0
        }
        
        for game in self.active_games.values():
            # Count by type
            game_type = game.game_type
            stats['games_by_type'][game_type] = stats['games_by_type'].get(game_type, 0) + 1
            
            # Count by state
            state = game.state
            stats['games_by_state'][state] = stats['games_by_state'].get(state, 0) + 1
            
            # Count total players
            stats['total_players'] += len(game.players)
        
        return stats
    
    async def handle_interaction(self, interaction: discord.Interaction, bot) -> bool:
        """Handle Discord UI interactions for all games"""
        channel_id = interaction.channel.id
        game = self.get_game(channel_id)
        
        if not game:
            return False
        
        # Try to handle the interaction
        return await game.handle_interaction(interaction, bot)
    
    def get_available_game_types(self) -> List[str]:
        """Get list of available game types"""
        return list(self.game_types.keys())
    
    def register_game_type(self, game_type: str, game_class: Type[BaseGame]):
        """Register a new game type"""
        self.game_types[game_type] = game_class
        logger.info(f"📝 Registered new game type: {game_type}")
    
    def get_game_info(self, channel_id: int) -> Optional[Dict]:
        """Get information about a specific game"""
        game = self.get_game(channel_id)
        if not game:
            return None
        
        return game.get_game_info() 