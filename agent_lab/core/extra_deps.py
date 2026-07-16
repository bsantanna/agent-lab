from agent_lab.domain.exceptions.base import ConfigurationError


def resolve_extra_deps(container, extra_deps, owner: str) -> dict:
    """Resolves declared extra dependencies off a live container instance.

    The single convention behind every registration decorator
    (``@RegisterAgent``, ``@RegisterMcpRegistrar``): each name in
    ``extra_deps`` is looked up as a provider attribute on the (possibly
    downstream-subclassed) container and passed as a constructor kwarg of the
    same name. ``owner`` names the declaring component in the error message.
    """
    kwargs = {}
    for dep_name in extra_deps:
        provider = getattr(container, dep_name, None)
        if provider is None:
            raise ConfigurationError(
                f"{owner} declares extra dependency '{dep_name}' "
                f"but {type(container).__name__} has no such provider"
            )
        kwargs[dep_name] = provider()
    return kwargs
