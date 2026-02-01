"""
Recyclability Logic
Lookup table mapping waste categories to recyclable status
"""

# Recyclability lookup table - simplified to match detection classes
# True = Recyclable, False = Non-recyclable/Trash
RECYCLABILITY_TABLE = {
    # Recyclable
    "can": True,
    "bottle": True,
    "cardboard box": True,
    "cardboard": True,
    "paper": True,
    # Non-recyclable
    "cup": False,              # Disposable cups have plastic lining
    "plastic bag": False,
    "chip bag": False,
    "food package": False,
    "wrapper": False,
    "plastic wrapper": False,
    "food container": False,
    "styrofoam": False,
    "foam container": False,
    "straw": False,
    "fork": False,
    "spoon": False,
    "plastic utensil": False,
    "napkin": False,
    "tissue": False,
    # Food waste
    "banana": False,
    "apple": False,
    "orange": False,
    # Electronics/Hazardous
    "phone": False,
    "battery": False,
    "light bulb": False,
    "pen": False,
    "pencil": False,
    "toy": False,
}


def is_recyclable(label: str) -> bool:
    """
    Check if detected item is recyclable
    
    Args:
        label: Detected label string
    
    Returns:
        bool: True if recyclable, False otherwise (defaults to False for unknown)
    """
    return RECYCLABILITY_TABLE.get(label.lower(), False)


def get_recyclability_symbol(recyclable: bool) -> str:
    """Get emoji symbol for recyclability status"""
    return "♻️ RECYCLABLE" if recyclable else "🗑️ TRASH"
