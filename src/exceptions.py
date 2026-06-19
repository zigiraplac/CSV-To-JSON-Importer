class ImporterError(Exception):
    pass


class FileFormatError(ImporterError):
    pass


class DuplicateUserError(ImporterError):
    pass
