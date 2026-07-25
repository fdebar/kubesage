from typing import Protocol

from kubesage.models.kubernetes import KubernetesSnapshot


class KubernetesProvider(Protocol):
    def collect(
        self,
        namespace: str,
        pod: str,
    ) -> KubernetesSnapshot:
        """Collect Kubernetes information for a pod."""
        ...
