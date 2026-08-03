from pydantic import BaseModel


class ClusterInfo(BaseModel):
    """Represents the Kubernetes cluster information."""

    name: str
    kubernetes_version: str
    node_count: int
    namespace_count: int
    api_server: str
