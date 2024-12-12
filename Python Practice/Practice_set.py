# class card:
#     def __init__(self, suit, rank):
#         self.suit = suit
#         self.rank = rank
#     def __repr__(self):
#         return f"{self.rank} of {self.suit}"
    
# class Deck:
#     def __init__(self):
#         suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
#         ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
#         self.cards = [card(suit, rank) for suit in suits for rank in ranks]

#     def shuffle(self):
#         import random
#         random.shuffle(self.cards)

#     def deal(self):
#         if len(self.cards) == 0:
#             return None
#         return self.cards.pop()
    
# obj1 = Deck()
# print(obj1.cards)


# from dataclasses import dataclass
# print(dir(dataclass))

# @dataclass
# class Person:
#     name: str
#     age: int
#     gender: str


# obj1=Person("CJ", 29, "male")
# print(obj1)



import random

