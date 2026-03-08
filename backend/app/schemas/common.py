from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DeleteResponse(BaseModel):
    ok: bool = True


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    limit: int
