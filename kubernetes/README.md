# Kubernetes

## Manifests Layout

We're using a Kustomize-style layout. `base` contains the default k8s manifests, while the `overlays` directory provide kustomize overrides for particular environments. You'll need Rancher Desktop (preferred and provides docker, kubectl, etc...) or docker, minikube, and kubectl isntalled locally. Trivy is recommended for security scanning.

## Getting Started 

### Start app via CLI

Rancher Desktop
```console
kubectl apply -k kubernetes/overlays/dev/ui             # Apply the Kustomize template
kubectl get -k kubernetes/overlays/dev/ui               # Get resource info
kubectl port-forward services/dev-ui 4000:4000          # Make the service appear on localhost:4000
kubectl delete -k kubernetes/overlays/dev/ui            # Delete the resources
```

Minikube:
```console
docker build -t unified-graphics/ui:dev services/ui
minikube image load unified-graphics/ui:dev             # Load your local image into minikube
kubectl apply -k kubernetes/overlays/dev/ui             # Apply the Kustomize template
kubectl get -k kubernetes/overlays/dev/ui               # Get resource info
kubectl port-forward services/dev-ui 4000:4000          # Make the service appear on localhost:4000
kubectl delete -k kubernetes/overlays/dev/ui            # Delete the resources
```

### Security scanning

```console
trivy image --ignore-unfixed --severity CRITICAL,HIGH <imagename>
```
## Other Tips

Get deployment yaml output from cluster

```console
kubectl get deploy deploymentname -o yaml
```

Get logs
```console
kubectl logs --namespace <namespace> <pod>
```

Inspect ConfigMap Values
```console
kubectl describe --namespace <namespace> configmaps <map name>
```

Enter a pod
```console
kubectl exec --namespace <namespace> --stdin --tty <pod> -- /bin/bash
```
### Allow unprivileged binding to ports lower than 80 for Rancher Desktop

Rancher desktop automatically starts a traefik ingress that tries to bind to `80` and `443`. On Linux, ports below 1024 are privileged so the ingress won't work.

```console
sudo sysctl net.ipv4.ip_unprivileged_port_start=80

# Or to make the change permanent
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80
```

And restart Rancher Desktop.