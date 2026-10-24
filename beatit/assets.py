"""Compiler-only sound asset lookup shared by semantic analysis and packaging."""
from pathlib import Path

# Supported audio file formats
SOUND_EXTENSIONS = (
    ".wav", ".mp3", ".aac", ".m4a", ".flac",
    ".ogg", ".opus", ".mid", ".midi", ".wma"
)

def find_sound_file(folder, name):
    for extension in SOUND_EXTENSIONS:
        candidate = Path(folder) / f"{name}{extension}"
        if candidate.is_file():
            return candidate
    return None