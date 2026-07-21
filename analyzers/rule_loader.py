import inspect
import pkgutil
import importlib

from analyzers.rules.base import BaseRule
import analyzers.rules


def discover_rules() -> list[BaseRule]:
    rules = []

    for module in pkgutil.iter_modules(analyzers.rules.__path__):
        if module.name in ("__init__", "base"):
            continue

        mod = importlib.import_module(f"analyzers.rules.{module.name}")
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, BaseRule) and obj != BaseRule:
                rules.append(obj())

    return rules
