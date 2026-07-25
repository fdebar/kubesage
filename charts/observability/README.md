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

helm upgrade --install kubesage ./charts/kubesage \
  --namespace kubesage \
  --create-namespace \
  --set image.repository=kubesage \
  --set image.tag=d5746a7 \
  --set openai.apiKey=ollama \
  --set openai.endpoint=http://host.minikube.internal:11434/v1 \
  --set openai.model=qwen2.5-coder:14b \
  -f ./charts/kubesage/values-dev.yaml