# envcage

> A CLI tool to validate, snapshot, and diff environment variable sets across deployments.

---

## Installation

```bash
pip install envcage
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated installs:

```bash
pipx install envcage
```

---

## Usage

**Snapshot your current environment:**
```bash
envcage snapshot --output snapshot.json
```

**Validate env vars against a schema:**
```bash
envcage validate --schema .envcage.yml
```

**Diff two snapshots to spot changes between deployments:**
```bash
envcage diff snapshot-staging.json snapshot-production.json
```

**Example output:**
```
+ NEW_FEATURE_FLAG=true
- DEPRECATED_API_KEY
~ DATABASE_URL  [changed]
```

---

## Configuration

Define required and optional variables in `.envcage.yml`:

```yaml
required:
  - DATABASE_URL
  - SECRET_KEY
optional:
  - DEBUG
  - LOG_LEVEL
```

---

## License

This project is licensed under the [MIT License](LICENSE).