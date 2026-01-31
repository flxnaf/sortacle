"""
Recyclability Logic
Lookup table mapping waste categories to recyclable status
"""

# Recyclability lookup table for YOLO-World custom categories
# True = Recyclable, False = Non-recyclable/Trash
RECYCLABILITY_TABLE = {
    # Recyclable metals
    "aluminum can": True,
    "metal can": True,
    "soda can": True,
    "beer can": True,
    # Recyclable plastics
    "plastic bottle": True,
    "water bottle": True,
    "plastic container": True,
    # Recyclable glass
    "glass bottle": True,
    "glass jar": True,
    # Recyclable paper/cardboard
    "cardboard box": True,
    "cardboard": True,
    "paper": True,
    "newspaper": True,
    # Cups - assume recyclable for demo
    "cup": True,
    "plastic cup": True,
    "paper cup": True,
    "coffee cup": True,
    # Non-recyclable
    "plastic bag": False,
    "styrofoam": False,
    "food waste": False,
    "food scraps": False,
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
