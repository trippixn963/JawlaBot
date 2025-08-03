import random
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# Card definitions
SUITS = ["♠", "♣", "♥", "♦"]
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

class AIPlayer:
    """AI player for Tarneeb with basic strategy"""
    
    def __init__(self, difficulty: str = "medium"):
        self.difficulty = difficulty
    
    def make_bid_decision(self, hand: List[Tuple[str, str]], current_bid: int, passes_count: int, position: int) -> int:
        """Make a bidding decision based on hand strength"""
        hand_strength = self._evaluate_hand_strength(hand)
        
        # Basic bidding strategy
        if hand_strength >= 8:
            # Strong hand - bid aggressively
            min_bid = max(current_bid + 1, 5)
            max_bid = min(7, hand_strength // 2 + 3)
        elif hand_strength >= 5:
            # Medium hand - bid cautiously
            min_bid = max(current_bid + 1, 3)
            max_bid = min(5, hand_strength // 2 + 2)
        else:
            # Weak hand - usually pass unless desperate
            if passes_count >= 2 and current_bid == 0:
                min_bid = 1
                max_bid = 2
            else:
                return 0  # Pass
        
        if min_bid <= max_bid and min_bid <= 7:
            return random.randint(min_bid, max_bid)
        
        return 0  # Pass
    
    def _evaluate_hand_strength(self, hand: List[Tuple[str, str]]) -> int:
        """Evaluate hand strength for bidding (0-13 scale)"""
        strength = 0
        suits_count = {"♠": 0, "♣": 0, "♥": 0, "♦": 0}
        high_cards = 0
        
        # Count cards per suit and high cards
        for rank, suit in hand:
            suits_count[suit] += 1
            if rank in ['A', 'K', 'Q', 'J']:
                high_cards += {'A': 4, 'K': 3, 'Q': 2, 'J': 1}[rank]
        
        # Add points for high cards
        strength += high_cards
        
        # Add points for long suits (potential trump suits)
        for suit, count in suits_count.items():
            if count >= 5:
                strength += count - 2
            elif count >= 3:
                strength += 1
        
        return min(strength, 13)
    
    def choose_card_to_play(self, hand: List[Tuple[str, str]], lead_suit: Optional[str], 
                           tarneeb_suit: str, played_cards: List[Tuple[str, str]]) -> Tuple[str, str]:
        """Choose a card to play based on game state and basic strategy"""
        
        # Get valid cards to play
        valid_cards = self._get_valid_cards(hand, lead_suit)
        
        if not valid_cards:
            return random.choice(hand)
        
        # If no lead suit, play strategically
        if not lead_suit:
            return self._choose_lead_card(valid_cards, tarneeb_suit)
        
        # If must follow suit
        same_suit_cards = [card for card in valid_cards if card[1] == lead_suit]
        if same_suit_cards:
            # Try to win if possible, otherwise play low
            if lead_suit == tarneeb_suit:
                # Trump suit - play high
                return max(same_suit_cards, key=lambda x: RANKS.index(x[0]))
            else:
                # Non-trump - try to win or play low
                highest_played = self._get_highest_played_card(played_cards, lead_suit, tarneeb_suit)
                winning_cards = [card for card in same_suit_cards 
                               if self._can_beat_card(card, highest_played, tarneeb_suit)]
                
                if winning_cards:
                    return min(winning_cards, key=lambda x: RANKS.index(x[0]))  # Lowest winning card
                else:
                    return min(same_suit_cards, key=lambda x: RANKS.index(x[0]))  # Lowest card
        
        # Can't follow suit - play trump or discard
        trump_cards = [card for card in valid_cards if card[1] == tarneeb_suit]
        if trump_cards and self._should_trump(played_cards, tarneeb_suit):
            return min(trump_cards, key=lambda x: RANKS.index(x[0]))  # Lowest trump
        
        # Discard lowest non-trump
        non_trump = [card for card in valid_cards if card[1] != tarneeb_suit]
        if non_trump:
            return min(non_trump, key=lambda x: RANKS.index(x[0]))
        
        return random.choice(valid_cards)
    
    def _get_valid_cards(self, hand: List[Tuple[str, str]], lead_suit: Optional[str]) -> List[Tuple[str, str]]:
        """Get valid cards that can be played"""
        if not lead_suit:
            return hand
        
        same_suit = [card for card in hand if card[1] == lead_suit]
        return same_suit if same_suit else hand
    
    def _choose_lead_card(self, cards: List[Tuple[str, str]], tarneeb_suit: str) -> Tuple[str, str]:
        """Choose card to lead with"""
        # Lead with high non-trump or low trump
        non_trump_high = [card for card in cards if card[1] != tarneeb_suit and card[0] in ['A', 'K']]
        if non_trump_high:
            return random.choice(non_trump_high)
        
        trump_cards = [card for card in cards if card[1] == tarneeb_suit]
        if trump_cards:
            return min(trump_cards, key=lambda x: RANKS.index(x[0]))
        
        return random.choice(cards)
    
    def _get_highest_played_card(self, played_cards: List[Tuple[str, str]], lead_suit: str, tarneeb_suit: str) -> Optional[Tuple[str, str]]:
        """Get the highest card played so far in the trick"""
        if not played_cards:
            return None
        
        # Check for trump cards first
        trump_cards = [card for card in played_cards if card[1] == tarneeb_suit]
        if trump_cards:
            return max(trump_cards, key=lambda x: RANKS.index(x[0]))
        
        # Otherwise, highest of lead suit
        lead_cards = [card for card in played_cards if card[1] == lead_suit]
        if lead_cards:
            return max(lead_cards, key=lambda x: RANKS.index(x[0]))
        
        return None
    
    def _can_beat_card(self, my_card: Tuple[str, str], other_card: Optional[Tuple[str, str]], tarneeb_suit: str) -> bool:
        """Check if my card can beat the other card"""
        if not other_card:
            return True
        
        my_rank, my_suit = my_card
        other_rank, other_suit = other_card
        
        # Trump beats non-trump
        if my_suit == tarneeb_suit and other_suit != tarneeb_suit:
            return True
        if my_suit != tarneeb_suit and other_suit == tarneeb_suit:
            return False
        
        # Same suit comparison
        if my_suit == other_suit:
            return RANKS.index(my_rank) > RANKS.index(other_rank)
        
        return False
    
    def _should_trump(self, played_cards: List[Tuple[str, str]], tarneeb_suit: str) -> bool:
        """Decide whether to play trump when can't follow suit"""
        # Simple strategy: trump if no trump played yet
        trump_played = any(card[1] == tarneeb_suit for card in played_cards)
        return not trump_played
    
    def choose_tarneeb_suit(self, hand: List[Tuple[str, str]]) -> str:
        """Choose the tarneeb (trump) suit based on hand"""
        suit_counts = {"♠": 0, "♣": 0, "♥": 0, "♦": 0}
        suit_strength = {"♠": 0, "♣": 0, "♥": 0, "♦": 0}
        
        # Count cards and calculate strength per suit
        for rank, suit in hand:
            suit_counts[suit] += 1
            if rank in ['A', 'K', 'Q', 'J']:
                suit_strength[suit] += {'A': 4, 'K': 3, 'Q': 2, 'J': 1}[rank]
        
        # Prefer suits with more cards and higher strength
        best_suit = max(SUITS, key=lambda s: suit_counts[s] * 2 + suit_strength[s])
        return best_suit

class Player:
    """Represents a player in the game"""
    
    def __init__(self, user_id: str, name: str, is_bot: bool = False):
        self.id = user_id
        self.name = name
        self.is_bot = is_bot
        self.hand: List[Tuple[str, str]] = []
        self.ai_player = AIPlayer() if is_bot else None
    
    def add_card(self, card: Tuple[str, str]):
        """Add a card to player's hand"""
        self.hand.append(card)
    
    def remove_card(self, card: Tuple[str, str]) -> bool:
        """Remove a card from player's hand"""
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False
    
    def has_suit(self, suit: str) -> bool:
        """Check if player has any cards of the given suit"""
        return any(card[1] == suit for card in self.hand) 