from dataclasses import dataclass

@dataclass(frozen=True)
class ConfigDTO:
    api_key: str
    max_depth: int
    timeout: int
    output_format: str