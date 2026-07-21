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


----


kube-prometheus-stack has been installed. Check its status by running:
  kubectl --namespace monitoring get pods -l "release=monitoring"

Get Grafana 'admin' user password by running:

  kubectl --namespace monitoring get secrets monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo

Access Grafana local instance:

  export POD_NAME=$(kubectl --namespace monitoring get pod -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=monitoring" -oname)
  kubectl --namespace monitoring port-forward $POD_NAME 3000

Get your grafana admin user password by running:

  kubectl get secret --namespace monitoring -l app.kubernetes.io/component=admin-secret -o jsonpath="{.items[0].data.admin-password}" | base64 --decode ; echo


Visit https://github.com/prometheus-operator/kube-prometheus for instructions on how to create & configure Alertmanager and Prometheus instances using the Operator.