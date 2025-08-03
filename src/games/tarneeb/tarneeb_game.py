import discord
import random
import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..base_game import BaseGame
from .player import Player, AIPlayer
from .card_ui import CardUI
from .game_state_embed import GameStateEmbed

logger = logging.getLogger(__name__)

# Card definitions
SUITS = ["♠", "♣", "♥", "♦"]
SUIT_NAMES = {"♠": "Spades", "♣": "Clubs", "♥": "Hearts", "♦": "Diamonds"}
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

class TarneebGame(BaseGame):
    """Tarneeb card game implementation"""
    
    def __init__(self, channel_id: int, creator_id: str, creator_name: str):
        super().__init__(channel_id, creator_id, creator_name, "Tarneeb")
        self.max_players = 4
        self.min_players = 4
        
        # Tarneeb-specific attributes
        self.round_number = 1
        self.current_bid = 0
        self.highest_bidder: Optional[Player] = None
        self.bidding_turn = 0
        self.passes_count = 0
        self.current_turn_index = 0
        self.tricks_won = {}
        self.teams_scores = [0, 0]
        self.tarneeb_suit: Optional[str] = None
        self.played_cards = []  # List of (player, card) tuples
        self.lead_suit: Optional[str] = None
        self.deck = []
        self.waiting_for_card_from: Optional[str] = None
        self.current_card_view: Optional[discord.ui.View] = None
        self.current_ephemeral_embed: Optional[discord.Embed] = None
        
        # Convert players list to Player objects
        self.player_objects: List[Player] = []
    
    def add_player(self, user_id: str, name: str) -> bool:
        """Add a player to the game"""
        if self.is_game_full():
            return False
        if self.is_player_in_game(user_id):
            return False
        
        # Add to players list
        player_data = {
            'id': user_id,
            'name': name,
            'is_bot': False,
            'joined_at': datetime.now()
        }
        self.players.append(player_data)
        
        # Create Player object
        player_obj = Player(user_id, name)
        self.player_objects.append(player_obj)
        
        logger.info(f"👤 Player {name} joined Tarneeb game in channel {self.channel_id}")
        return True
    
    def start_game(self):
        """Start the game with current players + bots"""
        # Fill remaining slots with bots
        bot_names = ["🤖 Ahmad", "🤖 Sara", "🤖 Omar", "🤖 Layla"]
        used_bot_names = []
        
        while len(self.players) < 4:
            available_names = [name for name in bot_names if name not in used_bot_names]
            if not available_names:
                available_names = [f"🤖 Bot{len(self.players)}"]
            
            bot_name = random.choice(available_names)
            used_bot_names.append(bot_name)
            bot_id = f"bot_{len(self.players)}"
            
            # Add bot to players list
            bot_data = {
                'id': bot_id,
                'name': bot_name,
                'is_bot': True,
                'joined_at': datetime.now()
            }
            self.players.append(bot_data)
            
            # Create Player object for bot
            bot_player = Player(bot_id, bot_name, is_bot=True)
            self.player_objects.append(bot_player)
        
        # Initialize game state
        self.state = "bidding"
        self.deal_cards()
        self.bidding_turn = 0
        self.current_turn_index = 0
        
        # Initialize tricks won tracking
        for player in self.player_objects:
            self.tricks_won[player.id] = 0
        
        logger.info(f"🎮 Tarneeb game started in channel {self.channel_id} with {len(self.players)} players")
    
    def deal_cards(self):
        """Deal 13 cards to each player"""
        # Create and shuffle deck
        self.deck = [(rank, suit) for suit in SUITS for rank in RANKS]
        random.shuffle(self.deck)
        
        # Deal cards
        for i, card in enumerate(self.deck):
            player_index = i % 4
            self.player_objects[player_index].add_card(card)
        
        logger.info(f"🃏 Dealt cards to {len(self.player_objects)} players")
    
    def get_player_object(self, user_id: str) -> Optional[Player]:
        """Get Player object by user ID"""
        return next((p for p in self.player_objects if p.id == user_id), None)
    
    def end_game(self, reason: str = "Game ended"):
        """End the game"""
        self.state = "finished"
        logger.info(f"🏁 Tarneeb game ended in channel {self.channel_id}: {reason}")
    
    def get_game_state_embed(self) -> discord.Embed:
        """Get current game state as embed"""
        return GameStateEmbed.create_game_state_embed(self)
    
    async def handle_interaction(self, interaction: discord.Interaction, bot) -> bool:
        """Handle Discord UI interactions"""
        if interaction.data.get("custom_id", "").startswith("bid_"):
            bid_value = int(interaction.data["custom_id"].split("_")[1])
            await self.handle_bid(interaction, bid_value, bot)
            return True
        elif interaction.data.get("custom_id") == "pass":
            await self.handle_pass(interaction, bot)
            return True
        elif interaction.data.get("custom_id", "").startswith("tarneeb_"):
            suit = interaction.data["custom_id"].split("_")[1]
            player = self.get_player_object(interaction.user.id)
            if player == self.highest_bidder:
                await interaction.response.send_message("Tarneeb suit selected!", ephemeral=True)
                await self.set_tarneeb_suit(interaction.channel, bot, suit, player)
                return True
            else:
                await interaction.response.send_message("Only the highest bidder can choose the tarneeb suit!", ephemeral=True)
                return True
        elif interaction.data.get("custom_id", "").startswith("show_my_cards_"):
            # Handle showing cards to current player
            player_id_from_button = interaction.data["custom_id"].split("_")[-1]
            player = self.get_player_object(interaction.user.id)
            
            if player and str(player.id) == player_id_from_button and player.id == self.waiting_for_card_from:
                # Create ephemeral card selection embed
                embed = discord.Embed(
                    title="🃏 Choose Your Card",
                    description="Select a card to play (only you can see this):",
                    color=0x0099ff
                )
                
                # Show game context
                suit_names = {'♠': 'Spades', '♥': 'Hearts', '♦': 'Diamonds', '♣': 'Clubs'}
                if self.lead_suit:
                    embed.add_field(name="Must Follow", value=f"{self.lead_suit} {suit_names[self.lead_suit]}", inline=True)
                embed.add_field(name="Trump", value=f"{self.tarneeb_suit} {suit_names[self.tarneeb_suit]}", inline=True)
                
                # Show cards played so far
                if self.played_cards:
                    cards_played = []
                    for p, card in self.played_cards:
                        card_str = CardUI.format_card(card)
                        cards_played.append(f"**{p.name}**: {card_str}")
                    embed.add_field(name="Cards Played", value="\n".join(cards_played), inline=False)
                
                view = CardUI.create_card_selection_view(player.hand, self.lead_suit, self.tarneeb_suit)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                return True
            else:
                await interaction.response.send_message("It's not your turn!", ephemeral=True)
                return True
        elif interaction.data.get("custom_id", "").startswith("card_"):
            card_data = interaction.data["custom_id"].split("_")[1:]
            rank, suit = card_data[0], card_data[1]
            card = (rank, suit)
            player = self.get_player_object(interaction.user.id)
            if player and player == self.player_objects[self.current_turn_index]:
                try:
                    await interaction.response.defer(ephemeral=True)
                    if await self.play_card(interaction.channel, bot, player, card):
                        await interaction.followup.send("Card played!", ephemeral=True)
                    else:
                        await interaction.followup.send("Invalid card play!", ephemeral=True)
                except:
                    # Interaction already responded to, just play the card
                    await self.play_card(interaction.channel, bot, player, card)
                return True
            else:
                try:
                    await interaction.response.send_message("It's not your turn!", ephemeral=True)
                except:
                    pass
                return True
        
        return False
    
    # All the existing Tarneeb game methods remain the same...
    async def handle_bid(self, interaction: discord.Interaction, bid: int, bot):
        """Handle a bid from a player"""
        player = self.get_player_object(interaction.user.id)
        current_player = self.player_objects[self.bidding_turn]
        
        if not player or player != current_player or player.is_bot:
            await interaction.response.send_message("It's not your turn to bid!", ephemeral=True)
            return
        
        if bid <= self.current_bid:
            await interaction.response.send_message(f"Bid must be higher than {self.current_bid}!", ephemeral=True)
            return
        
        self.current_bid = bid
        self.highest_bidder = player
        self.passes_count = 0
        
        logger.info(f"💰 {player.name} bid {bid} tricks")
        await interaction.response.send_message(f"Bid of {bid} tricks accepted!", ephemeral=True)
        await self.next_bidding_turn(interaction.channel, bot)
    
    async def handle_pass(self, interaction: discord.Interaction, bot):
        """Handle a pass from a player"""
        player = self.get_player_object(interaction.user.id)
        current_player = self.player_objects[self.bidding_turn]
        
        if not player or player != current_player or player.is_bot:
            await interaction.response.send_message("It's not your turn to bid!", ephemeral=True)
            return
        
        self.passes_count += 1
        logger.info(f"⏭️ {player.name} passed")
        await interaction.response.send_message("Pass registered!", ephemeral=True)
        await self.next_bidding_turn(interaction.channel, bot)
    
    async def next_bidding_turn(self, channel, bot):
        """Move to next bidding turn"""
        self.bidding_turn = (self.bidding_turn + 1) % 4
        
        # Check if bidding is over
        if self.passes_count >= 3 and self.highest_bidder:
            await self.end_bidding_phase(channel, bot)
            return
        elif self.passes_count >= 4:
            # All players passed, restart round
            await channel.send("🔄 All players passed! Starting new round...")
            self.restart_round()
            await self.continue_bidding(channel, bot)
            return
        
        await self.continue_bidding(channel, bot)
    
    async def continue_bidding(self, channel, bot):
        """Continue bidding with current player"""
        current_player = self.player_objects[self.bidding_turn]
        
        # Create bidding embed
        embed = discord.Embed(
            title="💰 Bidding Phase",
            description=f"**{current_player.name}**'s turn to bid",
            color=0xffd700
        )
        
        embed.add_field(name="Current Bid", value=str(self.current_bid) if self.current_bid > 0 else "No bids yet", inline=True)
        embed.add_field(name="Highest Bidder", value=self.highest_bidder.name if self.highest_bidder else "None", inline=True)
        embed.add_field(name="Round", value=str(self.round_number), inline=True)
        
        if current_player.is_bot:
            # Bot makes bid decision
            await asyncio.sleep(1)  # Simulate thinking
            bot_bid = current_player.ai_player.make_bid_decision(
                current_player.hand, self.current_bid, self.passes_count, self.bidding_turn
            )
            
            if bot_bid > 0:
                self.current_bid = bot_bid
                self.highest_bidder = current_player
                self.passes_count = 0
                embed.add_field(name="Bot Decision", value=f"Bids {bot_bid} tricks", inline=False)
                logger.info(f"🤖 {current_player.name} (bot) bid {bot_bid}")
            else:
                self.passes_count += 1
                embed.add_field(name="Bot Decision", value="Passes", inline=False)
                logger.info(f"🤖 {current_player.name} (bot) passed")
            
            await channel.send(embed=embed)
            await self.next_bidding_turn(channel, bot)
        else:
            # Human player's turn
            view = CardUI.create_bidding_view()
            await channel.send(embed=embed, view=view)
    
    async def end_bidding_phase(self, channel, bot):
        """End bidding and start tarneeb selection"""
        embed = discord.Embed(
            title="✅ Bidding Complete",
            description=f"**{self.highest_bidder.name}** won with {self.current_bid} tricks",
            color=0x00ff00
        )
        
        logger.info(f"✅ Bidding complete - {self.highest_bidder.name} won with {self.current_bid} tricks")
        await channel.send(embed=embed)
        await self.start_tarneeb_selection(channel, bot)
    
    async def start_tarneeb_selection(self, channel, bot):
        """Start tarneeb suit selection phase"""
        self.state = "tarneeb_selection"
        
        if self.highest_bidder.is_bot:
            # Bot chooses tarneeb suit
            await asyncio.sleep(1)
            chosen_suit = self.highest_bidder.ai_player.choose_tarneeb_suit(self.highest_bidder.hand)
            await self.set_tarneeb_suit(channel, bot, chosen_suit, self.highest_bidder)
        else:
            # Human player chooses
            embed = discord.Embed(
                title="🎯 Choose Tarneeb Suit",
                description=f"**{self.highest_bidder.name}**, choose the tarneeb (trump) suit:",
                color=0xff6600
            )
            
            view = CardUI.create_tarneeb_selection_view()
            await channel.send(embed=embed, view=view)
    
    async def set_tarneeb_suit(self, channel, bot, suit: str, player: Player):
        """Set the tarneeb suit and start playing"""
        self.tarneeb_suit = suit
        self.state = "playing"
        
        # Show chosen tarneeb
        suit_name = SUIT_NAMES[suit]
        embed = discord.Embed(
            title="🎯 Tarneeb Suit Chosen",
            description=f"**{player.name}** chose **{suit} {suit_name}** as tarneeb",
            color=0xff6600
        )
        
        embed.add_field(name="Bid", value=f"{self.current_bid} tricks", inline=True)
        embed.add_field(name="Bidding Team", value="Team 1" if self.player_objects.index(player) % 2 == 0 else "Team 2", inline=True)
        
        logger.info(f"🎯 {player.name} chose {suit} {suit_name} as tarneeb")
        await channel.send(embed=embed)
        
        # Start playing phase
        self.current_turn_index = 0  # Start with first player
        await self.start_playing_turn(channel, bot)
    
    async def start_playing_turn(self, channel, bot):
        """Start a player's turn in the playing phase"""
        current_player = self.player_objects[self.current_turn_index]
        
        if current_player.is_bot:
            # Bot plays automatically
            await asyncio.sleep(1)  # Simulate thinking
            card_choice = current_player.ai_player.choose_card_to_play(
                current_player.hand,
                self.lead_suit,
                self.tarneeb_suit,
                [card for _, card in self.played_cards]
            )
            await self.play_card(channel, bot, current_player, card_choice)
        else:
            # Human player's turn - show public game state with private card button
            embed = GameStateEmbed.create_playing_embed(self, current_player)
            
            # Create a view with a button for the current player to see their cards
            view = CardUI.create_show_cards_button_view(current_player.id)
            await channel.send(embed=embed, view=view)
            
            # Store card selection data for when player clicks the button
            self.waiting_for_card_from = current_player.id
    
    async def play_card(self, channel, bot, player: Player, card: Tuple[str, str]) -> bool:
        """Play a card and handle game logic"""
        # Validate card play
        if card not in player.hand:
            return False
        
        # Check if player must follow suit
        if self.lead_suit and player.has_suit(self.lead_suit) and card[1] != self.lead_suit:
            return False
        
        # Remove card from hand and add to played cards
        player.remove_card(card)
        self.played_cards.append((player, card))
        
        # Set lead suit if first card
        if not self.lead_suit:
            self.lead_suit = card[1]
        
        # Show card played
        card_str = CardUI.format_card(card)
        embed = discord.Embed(
            title="🎴 Card Played",
            description=f"**{player.name}** played {card_str}",
            color=0x0099ff
        )
        
        logger.info(f"🎴 {player.name} played {card_str}")
        await channel.send(embed=embed)
        
        # Check if trick is complete (4 cards played)
        if len(self.played_cards) == 4:
            await self.end_trick(channel, bot)
        else:
            # Next player's turn
            self.current_turn_index = (self.current_turn_index + 1) % 4
            await self.start_playing_turn(channel, bot)
        
        return True
    
    async def end_trick(self, channel, bot):
        """End current trick and determine winner"""
        # Find winning card
        winning_card = None
        winning_player = None
        
        # Check for trump cards first
        trump_cards = [(p, c) for p, c in self.played_cards if c[1] == self.tarneeb_suit]
        if trump_cards:
            # Highest trump wins
            winning_player, winning_card = max(trump_cards, key=lambda x: RANKS.index(x[1][0]))
        else:
            # Highest card of lead suit wins
            lead_cards = [(p, c) for p, c in self.played_cards if c[1] == self.lead_suit]
            if lead_cards:
                winning_player, winning_card = max(lead_cards, key=lambda x: RANKS.index(x[1][0]))
        
        if winning_player:
            # Award trick to winning player
            self.tricks_won[winning_player.id] += 1
            
            # Show trick result
            card_str = CardUI.format_card(winning_card)
            embed = discord.Embed(
                title="🏆 Trick Winner",
                description=f"**{winning_player.name}** wins with {card_str}",
                color=0x00ff00
            )
            
            # Show all played cards
            cards_summary = []
            for player, card in self.played_cards:
                card_display = CardUI.format_card(card)
                if player == winning_player:
                    cards_summary.append(f"**🏆 {player.name}: {card_display}**")
                else:
                    cards_summary.append(f"{player.name}: {card_display}")
            
            embed.add_field(name="Cards Played", value="\n".join(cards_summary), inline=False)
            await channel.send(embed=embed)
            
            logger.info(f"🏆 {winning_player.name} won the trick with {card_str}")
            
            # Reset for next trick
            self.played_cards = []
            self.lead_suit = None
            self.current_turn_index = self.player_objects.index(winning_player)
            
            # Check if hand is complete (13 tricks)
            if sum(self.tricks_won.values()) >= 13:
                await self.end_round(channel, bot)
            else:
                await asyncio.sleep(2)  # Brief pause
                await self.start_playing_turn(channel, bot)
    
    async def end_round(self, channel, bot):
        """End current round and calculate scores"""
        # Calculate team tricks
        team_tricks = [0, 0]
        for i, player in enumerate(self.player_objects):
            team_index = i % 2
            team_tricks[team_index] += self.tricks_won.get(player.id, 0)
        
        # Determine if bid was made
        bidding_team = self.player_objects.index(self.highest_bidder) % 2
        bid_made = team_tricks[bidding_team] >= self.current_bid
        
        # Calculate points
        if bid_made:
            # Bidding team made their bid
            points = self.current_bid
            self.teams_scores[bidding_team] += points
            result_msg = f"🎉 Team {bidding_team + 1} made their bid of {self.current_bid}! (+{points} points)"
        else:
            # Bidding team failed
            points = self.current_bid
            other_team = 1 - bidding_team
            self.teams_scores[other_team] += points
            result_msg = f"💥 Team {bidding_team + 1} failed their bid! Team {other_team + 1} gets +{points} points"
        
        # Show round results
        embed = GameStateEmbed.create_round_end_embed(self, result_msg, team_tricks)
        await channel.send(embed=embed)
        
        logger.info(f"🏁 Round {self.round_number} complete - {result_msg}")
        
        # Check for game winner (31 points)
        if max(self.teams_scores) >= 31:
            await self.end_game_final(channel, bot)
        else:
            # Start next round
            await asyncio.sleep(3)
            await self.start_next_round(channel, bot)
    
    async def start_next_round(self, channel, bot):
        """Start the next round"""
        self.round_number += 1
        self.restart_round()
        
        embed = discord.Embed(
            title=f"🔄 Round {self.round_number}",
            description="Starting new round...",
            color=0x0099ff
        )
        
        embed.add_field(name="Current Scores", value=f"Team 1: {self.teams_scores[0]}\nTeam 2: {self.teams_scores[1]}", inline=False)
        
        await channel.send(embed=embed)
        await asyncio.sleep(2)
        await self.continue_bidding(channel, bot)
    
    def restart_round(self):
        """Reset round-specific variables"""
        self.state = "bidding"
        self.current_bid = 0
        self.highest_bidder = None
        self.bidding_turn = 0
        self.passes_count = 0
        self.current_turn_index = 0
        self.tarneeb_suit = None
        self.played_cards = []
        self.lead_suit = None
        
        # Clear hands and redeal
        for player in self.player_objects:
            player.hand = []
            self.tricks_won[player.id] = 0
        
        self.deal_cards()
    
    async def end_game_final(self, channel, bot):
        """End the game and show final results"""
        winning_team = 0 if self.teams_scores[0] >= 31 else 1
        
        embed = discord.Embed(
            title="🎉 Game Over!",
            description=f"**Team {winning_team + 1}** wins!",
            color=0xffd700
        )
        
        # Show final scores
        embed.add_field(name="Final Scores", value=f"Team 1: {self.teams_scores[0]}\nTeam 2: {self.teams_scores[1]}", inline=False)
        
        # Show team members
        team_members = [[], []]
        for i, player in enumerate(self.player_objects):
            team_members[i % 2].append(player.name)
        
        embed.add_field(name="Team 1", value="\n".join(team_members[0]), inline=True)
        embed.add_field(name="Team 2", value="\n".join(team_members[1]), inline=True)
        
        await channel.send(embed=embed)
        
        logger.info(f"🎉 Tarneeb game ended in channel {self.channel_id} - Team {winning_team + 1} wins!")
        
        # End the game
        self.end_game("Game completed") 