class BeatItError(Exception):
    """Any error found while lexing, parsing, checking or running a Beat It program."""

    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        super().__init__(f"Line {line}: {message}" if line else message)
