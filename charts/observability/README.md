# Install

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana-community https://grafana.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts

helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
    -n monitoring \
    --create-namespace \
    -f kube-prometheus-stack.yaml

helm install grafana grafana-community/grafana \
  --namespace monitoring \
  --create-namespace \
  -f grafana-values.yaml

helm install loki grafana-community/loki \
  --namespace monitoring \
  --create-namespace \
  -f loki-values.yaml

helm install tempo grafana-community/tempo \
  --namespace monitoring \
  --create-namespace \
  -f tempo-values.yaml

helm install alloy grafana/alloy \
  --namespace monitoring \
  --create-namespace