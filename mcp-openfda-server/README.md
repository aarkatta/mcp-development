uv run server.py

Deployment
gcloud init

## Artifact repository to store the container image.
gcloud artifacts repositories create remote-mcp-servers \
  --repository-format=docker \
  --location=us-central1 \
  --description="Repository for remote MCP servers" \
  --project=mcp-openfda-server

  ## Build the image
  gcloud builds submit --region=us-central1 --tag us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-server:latest

  
## Deploy MCP server t ocloud run
gcloud run deploy mcp-server \
  --image us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-server:latest \
  --region=us-central1 \
  --no-allow-unauthenticated

## MCP server URL
Service [mcp-server] revision [mcp-server-00004-b62] has been deployed and is serving 100 percent of traffic.
Service URL: https://mcp-server-722021783439.us-central1.run.app

  for role in roles/viewer roles/serviceusage.serviceUsageConsumer; do
  gcloud projects add-iam-policy-binding mcp-openfda-server \
    --member="user:aarkatta@gmail.com" \
    --role="$role"
done


