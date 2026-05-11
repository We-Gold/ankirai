from pydantic import BaseModel


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
    instruct: str = ""
