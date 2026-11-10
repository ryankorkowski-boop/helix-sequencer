LEGACY_CHANNELS = 256

NOTE_TO_MODEL = {
    'C4':'NORTH_CANE_6',
    'D4':'NORTH_CANE_7',
    'E4':'NORTH_CANE_8',
    'F4':'NORTH_CANE_9',
    'G4':'NORTH_CANE_10',
    'A4':'NORTH_CANE_11',
    'B4':'NORTH_CANE_12',
    'C5':'NORTH_CANE_13',
}

def build_legacy_channel_map():
    return {f'CH_{i:03d}': i for i in range(1, LEGACY_CHANNELS + 1)}
