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

Run with Postgres backend (optional):

```bash
export PERSONAOPS_STORE_BACKEND=postgres
export PERSONAOPS_POSTGRES_DSN='postgresql://user:pass@localhost:5432/personaops'
# apply schema first
psql "$PERSONAOPS_POSTGRES_DSN" -f implementation/sql/001_init.sql
make run
```

Outbound sender modes:

```bash
# default (safe local mode)
export PERSONAOPS_OUTBOUND_MODE=mock

# webhook mode (real sends)
export PERSONAOPS_OUTBOUND_MODE=webhook
export PERSONAOPS_DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/...'
export PERSONAOPS_SLACK_WEBHOOK_URL='https://hooks.slack.com/services/...'

# openclaw CLI bridge mode (real sends through local OpenClaw runtime)
export PERSONAOPS_OUTBOUND_MODE=openclaw
export PERSONAOPS_OPENCLAW_CLI_PATH='openclaw'
export PERSONAOPS_OPENCLAW_CLI_TIMEOUT_SEC=20
```

Seed GitHub issues (optional):

```bash
./scripts/bootstrap_issues.sh your-org/your-repo
```

Optional gates/utilities:

```bash
# prompt regression gate (skips when OPENAI_API_KEY is missing)
make promptfoo

# local Postgres smoke
make postgres-up
make postgres-smoke
make postgres-down
```

Key API routes:
- `POST /adapters/discord/inbound`
- `POST /approvals/request`
- `GET /approvals`, `GET /approvals/{approval_id}`
- `POST /approvals/{approval_id}/decision`
- `POST /outbox/enqueue`
- `POST /outbox/process_once`
- `GET /temporal/bootstrap`

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

Install with optional extras:

```bash
# Langfuse trace integration
python -m pip install 'dist/personaops_kit-*.whl[observability]'

# Temporal workflow integration
python -m pip install 'dist/personaops_kit-*.whl[orchestration]'
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
