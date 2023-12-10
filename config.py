# Configuration and constants
MAX_WINDOW_SIZE = (800, 600)
# Other constants...

def choose_label(preset):
    """
    Function to choose different label presets.
    
    Args:
    preset (int): The preset number to choose.

    Returns:
    dict: A dictionary mapping original labels to new labels.
    """
    if preset == 1:
        # Preset 1: The one you provided
        return {
            1: "U1", 2: "U6", 3: "U5", 4: "R1", 5: "U10",
            6: "G3", 7: "R7", 8: "R3", 9: "G4", 10: "U7",
            11: "U3", 12: "R5", 13: "U4", 14: "R4", 15: "G2",
            16: "U9", 17: "R8", 18: "U8", 19: "R10", 20: "R9",
            21: "G1", 22: "R6", 23: "R2", 24: "U2"
        }
    elif preset == 2:
        # Preset 2: An example alternative preset
        return {
            1: "A1", 2: "B2", 3: "C3", 4: "D4", 5: "E5",
            # ... Continue for all labels
        }
    # ... You can add more presets here
    else:
        raise ValueError("Invalid preset number")

