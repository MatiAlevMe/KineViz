import random

suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
ranks = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.is_face_up = False

    def __str__(self):
        return f"{self.rank} of {self.suit}"

def create_deck():
    deck = []
    for suit in suits:
        for rank in ranks:
            deck.append(Card(suit, rank))
    random.shuffle(deck)
    return deck
