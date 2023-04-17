# Kubernetes

## Manifests Layout

We're using a Kustomize-style layout. `base` contains the default k8s manifests, while the `overlays` directory provide kustomize overrides for particular environments. You'll need Rancher Desktop (preferred and provides docker, kubectl, etc...) or you can try using docker, minikube, and kubectl installed locally. Trivy is recommended for security scanning.

## Getting Started

### Start app via CLI

Currently, you will need to create a `kuberenetes/overlays/dev/api/.env` file with the required AWS keys to pass in to the container. That file should look like so:

```shell
AWS_ACCESS_KEY_ID=<aws access key value>
AWS_SECRET_ACCESS_KEY=<aws secret access key value>
AWS_SESSION_TOKEN=<aws session token value>
```

Rancher Desktop

```console
kubectl create namespace ug
kubectl -n ug apply -k kubernetes/overlays/dev                # Apply the Kustomize templates for the UI and API services
# You should be able to visit the service at http://unified-graphics.127.0.0.1.nip.io - if you're on Linux, see the note on allowing port 80 below
kubectl -n ug get -k kubernetes/overlays/dev                  # Get resource info
kubectl -n ug delete -k kubernetes/overlays/dev               # Delete the resources
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
