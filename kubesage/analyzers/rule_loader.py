import importlib
import inspect
import pkgutil

import kubesage.analyzers.rules as rules_package
from kubesage.analyzers.rules.base import BaseRule


def discover_rules() -> list[BaseRule]:
    """Discover all rules in the rules package."""

    package_path = rules_package.__path__
    package_name = rules_package.__name__
    rules: list[BaseRule] = []

    for module in pkgutil.walk_packages(package_path, prefix=f"{package_name}."):
        module_name = module.name
        if module_name.endswith((".__init__", ".base")):
            continue

        mod = importlib.import_module(module_name)
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if (
                issubclass(obj, BaseRule)
                and obj is not BaseRule
                and obj.__module__ == mod.__name__
            ):
                rules.append(obj())

    return rules
