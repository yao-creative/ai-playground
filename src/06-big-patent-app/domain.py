from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PatentRecord:
    id: str
    config: str
    split: str
    abstract: str
    description: str
    text: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
