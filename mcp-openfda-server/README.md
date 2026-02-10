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
  --allow-unauthenticated





