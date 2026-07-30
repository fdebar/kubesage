# KubeSage Examples

This directory contains Kubernetes manifests used to validate KubeSage detection rules.

Each manifest reproduces a specific Kubernetes issue or operational scenario that should trigger one or more findings during an analysis.

## Available Scenarios

| Manifest                             | Expected Finding        |
| ------------------------------------ | ----------------------- |
| `crashloop.yaml`                     | CrashLoopBackOff        |
| `pending.yaml`                       | Pending Pod             |
| `image-pull-err.yaml`                | ImagePullBackOff        |
| `restarts.yaml`                      | High Restart Count      |
| `high-cpu.yaml`                      | High CPU Usage          |
| `cpu_throttling.yaml`                | CPU Throttling          |
| `high-memory.yaml`                   | High Memory Usage       |
| `oomkilled.yaml`                     | OOMKilled               |
| `readiness-fail.yaml`                | Readiness Probe Failure |
| `liveness-fail.yaml`                 | Liveness Probe Failure  |
| `error-logs.yaml`                    | Error Logs Detection    |
| `memory-pressure.yaml`               | Node Memory Pressure    |
| `disk-pressure.yaml`                 | Node Disk Pressure      |

## Usage

Deploy a scenario:

```bash
kubectl apply -f examples/crashloop.yaml
```

Run KubeSage against the affected namespace or pod.

When finished, remove the resources:

```bash
kubectl delete -f examples/crashloop.yaml
```

## Notes

* These manifests are intended for development and testing only.
* Some scenarios intentionally create failing or resource-intensive workloads.
* Deploy node pressure scenarios only on disposable or non-production clusters.
