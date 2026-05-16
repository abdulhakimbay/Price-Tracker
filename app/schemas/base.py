"""Shared Pydantic base configuration for all application schemas."""

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema that enables ORM mode for all derived models."""

    model_config = ConfigDict(from_attributes=True)
