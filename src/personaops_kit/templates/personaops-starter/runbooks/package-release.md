# PersonaOps Kit Release Runbook

## 1) Validate

```bash
make setup
make test
```

## 2) Build artifacts

```bash
make package
```

Expected artifacts:
- `dist/personaops_kit-<version>.tar.gz`
- `dist/personaops_kit-<version>-py3-none-any.whl`

## 3) Smoke inject

```bash
python -m pip install dist/personaops_kit-*.whl
TMP=$(mktemp -d)
personaops-kit inject "$TMP" --profile openclaw --name personaops --force
test -f "$TMP/personaops/implementation/control_plane.py"
```

## 4) Publish (optional)

```bash
python -m pip install twine
twine check dist/*
# twine upload dist/*
```

## 5) Target workspace injection

```bash
personaops-kit inject /path/to/workspace --profile openclaw --name personaops --force
# or
personaops-kit inject /path/to/workspace --profile nanobot --name personaops --force
```
