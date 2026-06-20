"""Unit test suite for the CSV Importer engine."""

import pytest
from src.exceptions import FileFormatError, DuplicateUserError
from src.parser import CsvUserImporter


@pytest.fixture
def mock_repository(mocker):
    """Creates an isolated mock repository object using pytest-mock.

    This acts as a 'stunt double' for our JsonUserRepository.
    """
    # Create a generic mock object
    mock_repo = mocker.MagicMock()
    # Ensure it implements the .save() method, but doesn't actually execute it
    mock_repo.save = mocker.MagicMock(return_value=None)
    return mock_repo


@pytest.fixture
def temp_csv_file(tmp_path):
    """A pytest fixture that leverages the built-in temporary path utility.

    It returns a factory function so we can write different test CSV data
    on the fly inside our test cases.
    """

    def _create_file(content: str) -> str:
        # Create a completely safe, isolated temporary file path
        csv_file = tmp_path / "test_input.csv"
        csv_file.write_text(content, encoding="utf-8")
        return str(csv_file)

    return _create_file


def test_import_perfect_data_success(temp_csv_file, mock_repository):
    """Verifies that a perfectly structured CSV increments success counter."""
    # Arrange: Setup clean CSV text data
    csv_data = (
        "user_id,name,email\n"
        "1,Alice Smith,alice@example.com\n"
        "2,Bob Jones,bob@example.com\n"
    )
    file_path = temp_csv_file(csv_data)
    importer = CsvUserImporter(repository=mock_repository)

    # Act: Run the processing engine
    imported_count = importer.import_from_file(file_path)

    # Assert: Verify outputs and tracking behavior
    assert imported_count == 2
    # Verify our mock repository was called exactly twice with clean User models
    assert mock_repository.save.call_count == 2


@pytest.mark.parametrize(
    "invalid_csv_content",
    [
        "wrong,headers,here\n1,Alice,alice@example.com",  # Broken headers
        "user_id,name,email\n1,,alice@example.com",  # Missing name column field
        "user_id,name,email\n,Alice Smith,alice@example.com",  # Missing ID field
    ],
)
def test_import_malformed_rows_are_skipped(
    temp_csv_file, mock_repository, invalid_csv_content
):
    """Verifies that various types of bad rows skip safely instead of crashing."""
    # Arrange
    file_path = temp_csv_file(invalid_csv_content)
    importer = CsvUserImporter(repository=mock_repository)

    # Act & Assert
    if "wrong,headers" in invalid_csv_content:
        # If headers are fundamentally broken, the engine should raise a fatal FileFormatError
        with pytest.raises(FileFormatError):
            importer.import_from_file(file_path)
    else:
        # If it's just a bad data row, the loop should gracefully handle it and return 0 successes
        imported_count = importer.import_from_file(file_path)
        assert imported_count == 0
        assert mock_repository.save.call_count == 0


def test_import_duplicate_user_is_skipped(temp_csv_file, mock_repository):
    """Verifies that if a user ID already exists, the row skips safely."""
    # Arrange: Instruct our mock object to explicitly raise an error when save is called
    mock_repository.save.side_effect = DuplicateUserError("Duplicate ID detected")

    csv_data = "user_id,name,email\n1,Alice Smith,alice@example.com\n"
    file_path = temp_csv_file(csv_data)
    importer = CsvUserImporter(repository=mock_repository)

    # Act
    imported_count = importer.import_from_file(file_path)

    # Assert: Verify that despite the duplicate issue, the application returned 0 successes safely
    assert imported_count == 0
