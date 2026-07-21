from kubernetes import client, config
from config import settings, logger
from models.container import ContainerInfo
from models.incident import Incident
from models.events import Event
from kubernetes.client.exceptions import ApiException


class KubernetesService:

    def __init__(self):
        config.load_kube_config()
        self.v1 = client.CoreV1Api()

    def collect(self, namespace: str, pod: str) -> Incident:
        logger.info("Collecting pod %s/%s", namespace, pod)

        try:
            pod_info = self.v1.read_namespaced_pod(name=pod, namespace=namespace)
        except ApiException as e:
            if e.status == 404:
                raise ValueError(f"Pod {namespace}/{pod} cannot be found.")
            raise

        logs = self.v1.read_namespaced_pod_log(
            name=pod,
            namespace=namespace,
            tail_lines=settings.log_tail_lines,
        )

        if isinstance(logs, bytes):
            logs = logs.decode("utf-8")

        containers = []
        for c in pod_info.status.container_statuses or []:
            waiting_reason = None
            waiting_message = None

            if c.state and c.state.waiting:
                waiting_reason = c.state.waiting.reason
                waiting_message = c.state.waiting.message

            last_exit_code = None
            last_exit_reason = None

            if c.last_state and c.last_state.terminated:
                last_exit_code = c.last_state.terminated.exit_code
                last_exit_reason = c.last_state.terminated.reason

            containers.append(
                ContainerInfo(
                    name=c.name,
                    ready=c.ready,
                    restart_count=c.restart_count,
                    waiting_reason=waiting_reason,
                    waiting_message=waiting_message,
                    last_exit_code=last_exit_code,
                    last_exit_reason=last_exit_reason,
                )
            )

        events = self.v1.list_namespaced_event(
            namespace=namespace,
            field_selector=f"involvedObject.name={pod}",
        )

        logger.info("Incident collected successfully.")

        warnings = []
        for e in events.items:
            if e.type != "Warning":
                continue

            warnings.append(
                Event(
                    reason=e.reason,
                    message=e.message,
                    last_timestamp=str(e.last_timestamp) if e.last_timestamp else "",
                )
            )

        return Incident(
            namespace=namespace,
            pod=pod,
            phase=pod_info.status.phase,
            logs=logs,
            containers=containers,
            events=warnings,
        )
