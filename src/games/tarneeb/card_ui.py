import discord
from typing import List, Tuple, Optional

# Card definitions
SUITS = ["♠", "♣", "♥", "♦"]
SUIT_NAMES = {"♠": "Spades", "♣": "Clubs", "♥": "Hearts", "♦": "Diamonds"}

class CardUI:
    """Handle card display and UI elements"""
    
    SUIT_EMOJIS = {
        '♠': '♠️',
        '♣': '♣️',
        '♥': '♥️',
        '♦': '♦️'
    }
    
    @staticmethod
    def format_card(card: Tuple[str, str]) -> str:
        """Format a card for display"""
        rank, suit = card
        emoji = CardUI.SUIT_EMOJIS.get(suit, suit)
        return f"{rank}{emoji}"
    
    @staticmethod
    def format_hand(hand: List[Tuple[str, str]]) -> str:
        """Format a hand of cards for display"""
        if not hand:
            return "No cards"
        
        # Sort by suit, then by rank
        sorted_hand = sorted(hand, key=lambda x: (SUITS.index(x[1]), ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'].index(x[0])))
        return " ".join([CardUI.format_card(card) for card in sorted_hand])
    
    @staticmethod
    def create_bidding_view() -> discord.ui.View:
        """Create bidding interface with buttons"""
        view = discord.ui.View(timeout=300)
        
        # Add bid buttons (1-7)
        for bid in range(1, 8):
            button = discord.ui.Button(
                label=str(bid),
                style=discord.ButtonStyle.primary,
                custom_id=f"bid_{bid}"
            )
            view.add_item(button)
        
        # Add pass button
        pass_button = discord.ui.Button(
            label="Pass",
            style=discord.ButtonStyle.secondary,
            custom_id="pass"
        )
        view.add_item(pass_button)
        
        return view
    
    @staticmethod
    def create_tarneeb_selection_view() -> discord.ui.View:
        """Create tarneeb suit selection interface"""
        view = discord.ui.View(timeout=300)
        
        for suit in SUITS:
            button = discord.ui.Button(
                label=SUIT_NAMES[suit],
                style=discord.ButtonStyle.primary,
                custom_id=f"tarneeb_{suit}",
                emoji=CardUI.SUIT_EMOJIS[suit]
            )
            view.add_item(button)
        
        return view
    
    @staticmethod
    def create_card_selection_view(hand: List[Tuple[str, str]], lead_suit: Optional[str], tarneeb_suit: str) -> discord.ui.View:
        """Create card selection interface"""
        view = discord.ui.View(timeout=300)
        
        # Filter valid cards
        valid_cards = []
        if lead_suit:
            # Must follow suit if possible
            same_suit = [card for card in hand if card[1] == lead_suit]
            valid_cards = same_suit if same_suit else hand
        else:
            valid_cards = hand
        
        # Limit to 25 buttons (Discord's max per view)
        display_cards = valid_cards[:25]
        
        for card in display_cards:
            rank, suit = card
            # Use simple suit emojis for buttons
            suit_emoji = CardUI.SUIT_EMOJIS.get(suit, suit)
            
            # Highlight tarneeb cards
            style = discord.ButtonStyle.danger if suit == tarneeb_suit else discord.ButtonStyle.primary
            
            button = discord.ui.Button(
                label=f"{rank}{suit}",
                style=style,
                custom_id=f"card_{rank}_{suit}",
                emoji=suit_emoji
            )
            view.add_item(button)
        
        return view
    
    @staticmethod
    def create_show_cards_button_view(current_player_id) -> discord.ui.View:
        """Create a button for current player to see their cards privately"""
        view = discord.ui.View(timeout=300)
        
        button = discord.ui.Button(
            label="Show My Cards",
            style=discord.ButtonStyle.primary,
            custom_id=f"show_my_cards_{current_player_id}",
            emoji="🃏"
        )
        view.add_item(button)
        
        return view 