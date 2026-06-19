from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    user_ID: str
    name: str
    email: str
