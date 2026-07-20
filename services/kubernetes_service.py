from kubernetes import client, config


class KubernetesService:

    def __init__(self):
        config.load_kube_config()
        self.v1 = client.CoreV1Api()