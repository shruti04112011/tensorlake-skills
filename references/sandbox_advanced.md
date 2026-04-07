<!--
Source:
  - https://docs.tensorlake.ai/sandboxes/skills-in-sandboxes.md
  - https://docs.tensorlake.ai/sandboxes/ai-code-execution.md
  - https://docs.tensorlake.ai/sandboxes/data-analysis.md
  - https://docs.tensorlake.ai/sandboxes/cicd-build.md
SDK version: tensorlake 0.4.39
Last verified: 2026-04-07
-->

# TensorLake Sandbox Advanced Patterns

## Skills in Sandboxes

Install agent skill files into sandbox images so coding agents (Claude Code, Codex, Cursor, etc.) can discover TensorLake SDK references at startup.

### Agent Discovery Paths

| Agent | Skill Location |
|-------|---------------|
| Claude Code | `~/.claude/skills/<name>/SKILL.md` |
| OpenAI Codex | `~/.agents/skills/<name>/SKILL.md` or `AGENTS.md` in working dir |
| Google ADK | Loaded via `load_skill_from_dir()` |
| Cursor | `.cursor/rules/*.mdc` |
| Cline | `.clinerules/` |
| Windsurf | `.windsurf/rules/*.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |

### Installation via Skills CLI (Multi-Agent)

```python
from tensorlake.applications import Image

SKILLS_IMAGE = (
    Image(name="with-skills", base_image="python:3.11-slim")
    .run("apt-get update && apt-get install -y nodejs npm")
    .run("npm install -g skills")
    .run("skills add tensorlakeai/tensorlake-skills --all -y --copy")
    .run("pip install tensorlake")
)
```

Flags: `--all` deploys to all detected agents, `-y` non-interactive, `--copy` avoids symlink issues in containers.

### Claude Code Specific Setup

```python
from tensorlake.applications import Image

CLAUDE_CODE_IMAGE = (
    Image(name="claude-code-skills", base_image="python:3.11-slim")
    .run("apt-get update && apt-get install -y git")
    .run("git clone https://github.com/tensorlakeai/tensorlake-skills /tmp/tensorlake-skills")
    .run("mkdir -p /root/.claude/skills/tensorlake && cp -r /tmp/tensorlake-skills/SKILL.md /tmp/tensorlake-skills/references /root/.claude/skills/tensorlake/")
    .run("rm -rf /tmp/tensorlake-skills")
    .run("pip install tensorlake")
)
```

### Template Creation

```bash
tl sbx create-template template.py --name claude-code-skills
tl sbx new --template claude-code-skills
```

### Runtime Installation (SDK)

```python
from tensorlake.sandbox import SandboxClient

client = SandboxClient()

with client.create_and_connect() as sandbox:
    sandbox.run("bash", ["-c", "apt-get update && apt-get install -y nodejs npm"])
    sandbox.run("bash", ["-c", "npm install -g skills"])
    sandbox.run("bash", ["-c", "skills add tensorlakeai/tensorlake-skills --all -y --copy"])

    result = sandbox.run("find", ["/", "-name", "SKILL.md", "-type", "f", "-not", "-path", "*/node_modules/*"])
    print(result.stdout)
```

---

## AI Code Execution

Use sandboxes as LLM tool-call targets for safe code execution.

### Architecture Pattern

1. Create a single sandbox at session start
2. Maintain it across multiple tool calls (state persists)
3. Close when done

```python
sandbox = tl_client.create_and_connect(
    cpus=1.0,
    memory_mb=1024,
    timeout_secs=600,
    allow_internet_access=False  # important for untrusted code
)

result = sandbox.run("python", ["-c", code])
# result.stdout, result.stderr, result.exit_code
```

### Snapshots for Pre-installed Dependencies

```python
snapshot = tl_client.snapshot_and_wait(sandbox.sandbox_id)
sandbox = tl_client.create_and_connect(snapshot_id=snapshot.snapshot_id)
```

### Integration Patterns

**Claude (Anthropic):** Define a `run_code` tool in the tools schema. Detect `tool_use` blocks in responses, execute via `sandbox.run()`, return results as `tool_result`.

**OpenAI Function Calling:** Structure sandbox as a function definition. Parse `tool_calls`, execute, append results to message history.

**OpenAI Agents SDK:** Wrap sandbox execution with `@function_tool` decorator.

### Best Practices

- **Reuse sandboxes** — creating new ones per tool call adds cold-start latency and loses state
- **Set `allow_internet_access=False`** for untrusted code
- **Pre-install deps via snapshots** or let agents `pip install` on demand
- Files and packages persist across calls, but each Python invocation is a fresh process (re-import required)

---

## Data Analysis

Run parallel data analysis and model benchmarking in isolated sandboxes.

### Pattern: Parallel Benchmarking

```python
import asyncio
from tensorlake.sandbox import SandboxClient

client = SandboxClient()

async def benchmark_model(model_name, import_path):
    with client.create_and_connect() as sandbox:
        sandbox.run("pip", ["install", "scikit-learn", "--break-system-packages"])
        code = f"""
import json
from {import_path} import {model_name}
# ... train, evaluate, output JSON
print(json.dumps(results))
"""
        result = sandbox.run("python", ["-c", code])
        return json.loads(result.stdout)

async def main():
    tasks = {
        "RandomForest": "sklearn.ensemble",
        "GradientBoosting": "sklearn.ensemble",
    }
    results = await asyncio.gather(*[
        benchmark_model(name, path) for name, path in tasks.items()
    ])
```

Use snapshots to avoid re-installing dependencies on each run.

---

## CI/CD Build Pipelines

Use sandboxes as ephemeral, isolated build containers.

### Pattern: Mini-CI Pipeline

```python
from tensorlake.sandbox import SandboxClient

client = SandboxClient()

with client.create_and_connect() as sandbox:
    # Upload project files
    sandbox.write_file("/workspace/project/src/app.py", source_bytes)
    sandbox.write_file("/workspace/project/tests/test_app.py", test_bytes)
    sandbox.write_file("/workspace/project/requirements.txt", req_bytes)

    # Install dependencies
    result = sandbox.run("pip", [
        "install", "-r", "/workspace/project/requirements.txt",
        "--user", "--break-system-packages"
    ], env={"PYTHONPATH": "/workspace/project/src"})

    # Run tests
    result = sandbox.run("python", ["-m", "pytest", "tests/"],
        working_dir="/workspace/project",
        env={"PYTHONPATH": "/workspace/project/src"})
    print(f"Exit: {result.exit_code}\nSTDOUT:\n{result.stdout}")

    # Build artifacts
    result = sandbox.run("python", ["-m", "build"],
        working_dir="/workspace/project")

    # Retrieve artifacts
    artifact = sandbox.read_file("/workspace/project/dist/package.tar.gz")
```

**Key `sandbox.run()` parameters:**
- `env` — inject environment variables
- `working_dir` — set working directory for the command
