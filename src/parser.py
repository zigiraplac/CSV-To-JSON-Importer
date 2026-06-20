"""CSV Data Parsing Engine with robust structured error handling."""

import csv
import logging
from src.models import User
from src.repository import JsonUserRepository
from src.exceptions import FileFormatError, DuplicateUserError

# Set up a structured logger bound to this specific module file
logger = logging.getLogger(__name__)


class CsvUserImporter:
    """Handles parsing user data from CSV files safely into storage."""

    def __init__(self, repository: JsonUserRepository) -> None:
        """Initializes the importer with a decoupled storage repository dependency."""
        self.repository = repository

    def import_from_file(self, file_path: str) -> int:
        """Parses a CSV file row by row and persists valid records to storage.

        Returns the total number of successfully imported users.
        """
        success_count = 0

        with open(file_path, mode="r", encoding="utf-8") as file:
            # DictReader uses the first line of the CSV as keys for each row dictionary
            reader = csv.DictReader(file)

            # Explicit verification that the expected columns exist in the header row
            if reader.fieldnames is None or not all(
                col in reader.fieldnames for col in ["user_id", "name", "email"]
            ):
                logger.error("CSV File structure is invalid. Missing required headers.")
                raise FileFormatError(
                    "CSV header row must contain 'user_id', 'name', and 'email'."
                )

            for row_number, row in enumerate(reader, start=2):
                try:
                    # 1. Look for missing or empty fields within the current row dictionary
                    if (
                        not row.get("user_id")
                        or not row.get("name")
                        or not row.get("email")
                    ):
                        raise FileFormatError(
                            f"Row {row_number} has missing or blank values."
                        )

                    # Instantiate our strict data model
                    user = User(
                        user_ID=row["user_id"].strip(),
                        name=row["name"].strip(),
                        email=row["email"].strip(),
                    )

                except FileFormatError as error:
                    # Capture formatting errors, log a detailed warning, and jump to next row
                    logger.warning("Skipping malformed data row: %s", error)
                    continue

                try:
                    # 2. Try to persist the valid user object to the database
                    self.repository.save(user)

                except DuplicateUserError as error:
                    # Capture data conflicts, log a detailed warning, and jump to next row
                    logger.warning("Skipping duplicate record: %s", error)
                    continue

                else:
                    # This block runs ONLY if the try block completed perfectly without throwing an exception
                    success_count += 1
                    logger.info(
                        "Successfully imported user: %s (%s)", user.name, user.user_ID
                    )

                finally:
                    # This block is guaranteed to run on every single iteration, no matter what happened above
                    logger.debug("Finished processing row number %d", row_number)

        return success_count
