# PersonaOps

Execution loop is fixed:

1. PRD (`PRD.md`)
2. SDD (`SDD.md`)
3. Implementation (`implementation/` + schemas/policies/flows)
4. Verification (`implementation/tests/` + evals)
5. Iterate

## Quickstart (local)

```bash
cd personaops
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic pytest pyyaml
uvicorn implementation.control_plane:app --reload --port 8081
```

Health check:

```bash
curl http://localhost:8081/health
```

Run tests:

```bash
pytest implementation/tests -q
```

Key API routes:
- `POST /adapters/discord/inbound`
- `POST /approvals/request`
- `GET /approvals`, `GET /approvals/{approval_id}`
- `POST /approvals/{approval_id}/decision`
- `POST /outbox/enqueue`
- `POST /outbox/process_once`
