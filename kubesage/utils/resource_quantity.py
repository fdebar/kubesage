def parse_cpu_quantity(value: str | None) -> float | None:
    if value is None:
        return None

    if value.endswith("n"):
        return float(value[:-1]) / 1000000000

    if value.endswith("u"):
        return float(value[:-1]) / 1000000

    if value.endswith("m"):
        return float(value[:-1]) / 1000

    return float(value)


def parse_memory_quantity(value: str | None) -> int | None:
    if value is None:
        return None

    units = {
        "Ki": 1024,
        "Mi": 1024**2,
        "Gi": 1024**3,
        "Ti": 1024**4,
    }

    for suffix, multiplier in units.items():
        if value.endswith(suffix):
            return int(float(value[: -len(suffix)]) * multiplier)

    return int(value)
