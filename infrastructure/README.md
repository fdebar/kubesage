# Prometheus Installation

This guide will walk you through the steps to install Prometheus on your Kubernetes cluster using Helm and how to access its web interface.

## Prerequisites

- [Helm](https://helm.sh/docs/intro/install/) installed on your machine.
- `kubectl` configured to communicate with your Kubernetes cluster.

## 1. Install Prometheus using Helm

First, add the Prometheus Community Helm repository and update your local Helm chart repository cache:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

Next, install the `kube-prometheus-stack` chart into a new namespace called `monitoring`:

```bash
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

## 2. Access the Prometheus Web Interface

Once the installation is complete and the pods are running, you can access the Prometheus web interface using port-forwarding.

Run the following command to forward your local port `9090` to the Prometheus service in the cluster:

```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
```

Open your web browser and navigate to:
[http://localhost:9090](http://localhost:9090)

You should now see the Prometheus web interface!

---

KubeSage uses Grafana Tempo Distributed deployed via Helm with OpenTelemetry Collector (Alloy)

## 2. Install OpenTelemetry Collector

helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

helm install opentelemetry-collector open-telemetry/opentelemetry-collector \
  --set image.repository="otel/opentelemetry-collector-k8s" \
  --set mode=deployment

## 3. Install Grafana

helm repo add grafana-community https://grafana.github.io/helm-charts
helm repo update

helm install grafana grafana-community/grafana \
  --namespace monitoring \
  --create-namespace \
  -f infrastructure/monitoring/grafana-values.yaml

helm install loki grafana-community/loki \
  --namespace monitoring \
  --create-namespace \
  -f infrastructure/monitoring/loki-values.yaml

helm install tempo grafana-community/tempo \
  --namespace monitoring \
  --create-namespace \
  -f infrastructure/monitoring/tempo-values.yaml

helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm install alloy grafana/alloy \
  --namespace monitoring \
  --create-namespace