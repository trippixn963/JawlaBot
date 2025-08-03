import discord
from discord.ext import commands
import asyncio
import os
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Create daily log files
today = datetime.now().strftime("%Y-%m-%d")
log_file = logs_dir / f"logs.log"
error_file = logs_dir / f"errors.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.FileHandler(error_file, level=logging.ERROR),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

class JawakerBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.game_manager = None
        
    async def setup_hook(self):
        """Setup bot commands and sync with Discord"""
        logger.info("🚀 Setting up bot commands...")
        
        # Initialize game manager
        from src.game_manager import GameManager
        self.game_manager = GameManager()
        
        # Import and setup commands
        from src.commands.game_commands import setup_game_commands
        from src.commands.info_commands import setup_info_commands
        
        setup_game_commands(self.tree, self)
        setup_info_commands(self.tree, self)
        
        # Sync commands with Discord
        await self.tree.sync()
        logger.info("✅ Commands synced successfully")
    
    async def on_ready(self):
        """Bot ready event"""
        logger.info(f"🤖 Logged in as {self.user}")
        await self.change_presence(activity=discord.Game(name="Jawaker Bot - Created by Hamoodi © 2025"))
    
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle button interactions"""
        if interaction.type == discord.InteractionType.component:
            # Let game manager handle the interaction
            await self.game_manager.handle_interaction(interaction, self)

# Create bot instance
bot = JawakerBot()

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("❌ DISCORD_TOKEN environment variable not set!")
    else:
        logger.info("🚀 Starting Jawaker Bot...")
        bot.run(token) 