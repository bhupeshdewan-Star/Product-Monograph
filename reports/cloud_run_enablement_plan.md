# Cloud Run Enablement Plan

Target: Google Cloud Run

Goal: move Release Gate RC1 from `FAIL` to `PASS` with the minimum deployment scaffolding.

## 1. Dockerfile Requirements

Minimum requirements for a Cloud Run-ready container image:

- Base image with Python 3.11+ support.
- Install system packages required by native Python wheels used in the repo, if any are needed at build time.
- Copy only the application source and dependency manifest.
- Install Python dependencies from `requirements.txt`.
- Expose the runtime port expected by Cloud Run.
- Launch the Streamlit app as the container entrypoint.

Minimum contract:

- image builds reproducibly
- container starts without shell interaction
- container listens on `0.0.0.0:$PORT`

## 2. Streamlit Startup Contract

Cloud Run should start the app with a single deterministic command:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port ${PORT}
```

Minimum requirements:

- no interactive prompts at startup
- no dependency on local terminal state
- app must boot even if optional API keys are absent

## 3. PORT Handling

Cloud Run injects `PORT` at runtime. The app container must:

- read `PORT` from the environment
- default safely if the variable is absent in local testing
- bind Streamlit to `0.0.0.0`
- avoid hardcoding `8501` in the container entrypoint

Recommended pattern:

- local default: `8501`
- Cloud Run: use injected `PORT`

## 4. Environment Variables

Minimum environment variables to support the active path:

- `DEFAULT_PROVIDER`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `DEEPSEEK_API_KEY`
- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENAI_MODEL`
- `ANTHROPIC_MODEL`
- `GOOGLE_MODEL`
- `DEEPSEEK_MODEL`
- `GROQ_MODEL`
- `OPENROUTER_MODEL`
- `LOCAL_MODEL`
- `MAX_TOKENS`
- `TEMPERATURE`
- `PUBMED_TIMEOUT`
- `FDA_TIMEOUT`
- `GOOGLE_SCHOLAR_TIMEOUT`
- `GENERATION_TIMEOUT`

Recommended Cloud Run extras:

- `APP_NAME`
- `APP_TAGLINE`
- `APP_VERSION`
- `APP_BUILD`
- `APP_THEME`

## 5. Secrets Strategy

Minimum strategy:

- Store provider API keys in Google Secret Manager.
- Bind secrets to the Cloud Run service as environment variables.
- Do not bake secrets into the image.
- Do not commit `.env` files for production.

Recommended secret separation:

- one secret per provider API key
- one secret per optional service token if added later

Operational notes:

- use the same environment variable names that `config.py` already reads
- keep local development on `.env` / `load_dotenv()`
- use Cloud Run secret injection in production

## 6. Storage Strategy

Current code writes runtime artifacts to local filesystem paths under `data/`:

- evidence cache
- generation history
- monograph outputs

Cloud Run has ephemeral filesystem storage, so minimum enablement requires one of the following:

### Option A: Minimal pass for RC1

- allow runtime writes to ephemeral local disk
- accept that exports, cache, and history are not durable across container restarts
- suitable only if Cloud Run is used for transient generation sessions

### Option B: Production-sane path

- mount or integrate a durable external store
- persist generated monographs and history to Cloud Storage or a database
- keep cache optional or move it to an external cache service later

Minimum change needed to pass RC1:

- document ephemeral storage limitation explicitly
- ensure the app does not crash when directories are recreated at startup

## 7. Cloud Run Deployment Commands

### Build image

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/product-monograph-champ
```

### Deploy service

```bash
gcloud run deploy product-monograph-champ \
  --image gcr.io/PROJECT_ID/product-monograph-champ \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --set-env-vars DEFAULT_PROVIDER=openrouter,APP_NAME="Product Monograph Champ" \
  --set-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest,DEEPSEEK_API_KEY=DEEPSEEK_API_KEY:latest,GROQ_API_KEY=GROQ_API_KEY:latest,OPENROUTER_API_KEY=OPENROUTER_API_KEY:latest
```

### Optional runtime tuning

```bash
gcloud run services update product-monograph-champ \
  --region REGION \
  --concurrency 1 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 3600
```

## 8. Risk Assessment

### Low risk

- Containerizing the existing Streamlit entrypoint.
- Binding Streamlit to `0.0.0.0:$PORT`.
- Injecting provider keys from Secret Manager.

### Medium risk

- Ephemeral filesystem behavior may cause loss of monograph outputs, cache, and history on restart.
- Large generation requests may exceed default Cloud Run time or memory settings.
- Outbound evidence-retrieval calls depend on external network availability.

### High risk

- Persistent storage is not yet designed for generated artifacts.
- The app assumes local filesystem paths for several runtime features.
- If a long monograph generation path exceeds Cloud Run request timeout, the user experience may degrade unless the service timeout is increased.

## Minimum Work to Move RC1 Toward PASS

1. Add a container build definition.
2. Start Streamlit on `0.0.0.0:$PORT`.
3. Externalize secrets with Secret Manager.
4. Accept or document ephemeral storage behavior, or add durable storage.
5. Set Cloud Run CPU/memory/timeout to match generation workload.

## Recommendation

Cloud Run is the best next deployment target after the container scaffold exists.

The minimum path to a pass is straightforward, but the current repository is missing the container and deployment scaffolding required to execute it.
