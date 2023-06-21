from config import FUZZER_NAME, FUZZER_COLOR


def color_selection_cb(key: str) -> str:
    for (fuzzer_key, name) in FUZZER_NAME.items():
        if name == key:
            return FUZZER_COLOR[fuzzer_key]
        
    raise ValueError(f'Unknown key for color name mapping: {key}')