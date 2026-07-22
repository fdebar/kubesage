from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from utils.config import logger

_kube_config_loaded: bool | None = None


def _ensure_kube_config() -> bool:
    global _kube_config_loaded

    if _kube_config_loaded is not None:
        return _kube_config_loaded

    try:
        config.load_kube_config()
    except ConfigException as exc:
        logger.warning("Kubernetes config unavailable: %s", exc)
        _kube_config_loaded = False
        return False
    except Exception as exc:
        logger.warning("Failed to load Kubernetes config: %s", exc)
        _kube_config_loaded = False
        return False

    _kube_config_loaded = True
    return True


def create_core_v1_api() -> client.CoreV1Api | None:
    if not _ensure_kube_config():
        return None

    return client.CoreV1Api()


def create_custom_objects_api() -> client.CustomObjectsApi | None:
    if not _ensure_kube_config():
        return None

    return client.CustomObjectsApi()
