from pydantic import BaseModel, Field


class Card(BaseModel):
    front: str
    back: str
    tags: list[str] = []
    is_cloze: bool = False
    source_file: str = ""
    source_chunk: int = 0


class CardList(BaseModel):
    cards: list[Card]


class Chunk(BaseModel):
    text: str
    source_file: str
    chunk_index: int


class ProviderConfig(BaseModel):
    api_key: str = ""
    base_url: str = ""
    default_model: str = ""
    vision: bool = True


class Config(BaseModel):
    provider: str = "gemini"
    model: str = "gemini-3.1-flash-lite"
    api_key: str = ""
    base_url: str = ""
    vision: bool = True
    parsing_model: str = ""
    batch_size: int = 15
    prompt: str = ""
    deck_name: str = "ankirai Deck"
    output_format: str = "apkg"
    output_path: str = ""
    extra_tags: list[str] = Field(default_factory=list)
