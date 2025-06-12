"""
Game Data - Constants and mappings for Balatro items
"""

# Card Ranks and Suits
CARD_RANKS = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]
CARD_SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]  # Ordered for consistency if it matters

# Mapping between display names and internal values
JOKER_MAPPING = {
    # Jokers - Common
    "Joker": "Joker",
    "Greedy Joker": "Greedy_Joker",
    "Lusty Joker": "Lusty_Joker",
    "Wrathful Joker": "Wrathful_Joker",
    "Gluttonous Joker": "Gluttonous_Joker",
    "Jolly Joker": "Jolly_Joker",
    "Zany Joker": "Zany_Joker",
    "Mad Joker": "Mad_Joker",
    "Crazy Joker": "Crazy_Joker",
    "Droll Joker": "Droll_Joker",
    "Sly Joker": "Sly_Joker",
    "Wily Joker": "Wily_Joker",
    "Clever Joker": "Clever_Joker",
    "Devious Joker": "Devious_Joker",
    "Crafty Joker": "Crafty_Joker",
    "Half Joker": "Half_Joker",
    "Credit Card": "Credit_Card",
    "Banner": "Banner",
    "Mystic Summit": "Mystic_Summit",
    "8 Ball": "_8_Ball",
    "Misprint": "Misprint",
    "Raised Fist": "Raised_Fist",
    "Chaos the Clown": "Chaos_the_Clown",
    "Scary Face": "Scary_Face",
    "Abstract Joker": "Abstract_Joker",
    "Delayed Gratification": "Delayed_Gratification",
    "Gros Michel": "Gros_Michel",
    "Even Steven": "Even_Steven",
    "Odd Todd": "Odd_Todd",
    "Scholar": "Scholar",
    "Business Card": "Business_Card",
    "Supernova": "Supernova",
    "Ride the Bus": "Ride_the_Bus",
    "Egg": "Egg",
    "Runner": "Runner",
    "Ice Cream": "Ice_Cream",
    "Splash": "Splash",
    "Blue Joker": "Blue_Joker",
    "Faceless Joker": "Faceless_Joker",
    "Green Joker": "Green_Joker",
    "Superposition": "Superposition",
    "To Do List": "To_Do_List",
    "Cavendish": "Cavendish",
    "Red Card": "Red_Card",
    "Square Joker": "Square_Joker",
    "Riff raff": "Riff_raff",
    "Photograph": "Photograph",
    "Reserved Parking": "Reserved_Parking",
    "Mail In Rebate": "Mail_In_Rebate",
    "Hallucination": "Hallucination",
    "Fortune Teller": "Fortune_Teller",
    "Juggler": "Juggler",
    "Drunkard": "Drunkard",
    "Golden Joker": "Golden_Joker",
    "Popcorn": "Popcorn",
    "Walkie Talkie": "Walkie_Talkie",
    "Smiley Face": "Smiley_Face",
    "Golden Ticket": "Golden_Ticket",
    "Swashbuckler": "Swashbuckler",
    "Hanging Chad": "Hanging_Chad",
    "Shoot the Moon": "Shoot_the_Moon",

    # Jokers - Uncommon
    "Joker Stencil": "Joker_Stencil",
    "Four Fingers": "Four_Fingers",
    "Mime": "Mime",
    "Ceremonial Dagger": "Ceremonial_Dagger",
    "Marble Joker": "Marble_Joker",
    "Loyalty Card": "Loyalty_Card",
    "Dusk": "Dusk",
    "Fibonacci": "Fibonacci",
    "Steel Joker": "Steel_Joker",
    "Hack": "Hack",
    "Pareidolia": "Pareidolia",
    "Space Joker": "Space_Joker",
    "Burglar": "Burglar",
    "Blackboard": "Blackboard",
    "Sixth Sense": "Sixth_Sense",
    "Constellation": "Constellation",
    "Hiker": "Hiker",
    "Card Sharp": "Card_Sharp",
    "Madness": "Madness",
    "Seance": "Seance",
    "Shortcut": "Shortcut",
    "Hologram": "Hologram",
    "Cloud 9": "Cloud_9",
    "Rocket": "Rocket",
    "Midas Mask": "Midas_Mask",
    "Luchador": "Luchador",
    "Gift Card": "Gift_Card",
    "Turtle Bean": "Turtle_Bean",
    "Erosion": "Erosion",
    "To the Moon": "To_the_Moon",
    "Stone Joker": "Stone_Joker",
    "Lucky Cat": "Lucky_Cat",
    "Bull": "Bull",
    "Diet Cola": "Diet_Cola",
    "Trading Card": "Trading_Card",
    "Flash Card": "Flash_Card",
    "Spare Trousers": "Spare_Trousers",
    "Ramen": "Ramen",
    "Seltzer": "Seltzer",
    "Castle": "Castle",
    "Mr Bones": "Mr_Bones",
    "Acrobat": "Acrobat",
    "Sock and Buskin": "Sock_and_Buskin",
    "Troubadour": "Troubadour",
    "Certificate": "Certificate",
    "Smeared Joker": "Smeared_Joker",
    "Throwback": "Throwback",
    "Rough Gem": "Rough_Gem",
    "Bloodstone": "Bloodstone",
    "Arrowhead": "Arrowhead",
    "Onyx Agate": "Onyx_Agate",
    "Glass Joker": "Glass_Joker",
    "Showman": "Showman",
    "Flower Pot": "Flower_Pot",
    "Merry Andy": "Merry_Andy",
    "Oops All 6s": "Oops_All_6s",
    "The Idol": "The_Idol",
    "Seeing Double": "Seeing_Double",
    "Matador": "Matador",
    "Stuntman": "Stuntman",
    "Satellite": "Satellite",
    "Cartomancer": "Cartomancer",
    "Astronomer": "Astronomer",
    "Bootstraps": "Bootstraps",

    # Jokers - Rare
    "DNA": "DNA",
    "Vampire": "Vampire",
    "Vagabond": "Vagabond",
    "Baron": "Baron",
    "Obelisk": "Obelisk",
    "Baseball Card": "Baseball_Card",
    "Ancient Joker": "Ancient_Joker",
    "Campfire": "Campfire",
    "Blueprint": "Blueprint",
    "Wee Joker": "Wee_Joker",
    "Hit the Road": "Hit_the_Road",
    "The Duo": "The_Duo",
    "The Trio": "The_Trio",
    "The Family": "The_Family",
    "The Order": "The_Order",
    "The Tribe": "The_Tribe",
    "Invisible Joker": "Invisible_Joker",
    "Brainstorm": "Brainstorm",
    "Drivers License": "Drivers_License",
    "Burnt Joker": "Burnt_Joker",

    # Jokers - Legendary
    "Canio": "Canio",
    "Triboulet": "Triboulet",
    "Yorick": "Yorick",
    "Chicot": "Chicot",
    "Perkeo": "Perkeo",

    # Tarots
    "The Fool": "The_Fool",
    "The Magician": "The_Magician",
    "The High Priestess": "The_High_Priestess",
    "The Empress": "The_Empress",
    "The Emperor": "The_Emperor",
    "The Hierophant": "The_Hierophant",
    "The Lovers": "The_Lovers",
    "The Chariot": "The_Chariot",
    "Justice": "Justice",
    "The Hermit": "The_Hermit",
    "The Wheel of Fortune": "The_Wheel_of_Fortune",
    "Strength": "Strength",
    "The Hanged Man": "The_Hanged_Man",
    "Death": "Death",
    "Temperance": "Temperance",
    "The Devil": "The_Devil",
    "The Tower": "The_Tower",
    "The Star": "The_Star",
    "The Moon": "The_Moon",
    "The Sun": "The_Sun",
    "Judgement": "Judgement",
    "The World": "The_World",

    # Spectrals
    "Familiar": "Familiar",
    "Grim": "Grim",
    "Incantation": "Incantation",
    "Talisman": "Talisman",
    "Aura": "Aura",
    "Wraith": "Wraith",
    "Sigil": "Sigil",
    "Ouija": "Ouija",
    "Ectoplasm": "Ectoplasm",
    "Immolate": "Immolate",
    "Ankh": "Ankh",
    "Deja Vu": "Deja_Vu",
    "Hex": "Hex",
    "Trance": "Trance",
    "Medium": "Medium",
    "Cryptid": "Cryptid",
    "The Soul": "The_Soul",
    "Black Hole": "Black_Hole",

    # Tags
    "Uncommon Tag": "Uncommon_Tag",
    "Rare Tag": "Rare_Tag",
    "Negative Tag": "Negative_Tag",
    "Foil Tag": "Foil_Tag",
    "Holographic Tag": "Holographic_Tag",
    "Polychrome Tag": "Polychrome_Tag",
    "Investment Tag": "Investment_Tag",
    "Voucher Tag": "Voucher_Tag",
    "Boss Tag": "Boss_Tag",
    "Standard Tag": "Standard_Tag",
    "Charm Tag": "Charm_Tag",
    "Meteor Tag": "Meteor_Tag",
    "Buffoon Tag": "Buffoon_Tag",
    "Handy Tag": "Handy_Tag",
    "Garbage Tag": "Garbage_Tag",
    "Ethereal Tag": "Ethereal_Tag",
    "Coupon Tag": "Coupon_Tag",
    "Double Tag": "Double_Tag",
    "Juggle Tag": "Juggle_Tag",
    "D6 Tag": "D6_Tag",
    "Top up Tag": "Top_up_Tag",
    "Speed Tag": "Speed_Tag",
    "Orbital Tag": "Orbital_Tag",
    "Economy Tag": "Economy_Tag",

    # Vouchers
    "Overstock": "Overstock",
    "Overstock Plus": "Overstock_Plus",
    "Clearance Sale": "Clearance_Sale",
    "Liquidation": "Liquidation",
    "Hone": "Hone",
    "Glow Up": "Glow_Up",
    "Reroll Surplus": "Reroll_Surplus",
    "Reroll Glut": "Reroll_Glut",
    "Crystal Ball": "Crystal_Ball",
    "Omen Globe": "Omen_Globe",
    "Telescope": "Telescope",
    "Observatory": "Observatory",
    "Grabber": "Grabber",
    "Nacho Tong": "Nacho_Tong",
    "Wasteful": "Wasteful",
    "Recyclomancy": "Recyclomancy",
    "Tarot Merchant": "Tarot_Merchant",
    "Tarot Tycoon": "Tarot_Tycoon",
    "Planet Merchant": "Planet_Merchant",
    "Planet Tycoon": "Planet_Tycoon",
    "Seed Money": "Seed_Money",
    "Money Tree": "Money_Tree",
    "Blank": "Blank",
    "Antimatter": "Antimatter",
    "Magic Trick": "Magic_Trick",
    "Illusion": "Illusion",
    "Hieroglyph": "Hieroglyph",
    "Petroglyph": "Petroglyph",
    "Directors Cut": "Directors_Cut",
    "Retcon": "Retcon",
    "Paint Brush": "Paint_Brush",
    "Palette": "Palette",

    # Decks
    "Red Deck": "Red_Deck",
    "Blue Deck": "Blue_Deck",
    "Yellow Deck": "Yellow_Deck",
    "Green Deck": "Green_Deck",
    "Black Deck": "Black_Deck",
    "Magic Deck": "Magic_Deck",
    "Nebula Deck": "Nebula_Deck",
    "Ghost Deck": "Ghost_Deck",
    "Abandoned Deck": "Abandoned_Deck",
    "Checkered Deck": "Checkered_Deck",
    "Zodiac Deck": "Zodiac_Deck",
    "Painted Deck": "Painted_Deck",
    "Anaglyph Deck": "Anaglyph_Deck",
    "Plasma Deck": "Plasma_Deck",
    "Erratic Deck": "Erratic_Deck",

    # Stakes
    "White Stake": "White_Stake",
    "Red Stake": "Red_Stake",
    "Green Stake": "Green_Stake",
    "Black Stake": "Black_Stake",
    "Blue Stake": "Blue_Stake",
    "Purple Stake": "Purple_Stake",
    "Orange Stake": "Orange_Stake",
    "Gold Stake": "Gold_Stake"
}

