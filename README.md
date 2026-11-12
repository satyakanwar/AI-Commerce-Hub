# AI Commerce Hub

A learning/portfolio AI e-commerce microservices project.

## Stack
- React + Vite frontend
- FastAPI product, order and AI services
- PostgreSQL for products/orders
- MongoDB for chat and search activity
- Docker Compose for local orchestration
- Kubernetes manifests for AKS deployment

## Prerequisites
- VS Code
- Git
- Docker Desktop (Windows/Mac) or Docker Engine + Compose (Linux)
- Node.js 20.19+ (only needed if running frontend outside Docker)
- Python 3.11+ (only needed if running services outside Docker)

## Run in VS Code
1. Extract this folder and open `ai-commerce-hub` in VS Code.
2. Open Terminal -> New Terminal.
3. Run:
   ```bash
   docker compose up --build
   ```
4. Open http://localhost:5173
5. API health checks:
   - Product: http://localhost:8001/health
   - Order: http://localhost:8002/health
   - AI: http://localhost:8003/health
6. Stop:
   ```bash
   docker compose down
   ```
   Remove database volumes too (destructive):
   ```bash
   docker compose down -v
   ```

The product service seeds sample products on first startup. Orders and products are stored in PostgreSQL. Chat messages/search activity are stored in MongoDB.

## Test APIs
```bash
curl http://localhost:8001/products
curl -X POST http://localhost:8002/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Demo User","items":[{"product_id":1,"quantity":1}]}'
curl -X POST http://localhost:8003/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","message":"Suggest a laptop under 60000"}'
curl "http://localhost:8003/search?q=cheap%20phone%20with%20good%20camera"
```

## Push to GitHub
Create an empty repository on GitHub, then:
```bash
git init
git add .
git commit -m "Initial AI Commerce Hub microservices application"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-commerce-hub.git
git push -u origin main
```
Do not commit `.env` files, passwords, API keys, or cloud credentials.

## Docker Hub
Build and tag after local testing:
```bash
docker build -t YOUR_DOCKERHUB_USERNAME/commerce-product:1.0 ./services/product
docker build -t YOUR_DOCKERHUB_USERNAME/commerce-order:1.0 ./services/order
docker build -t YOUR_DOCKERHUB_USERNAME/commerce-ai:1.0 ./services/ai
docker build -t YOUR_DOCKERHUB_USERNAME/commerce-frontend:1.0 ./frontend
docker push YOUR_DOCKERHUB_USERNAME/commerce-product:1.0
docker push YOUR_DOCKERHUB_USERNAME/commerce-order:1.0
docker push YOUR_DOCKERHUB_USERNAME/commerce-ai:1.0
docker push YOUR_DOCKERHUB_USERNAME/commerce-frontend:1.0
```

## Kubernetes / AKS
1. Create an AKS cluster in Azure and connect:
   ```bash
   az login
   az aks get-credentials --resource-group YOUR_RESOURCE_GROUP --name YOUR_AKS_CLUSTER
   kubectl get nodes
   ```
2. Edit `k8s/deployment.yaml`: replace `YOUR_DOCKERHUB_USERNAME` with your Docker Hub username.
3. Apply resources:
   ```bash
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/secrets.example.yaml
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```
4. Wait for the public IP:
   ```bash
   kubectl get services -w
   ```
   Open the `EXTERNAL-IP` of `frontend-service` in your browser.
5. Check:
   ```bash
   kubectl get deployments
   kubectl get pods
   kubectl get svc
   kubectl logs deployment/ai-service
   ```

`secrets.example.yaml` contains demo-only credentials. Replace them before any real deployment. For production, use Azure Key Vault, managed identities, TLS ingress, persistent managed database services, resource limits, probes, and proper authentication. The included Kubernetes database deployments use ephemeral container storage for classroom/demo use; they are not production-persistent.
