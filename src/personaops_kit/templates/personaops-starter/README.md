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
make setup
make run
```

Health check:

```bash
curl http://localhost:8081/health
```

Run tests:

```bash
make test
```

Seed GitHub issues (optional):

```bash
./scripts/bootstrap_issues.sh your-org/your-repo
```

Key API routes:
- `POST /adapters/discord/inbound`
- `POST /approvals/request`
- `GET /approvals`, `GET /approvals/{approval_id}`
- `POST /approvals/{approval_id}/decision`
- `POST /outbox/enqueue`
- `POST /outbox/process_once`

## Portable package (inject into other OpenClaw/NanoBot workspaces)

Build package:

```bash
python -m pip install --upgrade build
python -m build
```

Install locally:

```bash
python -m pip install dist/personaops_kit-*.whl
```

Create starter in any directory:

```bash
personaops-kit init /path/to/new/personaops
```

Inject into an existing workspace:

```bash
personaops-kit inject /path/to/workspace --profile openclaw --name personaops --force
```

NanoBot profile (same layout for now, reserved for future profile-specific paths):

```bash
personaops-kit inject /path/to/workspace --profile nanobot --name personaops --force
```
