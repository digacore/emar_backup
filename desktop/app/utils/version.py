from typing import Self


class Version:
    """Version class for comparing versions."""

    def __init__(self):
        self.major = 0
        self.minor = 0
        self.patch = 0
        self.build = 0

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}.{self.build}"

    def __repr__(self):
        return f"{self.major}.{self.minor}.{self.patch}.{self.build}"

    def __eq__(self, other: Self) -> bool:
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.build == other.build
        )

    def __gt__(self, other: Self) -> bool:
        return (
            self.major > other.major or self.minor > other.minor or self.patch > other.patch or self.build > other.build
        )

    def __lt__(self, other: Self) -> bool:
        return (
            self.major < other.major or self.minor < other.minor or self.patch < other.patch or self.build < other.build
        )

    def from_str(self, version: str) -> Self:
        self.major, self.minor, self.patch, self.build = [int(i) for i in version.strip().split(".")]
        return self
