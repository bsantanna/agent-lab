from fastapi import HTTPException


class NotFoundError(Exception):
    entity_name: str

    def __init__(self, entity_id):
        super().__init__(f"{self.entity_name} not found, id: {entity_id}")


class InvalidFieldError(HTTPException):
    def __init__(self, field_name, reason):
        super().__init__(
            status_code=400, detail=f"Field {field_name} is invalid, reason: {reason}"
        )
