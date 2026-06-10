# Cloud Run Deployment

This repository now has the minimum container scaffold needed for Cloud Run.

## Build

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/product-monograph-champ
```

## Deploy

```bash
gcloud run deploy product-monograph-champ \
  --image gcr.io/PROJECT_ID/product-monograph-champ \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --set-env-vars DEFAULT_PROVIDER=openrouter,APP_NAME="Product Monograph Champ" \
  --set-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest,DEEPSEEK_API_KEY=DEEPSEEK_API_KEY:latest,GROQ_API_KEY=GROQ_API_KEY:latest,OPENROUTER_API_KEY=OPENROUTER_API_KEY:latest
```

## Notes

- Streamlit starts with:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port ${PORT}
```

- Cloud Run injects `PORT` at runtime.
- Secrets are injected from Secret Manager.
- Generated files remain on ephemeral container storage unless external persistence is added later.
