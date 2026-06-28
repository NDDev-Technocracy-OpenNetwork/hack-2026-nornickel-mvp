# fa.nddev.asia Deployment Notes

Target host:

```text
ssh server-nddev
public URL: https://fa.nddev.asia
```

The repository is prepared for container deployment with Docker Compose:

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Required runtime values stay outside git:

- `OPENAI_API_KEY`
- `LITELLM_API_BASE`, when using a non-default OpenAI-compatible gateway
- any future OCR service credentials

Current Compose services:

- `web`: Nginx serving the React build and proxying `/api/` to FastAPI.
- `api`: FastAPI application.
- `qdrant`: vector database placeholder for the retrieval adapter.

Before production rollout, verify:

```bash
docker compose config
docker compose up --build -d
curl -fsS http://127.0.0.1:5173/
curl -fsS http://127.0.0.1:8000/health
```

The current scaffold does not include TLS termination or reverse-proxy configuration for
`fa.nddev.asia`; that should be handled by the server-level proxy already managing the domain.
