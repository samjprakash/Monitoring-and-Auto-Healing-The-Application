minikube

To Start :  minikube start --memory=6144 --cpus=4 --driver=docker


Install using Helm

Add helm repo;
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

Update helm repo,
helm repo update

Install helm.,
helm install prometheus prometheus-community/prometheus

Expose Prometheus Service

This is required to access prometheus-server using your browser.
kubectl expose service prometheus-server --type=NodePort --target-port=9090 --name=prometheus-server-ext

Then,
kubectl get pods
kubectl get svc



Install using Helm

Add helm repo.,
helm repo add grafana https://grafana.github.io/helm-charts

Update helm repo.,
helm repo update

Install helm.,
helm install grafana grafana/grafana

Expose Grafana Service

kubectl expose service grafana — type=NodePort — target-port=3000 — name=grafana-ext



To have Password For Grafana:
base64 : kubectl get secret --namespace default grafana -o jsonpath="{.data.admin-password}" | 
    ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }




For state Metrics:
kubectl expose service prometheus-kube-state-metrics --type=NodePort --target-port=8080 --name=prometheus-kube-state-metrics-ext

then 
kubectl get svc
kubectl get pods


To open the Services:
minikube service prometheus-kube-state-metrics-ext

minikube service prometheus-server-ext

minikube service Grafana


 
