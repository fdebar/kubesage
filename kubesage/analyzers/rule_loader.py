import importlib
import inspect
import pkgutil
import kubesage.analyzers.rules as rules_package
from kubesage.analyzers.rules.base import BaseRule


def discover_rules() -> list[BaseRule]:
    rules = []

    for module in pkgutil.iter_modules(rules_package.__path__):
        if module.name in ("__init__", "base"):
            continue

        mod = importlib.import_module(f"{rules_package.__name__}.{module.name}")

        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, BaseRule) and obj is not BaseRule:
                rules.append(obj())

    return rules
