"""Unit test suite for the CSV Importer engine."""

import pytest
from src.exceptions import FileFormatError, DuplicateUserError
from src.parser import CsvUserImporter


@pytest.fixture
def mock_repository(mocker):
    """Creates an isolated mock repository object using pytest-mock.

    This acts as a 'stunt double' for our JsonUserRepository, preventing
    tests from making actual modifications to your hard drive.
    """
    mock_repo = mocker.MagicMock()
    mock_repo.save = mocker.MagicMock(return_value=None)
    return mock_repo


@pytest.fixture
def temp_csv_file(tmp_path):
    """A pytest fixture leveraging the built-in temporary path utility.

    It returns a factory function so we can generate distinct CSV scenarios
    dynamically inside each individual test case.
    """

    def _create_file(content: str) -> str:
        csv_file = tmp_path / "test_input.csv"
        csv_file.write_text(content, encoding="utf-8")
        return str(csv_file)

    return _create_file


def test_import_perfect_data_success(temp_csv_file, mock_repository):
    """Verifies that a perfectly structured CSV file increments the success counter."""
    # Arrange: Set up clean, ideal raw CSV text data
    csv_data = (
        "user_id,name,email\n"
        "1,Alice Smith,alice@example.com\n"
        "2,Bob Jones,bob@example.com\n"
    )
    file_path = temp_csv_file(csv_data)
    importer = CsvUserImporter(repository=mock_repository)

    # Act: Run the streaming process engine
    imported_count = importer.import_from_file(file_path)

    # Assert: Verify that the math and structural interactions line up perfectly
    assert imported_count == 2
    assert mock_repository.save.call_count == 2


@pytest.mark.parametrize(
    "invalid_csv_content",
    [
        "wrong,headers,here\n1,Alice,alice@example.com",  # Completely broken headers
        "user_id,name,email\n1,,alice@example.com",  # Missing required name column
        "user_id,name,email\n,Alice Smith,alice@example.com",  # Missing primary ID field
    ],
)
def test_import_malformed_rows_are_skipped(
    temp_csv_file, mock_repository, invalid_csv_content
):
    """Verifies that various types of corrupted rows skip safely instead of crashing."""
    # Arrange
    file_path = temp_csv_file(invalid_csv_content)
    importer = CsvUserImporter(repository=mock_repository)

    # Act & Assert
    if "wrong,headers" in invalid_csv_content:
        # If headers are fundamentally unreadable, the entire operation should raise a fatal FileFormatError
        with pytest.raises(FileFormatError):
            importer.import_from_file(file_path)
    else:
        # If it's a structural layout defect on a specific data line, the loop should skip it and return 0
        imported_count = importer.import_from_file(file_path)
        assert imported_count == 0
        assert mock_repository.save.call_count == 0


def test_import_duplicate_user_is_skipped(temp_csv_file, mock_repository):
    """Verifies that if a user ID already exists in storage, the row skips safely."""
    # Arrange: Force our repository stunt double to simulate a database constraint violation
    mock_repository.save.side_effect = DuplicateUserError("Duplicate ID detected")

    csv_data = "user_id,name,email\n1,Alice Smith,alice@example.com\n"
    file_path = temp_csv_file(csv_data)
    importer = CsvUserImporter(repository=mock_repository)

    # Act
    imported_count = importer.import_from_file(file_path)

    # Assert: Ensure that despite the duplicate error, the application handled it gracefully
    assert imported_count == 0
