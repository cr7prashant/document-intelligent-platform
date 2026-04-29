from pydantic import BaseModel


class CatalogItem(BaseModel):
    hs_code: str
    description: str
    category: str
    restricted: bool
    typical_weight_kg: float