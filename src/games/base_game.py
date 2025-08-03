import discord
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseGame(ABC):
    """Base class for all games in the bot"""
    
    def __init__(self, channel_id: int, creator_id: str, creator_name: str, game_type: str):
        self.channel_id = channel_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.game_type = game_type
        self.state = "waiting"  # waiting, playing, finished
        self.created_at = datetime.now()
        self.players: List[Dict] = []
        self.max_players = 4
        self.min_players = 2
        
        logger.info(f"🎮 Created new {game_type} game in channel {channel_id} by {creator_name}")
    
    @abstractmethod
    def add_player(self, user_id: str, name: str) -> bool:
        """Add a player to the game"""
        pass
    
    @abstractmethod
    def start_game(self):
        """Start the game"""
        pass
    
    @abstractmethod
    def end_game(self, reason: str = "Game ended"):
        """End the game"""
        pass
    
    @abstractmethod
    def get_game_state_embed(self) -> discord.Embed:
        """Get current game state as embed"""
        pass
    
    @abstractmethod
    async def handle_interaction(self, interaction: discord.Interaction, bot) -> bool:
        """Handle Discord UI interactions"""
        pass
    
    def get_player(self, user_id: str) -> Optional[Dict]:
        """Get player by user ID"""
        return next((p for p in self.players if p['id'] == user_id), None)
    
    def is_player_in_game(self, user_id: str) -> bool:
        """Check if user is in the game"""
        return self.get_player(user_id) is not None
    
    def is_game_full(self) -> bool:
        """Check if game is full"""
        return len(self.players) >= self.max_players
    
    def can_start(self) -> bool:
        """Check if game can start"""
        return len(self.players) >= self.min_players and self.state == "waiting"
    
    def get_players_list(self) -> str:
        """Get formatted players list"""
        if not self.players:
            return "No players"
        
        players_list = []
        for i, player in enumerate(self.players):
            bot_icon = "🤖" if player.get('is_bot', False) else "👤"
            players_list.append(f"{i+1}. {bot_icon} {player['name']}")
        
        return "\n".join(players_list)
    
    def get_game_info(self) -> Dict[str, Any]:
        """Get basic game information"""
        return {
            'type': self.game_type,
            'state': self.state,
            'players_count': len(self.players),
            'max_players': self.max_players,
            'created_at': self.created_at,
            'creator': self.creator_name
        } 