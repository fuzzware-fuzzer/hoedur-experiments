from config import FUZZER_NAME


def name_resolver(key: str, value: str) -> str:
    if key == 'Fuzzers':
        return FUZZER_NAME[value]

    return value