# Populate JOKER_MAPPING with individual Ranks
for rank in CARD_RANKS:
    JOKER_MAPPING[rank] = rank

# Populate JOKER_MAPPING with individual Suits
for suit in CARD_SUITS:
    JOKER_MAPPING[suit] = suit

# Map of all available items by category
AVAILABLE_ITEMS = {
    "Jokers": [
        # Common Jokers
        "Joker", "Greedy Joker", "Lusty Joker", "Wrathful Joker", "Gluttonous Joker",
        "Jolly Joker", "Zany Joker", "Mad Joker", "Crazy Joker", "Droll Joker",
        "Sly Joker", "Wily Joker", "Clever Joker", "Devious Joker", "Crafty Joker",
        "Half Joker", "Credit Card", "Banner", "Mystic Summit", "8 Ball",
        "Misprint", "Raised Fist", "Chaos the Clown", "Scary Face", "Abstract Joker",
        "Delayed Gratification", "Gros Michel", "Even Steven", "Odd Todd", "Scholar",
        "Business Card", "Supernova", "Ride the Bus", "Egg", "Runner",
        "Ice Cream", "Splash", "Blue Joker", "Faceless Joker", "Green Joker",
        "Superposition", "To Do List", "Cavendish", "Red Card", "Square Joker",
        "Riff raff", "Photograph", "Reserved Parking", "Mail In Rebate", "Hallucination",
        "Fortune Teller", "Juggler", "Drunkard", "Golden Joker", "Popcorn",
        "Walkie Talkie", "Smiley Face", "Golden Ticket", "Swashbuckler", "Hanging Chad",
        "Shoot the Moon",
        # Uncommon Jokers
        "Joker Stencil", "Four Fingers", "Mime", "Ceremonial Dagger", "Marble Joker",
        "Loyalty Card", "Dusk", "Fibonacci", "Steel Joker", "Hack",
        "Pareidolia", "Space Joker", "Burglar", "Blackboard", "Sixth Sense",
        "Constellation", "Hiker", "Card Sharp", "Madness", "Seance",
        "Shortcut", "Hologram", "Cloud 9", "Rocket", "Midas Mask",
        "Luchador", "Gift Card", "Turtle Bean", "Erosion", "To the Moon",
        "Stone Joker", "Lucky Cat", "Bull", "Diet Cola", "Trading Card",
        "Flash Card", "Spare Trousers", "Ramen", "Seltzer", "Castle",
        "Mr Bones", "Acrobat", "Sock and Buskin", "Troubadour", "Certificate",
        "Smeared Joker", "Throwback", "Rough Gem", "Bloodstone", "Arrowhead",
        "Onyx Agate", "Glass Joker", "Showman", "Flower Pot", "Merry Andy",
        "Oops All 6s", "The Idol", "Seeing Double", "Matador", "Stuntman",
        "Satellite", "Cartomancer", "Astronomer", "Bootstraps",
        # Rare Jokers
        "DNA", "Vampire", "Vagabond", "Baron", "Obelisk",
        "Baseball Card", "Ancient Joker", "Campfire", "Blueprint", "Wee Joker",
        "Hit the Road", "The Duo", "The Trio", "The Family", "The Order",
        "The Tribe", "Invisible Joker", "Brainstorm", "Drivers License", "Burnt Joker",
        # Legendary Jokers
        "Canio", "Triboulet", "Yorick", "Chicot", "Perkeo"
    ],
    "Tarots": [
        "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor",
        "The Hierophant", "The Lovers", "The Chariot", "Justice", "The Hermit",
        "The Wheel of Fortune", "Strength", "The Hanged Man", "Death", "Temperance",
        "The Devil", "The Tower", "The Star", "The Moon", "The Sun",
        "Judgement", "The World"
    ],
    "Spectrals": [
        "Familiar", "Grim", "Incantation", "Talisman", "Aura",
        "Wraith", "Sigil", "Ouija", "Ectoplasm", "Immolate",
        "Ankh", "Deja Vu", "Hex", "Trance", "Medium",
        "Cryptid", "The Soul", "Black Hole"
    ],
    "Tags": [
        "Uncommon Tag", "Rare Tag", "Negative Tag", "Foil Tag", "Holographic Tag",
        "Polychrome Tag", "Investment Tag", "Voucher Tag", "Boss Tag", "Standard Tag",
        "Charm Tag", "Meteor Tag", "Buffoon Tag", "Handy Tag", "Garbage Tag",
        "Ethereal Tag", "Coupon Tag", "Double Tag", "Juggle Tag", "D6 Tag",
        "Top up Tag", "Speed Tag", "Orbital Tag", "Economy Tag"
    ],
    "Vouchers": [
        "Overstock", "Overstock Plus", "Clearance Sale", "Liquidation", "Hone",
        "Glow Up", "Reroll Surplus", "Reroll Glut", "Crystal Ball", "Omen Globe",
        "Telescope", "Observatory", "Grabber", "Nacho Tong", "Wasteful",
        "Recyclomancy", "Tarot Merchant", "Tarot Tycoon", "Planet Merchant", "Planet Tycoon",
        "Seed Money", "Money Tree", "Blank", "Antimatter", "Magic Trick",
        "Illusion", "Hieroglyph", "Petroglyph", "Directors Cut", "Retcon",
        "Paint Brush", "Palette"
    ],
    "Decks": [
        "Red Deck", "Blue Deck", "Yellow Deck", "Green Deck", "Black Deck",
        "Magic Deck", "Nebula Deck", "Ghost Deck", "Abandoned Deck", "Checkered Deck",
        "Zodiac Deck", "Painted Deck", "Anaglyph Deck", "Plasma Deck", "Erratic Deck"
    ],
    "Stakes": [
        "White Stake", "Red Stake", "Green Stake", "Black Stake",
        "Blue Stake", "Purple Stake", "Orange Stake", "Gold Stake"
    ],
    "Ranks": CARD_RANKS[:],  # Add Ranks category, assign a copy
    "Suits": CARD_SUITS[:]  # Add Suits category, assign a copy
}

# Valid joker editions
JOKER_EDITIONS = ["No_Edition", "Foil", "Holographic", "Polychrome", "Negative"]


def get_internal_name(display_name):
    """Convert a display name to its internal name format
    
    Args:
        display_name: The display name (e.g., "Blue Joker")
        
    Returns:
        The internal name (e.g., "Blue_Joker")
    """
    return JOKER_MAPPING.get(display_name, display_name.replace(" ", "_"))


def get_display_name(internal_name):
    """Convert an internal name to its display name format
    
    Args:
        internal_name: The internal name (e.g., "Blue_Joker")
        
    Returns:
        The display name (e.g., "Blue Joker")
    """
    # Create a reverse mapping for quick lookup
    reverse_map = {v: k for k, v in JOKER_MAPPING.items()}
    return reverse_map.get(internal_name, internal_name.replace("_", " "))
