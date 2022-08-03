# Kubernetes

## Manifests Layout

We're using a Kustomize-style layout. `base` contains the default k8s manifests, while the `overlays` directory provide kustomize overrides for particular environments. You'll need Rancher Desktop (preferred and provides docker, kubectl, etc...) or you can try using docker, minikube, and kubectl installed locally. Trivy is recommended for security scanning.

## Getting Started

### Start app via CLI

Currently, you will need to update the path used by the `hostPath` volume in `kubernetes/overlays/dev/api/patch_add_volume.yaml` to match where you've put data on your host system. (If you don't want to use `/tmp`)

Rancher Desktop
```console
kubectl apply -k kubernetes/overlays/dev                # Apply the Kustomize templates for the UI and API services
# You should be able to visit the service on localhost:80 - if you're on Linux, see the note on allowing port 80 below
kubectl get -k kubernetes/overlays/dev                  # Get resource info
kubectl delete -k kubernetes/overlays/dev               # Delete the resources
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
echo "net.ipv4.ip_unprivileged_port_start=80" | sudo tee /etc/sysctl.d/99-custom-unprivileged-port.conf
sysctl -p /etc/sysctl.d/99-custom-unprivileged-port.conf
```

And restart Rancher Desktop.
