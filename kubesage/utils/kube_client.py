import structlog
from kubernetes import client, config, watch
from kubernetes.config.config_exception import ConfigException

logger = structlog.get_logger(__name__)
_kube_config_loaded: bool | None = None


def _ensure_kube_config() -> bool:
    global _kube_config_loaded

    if _kube_config_loaded is not None:
        return _kube_config_loaded

    try:
        config.load_incluster_config()
        _kube_config_loaded = True
    except ConfigException:
        try:
            config.load_kube_config()
            logger.info("Loaded local kubeconfig.")
            _kube_config_loaded = True
        except ConfigException as exc:
            logger.warning("Failed to load kubeconfig: %s", exc)
            _kube_config_loaded = False

    return _kube_config_loaded


def create_core_v1_api() -> client.CoreV1Api:
    if not _ensure_kube_config():
        logger.exception("kubernetes_client_initialization_failed")
        raise RuntimeError("Unable to initialize Kubernetes client")

    return client.CoreV1Api()


def create_custom_objects_api() -> client.CustomObjectsApi:
    if not _ensure_kube_config():
        logger.exception("kubernetes_client_initialization_failed")
        raise RuntimeError("Unable to initialize Kubernetes client")

    return client.CustomObjectsApi()


def create_watch() -> watch.Watch:
    return watch.Watch()
