  ## Deployment
  
  gcloud builds submit --region=us-central1 --tag  us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-client:latest --project=mcp-openfda-server
  
  gcloud run deploy  mcp-client --image us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-client:latest --region=us-central1 --allow-unauthenticated
  --project=mcp-openfda-server

  gcloud run deploy mcp-client \
    --image us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-client:latest \
    --region=us-central1 \
    --allow-unauthenticated \
    --project=mcp-openfda-server \
    --set-env-vars="GEMINI_API_KEY=api_key