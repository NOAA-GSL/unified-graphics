# Kubernetes

## Manifests Layout

We're using a Kustomize-style layout. `base` contains the default k8s manifests, while the other directories provide kustomize overrides for particular environments. You'll need docker, minikube, and kubectl isntalled locally. Trivy is recommended for security scanning.

### Start app via CLI

```console
cd services/ui && docker build -t graphics-ui:dev . && cd ../..
#OR - docker build -t graphics-ui:dev services/ui
minikube image load graphics-ui:dev 			# Load your local image into minikube
kubectl apply -k kubernetes/dev/ui 				# Apply the Kustomize template
kubectl get -k kubernetes/dev/ui 				# Get resource info
kubectl port-forward services/dev-ui 4000:4000 	# Make the service appear on localhost:4000
kubectl delete -k kubernetes/dev/ui 			# Delete the resources
```

### Security scanning

```console
trivy image --ignore-unfixed --severity CRITICAL,HIGH <imagename>
```

### Ingress
start with nginx ingress?
- need an ingress controller for the entire cluster
	- AWS has one (https://github.com/kubernetes-sigs/aws-load-balancer-controller#readme)
		- services -> NLB's
		- Ingress's -> ALB's
	- could look at nginx for the other
- ingress controllers make ingress resources work
- ingress resources target nodePort's?
- https://medium.com/google-cloud/understanding-kubernetes-networking-services-f0cb48e4cc82
- https://kubernetes.io/docs/concepts/services-networking/
- https://www.eksworkshop.com/beginner/130_exposing-service/ingress/

## Tips

Get deployment yaml output from cluster

```console
kubectl get deploy deploymentname -o yaml
```

### TODO

- figure out how to do networking
	- Load balancer or an ingress?
- figure out how to install ArgoCD
- Do we need a service mesh like Istio/Traefik/linkerd?
	- look at linkerd
- How do we deploy Jaeger, Prometheus, & Grafana?

### To mull

- We're using Kustomize - should we use Helm?
	- personally, it seems like sticking with vanilla k8s manifests would be good
- How does using Argo work for VLab?
	- They want to issue an eventbridge event from ECR to trigger deployment. I'd like there to be a record of the manifests in git somewhere.
		- can the event bridge event trigger a service to modify/create some manifests in a git repo, commit & push, and then apply them? (Or have argo apply them?)
- How do preview environments work?
- How do we access the "internal" services like Argo, Jaeger, Grafana, etc...?


