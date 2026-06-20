"""Repository layer for persisting user data to JSON storage."""

import json
import os
from src.models import User
from src.exceptions import DuplicateUserError


class JsonUserRepository:
    """Manages reading and writing User objects to a physical JSON file."""

    def __init__(self, file_path: str) -> None:

        self.file_path = file_path

    def _read_raw_data(self) -> dict:
        """Helper method to safely open and read the raw file contents."""

        if not os.path.exists(self.file_path):
            return {}

        with open(self.file_path, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                # If the file is empty or corrupted, treat it as empty database
                return {}

    def save(self, user: User) -> None:
        """Persists a single unique User object to the JSON database."""
        # 1. Read existing database records
        current_data = self._read_raw_data()

        # 2. Enforce business rules: Check for duplicates
        if user.user_ID in current_data:
            raise DuplicateUserError(
                f"Cannot save user. ID '{user.user_ID}' already exists."
            )

        # 3. Add the new record serialized as a plain dictionary
        current_data[user.user_ID] = {"name": user.name, "email": user.email}

        # 4. Write back to disk cleanly using a context manager
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(current_data, file, indent=4)
