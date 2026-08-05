from kubesage.utils.resource_quantity import (
    parse_cpu_quantity,
    parse_memory_quantity,
)


def test_cpu_quantity_parser() -> None:
    assert parse_cpu_quantity("1000m") == 1.0
    assert parse_cpu_quantity("500m") == 0.5
    assert parse_cpu_quantity("1000000000n") == 1.0
    assert parse_cpu_quantity("1000000u") == 1.0
    assert parse_cpu_quantity("2") == 2.0
    assert parse_cpu_quantity(None) is None


def test_memory_quantity_parser() -> None:
    assert parse_memory_quantity("1Ki") == 1024
    assert parse_memory_quantity("1Mi") == 1024**2
    assert parse_memory_quantity("1Gi") == 1024**3
    assert parse_memory_quantity("512") == 512
    assert parse_memory_quantity(None) is None
