"""Flow control guards: enforce batch-first design rules."""


class LoopWarning(Exception):
    """Raised when code attempts an inefficient individual-code loop."""


def validate_no_loop(codes: list, batch_size: int = 60):
    """
    Guard against silent loops.

    Raises LoopWarning if caller tries to process more codes than a
    single batch endpoint can handle, suggesting they should chunk or
    use a batch endpoint.
    """
    if len(codes) > batch_size:
        raise LoopWarning(
            f"Attempting to process {len(codes)} codes individually. "
            f"Use batch endpoint or chunk into groups of {batch_size}."
        )


def chunk(codes: list, batch_size: int = 60) -> list[list]:
    """Split a list of codes into batch-sized chunks."""
    return [codes[i:i + batch_size] for i in range(0, len(codes), batch_size)]
