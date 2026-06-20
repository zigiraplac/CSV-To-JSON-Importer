"""Main entry point script for executing the CSV to JSON Importer CLI."""

import logging
import sys
from src.parser import CsvUserImporter
from src.repository import JsonUserRepository

# Configure the root logger to output cleanly to the console terminal screen
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("main")


def main() -> None:
    """Validates command-line arguments and runs the importer pipeline."""
    # We expect exactly 3 arguments: ['main.py', 'input.csv', 'output.json']
    if len(sys.argv) != 3:
        logger.error("Invalid execution syntax.")
        print("\nUsage: python main.py <path_to_input_csv> <path_to_output_json>\n")
        sys.exit(1)

    csv_path = sys.argv[1]
    json_path = sys.argv[2]

    logger.info("Initializing import pipeline process...")

    # 1. Instantiate our isolated storage repository layer
    repository = JsonUserRepository(file_path=json_path)

    # 2. Inject the repository dependency straight into the streaming parsing engine
    importer = CsvUserImporter(repository=repository)

    try:
        # 3. Fire up the execution process
        successful_imports = importer.import_from_file(csv_path)
        logger.info(
            "Import complete! Successfully synchronized %d users to %s.",
            successful_imports,
            json_path,
        )
    except Exception as error:
        logger.critical("The data synchronization pipeline collapsed: %s", error)
        sys.exit(1)


if __name__ == "__main__":
    main()
