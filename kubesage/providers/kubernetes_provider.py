from typing import Protocol

from kubesage.models.kubernetes_snapshot import KubernetesSnapshot


class KubernetesProvider(Protocol):
    def collect(
        self,
        namespace: str,
        pod: str,
        expected_pod_uid: str | None = None,
    ) -> KubernetesSnapshot:
        """Collect Kubernetes information for a pod."""
        ...
