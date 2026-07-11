"""
this module initializes the controllers for the application, including business and user management.
"""
from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    """
    A Pydantic base model that enforces strict validation rules.

    This model forbids extra fields during initialization and ensures that
    data is re-validated whenever an attribute is assigned a new value.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True
    )
