"""Qualitative rubric transfer schemas."""

from pydantic import BaseModel, Field, model_validator


class CriterionInput(BaseModel):
    """One rubric question."""

    code: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1)
    guidance: str = ""


class RubricCreate(BaseModel):
    """New rubric and ordered criteria."""

    name: str = Field(min_length=1)
    description: str = ""
    criteria: list[CriterionInput] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_codes(self):
        """Criterion identifiers must be unique within a version."""
        codes = [item.code for item in self.criteria]
        if len(codes) != len(set(codes)):
            raise ValueError("duplicate criterion code")
        return self


class RubricUpdate(BaseModel):
    """Partial rubric edit that creates another version."""

    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    criteria: list[CriterionInput] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def unique_codes(self):
        """Reject duplicate codes on replacement."""
        if self.criteria is not None:
            codes = [item.code for item in self.criteria]
            if len(codes) != len(set(codes)):
                raise ValueError("duplicate criterion code")
        return self


class CriterionRead(CriterionInput):
    """A criterion with its display order."""

    order_index: int


class RubricRead(BaseModel):
    """Current rubric head and selected version criteria."""

    id: str
    name: str
    description: str
    version: int
    criteria: list[CriterionRead]


class RubricPage(BaseModel):
    """Paginated rubric collection."""

    items: list[RubricRead]
    total: int
    limit: int
    offset: int
