from app.infrastructure.auth.schema import User


def get_schema(user_id: str | None) -> str:
    """Derive the tenant DB schema from a prefixed user ID (e.g. 'id_<uuid>')."""
    return user_id.replace("-", "_") if user_id is not None else "public"


async def map_user(userinfo: dict) -> User | None:  # NOSONAR(S7503)
    user_id = userinfo.get("sub")
    if user_id is not None:
        return User(
            id=f"id_{user_id}",
            email=userinfo.get("email"),
            username=userinfo.get("preferred_username"),
        )
    return None
