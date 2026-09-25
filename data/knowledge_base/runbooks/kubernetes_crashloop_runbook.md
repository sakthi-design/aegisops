# Runbook: Kubernetes OOMKilled & CrashLoopBackOff

## Symptoms
- Pod state `CrashLoopBackOff`, exit code 137 (SIGKILL by Linux OOM killer)
- Service response degraded, 502 Bad Gateway at ingress

## Mitigation
1. Check dmesg / k8s events: `kubectl describe pod -l app=order-service`
2. Review memory cgroup limit: `resources.limits.memory`
3. Roll back bad deployment immediately: `kubectl rollout undo deployment/order-service`
