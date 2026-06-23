
def get_font_size(font):
    if font is not None:
        font = font.strip().lower()
    sizes = {             # MIN  2k 4k
        "smallest": 18,   # LB   -- -- 
        "gui-1": 22,      # BD   LB -- 
        "gui-2": 24,      # H3   BD LB 
        "gui-3": 28,      # H2   H3 BD  
        "gui-4": 32,      # H1   H2 H3
        "gui-5": 36,      # TT   H1 H2
        "gui-6": 52,      # __   TT H1/TT
    }
    return sizes.get(font, 30)