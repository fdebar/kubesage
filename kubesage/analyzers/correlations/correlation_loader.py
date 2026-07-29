import importlib
import inspect
import pkgutil

import kubesage.analyzers.correlations as package
from kubesage.analyzers.correlations.base import BaseCorrelation


def discover_correlations() -> list[BaseCorrelation]:

    correlations = []

    for module in pkgutil.walk_packages(
        package.__path__,
        prefix=f"{package.__name__}.",
    ):
        if module.name.endswith((".__init__", ".base")):
            continue

        mod = importlib.import_module(module.name)

        for _, obj in inspect.getmembers(
            mod,
            inspect.isclass,
        ):
            if (
                issubclass(obj, BaseCorrelation)
                and obj is not BaseCorrelation
                and obj.__module__ == mod.__name__
            ):
                correlations.append(obj())

    return correlations
