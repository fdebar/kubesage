helm upgrade --install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
# TODO: We need to test it's replaced by Alloy
#helm upgrade --install opentelemetry-collector open-telemetry/opentelemetry-collector \
#   --set image.repository="otel/opentelemetry-collector-k8s" \
#   --set mode=deployment
helm upgrade --install loki grafana-community/loki -n monitoring
helm upgrade --install tempo grafana-community/tempo -n monitoring
helm upgrade --install alloy grafana/alloy -n monitoring
helm upgrade --install grafana grafana-community/grafana -n monitoring
helm upgrade --install kubesage ./deploy/kubesage -n kubesage --create-namespace