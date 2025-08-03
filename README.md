# 🎮 Jawaker Discord Bot

A comprehensive Discord bot that implements multiple card games and board games, starting with Syrian Tarneeb. Built for scalability to support many games like the popular Jawaker platform.

## 🎯 Features

- **Multi-Game Support**: Scalable architecture to support multiple game types
- **Complete Tarneeb Game**: Full implementation of Syrian Tarneeb with bidding, trump selection, and trick-taking
- **AI Players**: Smart bot players that can bid and play strategically
- **Interactive UI**: Button-based interface for bidding, card selection, and game management
- **Team Play**: 2v2 team format with proper scoring system
- **Slash Commands**: Modern Discord slash commands for all game functions
- **Comprehensive Logging**: Detailed logging with emoji-enhanced messages
- **Game Manager**: Centralized game management across multiple channels

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd JawlaBot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the bot**
   ```bash
   # Copy the example environment file
   cp config/env_example.txt config/.env
   
   # Edit config/.env and add your Discord bot token
   DISCORD_TOKEN=your_actual_bot_token_here
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## 🎮 How to Play

### Starting a Game

1. Use `/start <game_type>` to create a new game (e.g., `/start tarneeb`)
2. Other players use `/join` to join
3. Game automatically starts when minimum players join (bots fill empty slots)

### Game Commands

- `/start <game_type>` - Create a new game (e.g., `/start tarneeb`)
- `/join` - Join an existing game
- `/hand` - View your cards (sent via DM)
- `/game_state` - Show current game status
- `/scores` - Show team scores
- `/rules [game_type]` - Show game rules
- `/games` - Show all available game types
- `/stats` - Show bot statistics
- `/stop` - Stop game (creator only)
- `/end` - End game (any player)

### Available Games

- **Tarneeb**: Syrian Tarneeb - 4-player team card game with bidding and trump selection

## 🏗️ Project Structure

```
JawlaBot/
├── main.py                 # Main bot entry point
├── src/
│   ├── game_manager.py     # Centralized game management
│   ├── games/              # All game implementations
│   │   ├── base_game.py    # Base game class
│   │   └── tarneeb/        # Tarneeb game package
│   │       ├── tarneeb_game.py    # Main game logic
│   │       ├── player.py          # Player and AI classes
│   │       ├── card_ui.py         # UI components
│   │       └── game_state_embed.py # Discord embeds
│   └── commands/          # Slash command modules
│       ├── game_commands.py   # Game management commands
│       └── info_commands.py   # Info and utility commands
├── config/
│   └── env_example.txt    # Environment configuration template
├── logs/                  # Log files (created automatically)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🎯 Game Rules

### Tarneeb

#### Objective
First team to reach 31 points wins!

#### Teams
- **Team 1**: Players 1 & 3
- **Team 2**: Players 2 & 4

#### Bidding
- Players bid on how many tricks their team can win (1-7)
- Highest bidder chooses the tarneeb (trump) suit
- Must bid higher than current bid or pass

#### Playing
- Must follow suit if possible
- Tarneeb (trump) cards beat all other suits
- Highest card of led suit wins (if no trump)
- Winner of trick leads next

#### Scoring
- If bidding team makes their bid: they get points equal to bid
- If they fail: other team gets points equal to bid
- First team to 31 points wins!

## 🤖 AI Players

The bot includes intelligent AI players that:
- Evaluate hand strength for bidding
- Choose optimal tarneeb suits
- Play cards strategically during tricks
- Follow suit rules and trump appropriately

## 📊 Logging

The bot includes comprehensive logging:
- Daily log files in `/logs` directory
- Emoji-enhanced log messages
- Error tracking and debugging information
- Game state and player action logging

## 🔧 Configuration

### Environment Variables

Create a `config/.env` file with:

```env
DISCORD_TOKEN=your_discord_bot_token_here
BOT_PREFIX=!
GAME_CHANNEL_NAME=🎮┃games
```

### Bot Permissions

Your Discord bot needs these permissions:
- Send Messages
- Use Slash Commands
- Send Messages in Threads
- Embed Links
- Attach Files
- Read Message History
- Add Reactions

## 🛠️ Development

### Adding New Games

The bot is designed to easily add new games:

1. **Create game package** in `src/games/<game_name>/`
2. **Inherit from BaseGame** class
3. **Implement required methods**:
   - `add_player()`
   - `start_game()`
   - `end_game()`
   - `get_game_state_embed()`
   - `handle_interaction()`
4. **Register game type** in `GameManager`
5. **Add game-specific commands** if needed

### Example Game Structure

```python
from src.games.base_game import BaseGame

class MyGame(BaseGame):
    def __init__(self, channel_id, creator_id, creator_name):
        super().__init__(channel_id, creator_id, creator_name, "my_game")
        self.max_players = 4
        self.min_players = 2
        # Game-specific initialization
    
    def add_player(self, user_id: str, name: str) -> bool:
        # Implementation
        pass
    
    def start_game(self):
        # Implementation
        pass
    
    # ... other required methods
```

### Adding New Commands

1. Create a new command function in `src/commands/`
2. Register it in the appropriate setup function
3. Import and call the setup function in `main.py`

## 🎯 Scalability Features

- **Game Manager**: Centralized management of all games
- **Base Game Class**: Consistent interface for all games
- **Modular Commands**: Easy to add game-specific commands
- **Type Safety**: Proper typing for all game components
- **Logging**: Comprehensive logging for debugging
- **Statistics**: Built-in game statistics and monitoring

## 📝 License

Created by Hamoodi © 2025 All Rights Reserved

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

**Enjoy playing with Jawaker Bot! 🎮** 