from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
GENOME_SCRIPT = SKILLS_ROOT / "codex-project-memory" / "scripts" / "generate_genome.py"


def run_genome(project_root: Path, *args: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(GENOME_SCRIPT), "--project-root", str(project_root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_generate_genome_writes_all_sections_for_sample_repo(tmp_path: Path) -> None:
    write(
        tmp_path / "package.json",
        json.dumps(
            {
                "dependencies": {"express": "^4.19.0", "mongoose": "^8.0.0"},
                "devDependencies": {"jest": "^29.0.0"},
            }
        ),
    )
    write(tmp_path / ".gitignore", ".env\nnode_modules/\n")
    write(tmp_path / ".env.example", "JWT_SECRET=example-secret-value\n")
    write(
        tmp_path / "src" / "app.js",
        """
        const express = require('express');
        const cors = require('cors');
        const rateLimit = require('express-rate-limit');
        const router = require('./routes/auth.routes');
        const app = express();
        app.use(cors());
        app.use(rateLimit());
        app.use('/api', router);
        app.get('/health', authMiddleware, (req, res) => res.json({ ok: true }));
        """,
    )
    write(
        tmp_path / "src" / "routes" / "auth.routes.js",
        """
        const router = require('express').Router();
        const jwt = require('jsonwebtoken');
        router.post('/login', (req, res) => res.json({ token: jwt.sign({}, 'dev-secret-token') }));
        module.exports = router;
        """,
    )
    write(
        tmp_path / "src" / "models" / "user.model.js",
        """
        const mongoose = require('mongoose');
        const UserSchema = new mongoose.Schema({ email: String, passwordHash: String });
        module.exports = mongoose.model('User', UserSchema);
        """,
    )
    write(
        tmp_path / "tests" / "auth.test.js",
        """
        describe('auth', () => {
          it('logs in', () => expect(true).toBe(true));
        });
        """,
    )
    write(
        tmp_path / ".github" / "workflows" / "quality.yml",
        """
        name: quality
        on: [push]
        jobs:
          test:
            runs-on: ubuntu-latest
        """,
    )

    payload = run_genome(tmp_path, "--format", "json")
    genome_path = tmp_path / ".codex" / "context" / "genome.md"
    genome_text = genome_path.read_text(encoding="utf-8")

    assert payload["status"] == "ok"
    assert payload["sections_scanned"] == ["architecture", "api", "data", "security", "tests", "file_map"]
    assert genome_path.exists()
    assert "# Project Genome:" in genome_text
    assert "## 1. Architecture Overview" in genome_text
    assert "## 2. API Surface" in genome_text
    assert "## 3. Data Layer" in genome_text
    assert "## 4. Security Posture" in genome_text
    assert "## 5. Test Coverage Map" in genome_text
    assert "## 6. File Map" in genome_text
    assert "/health" in genome_text or "/login" in genome_text
    assert "mongoose" in genome_text.lower()
    assert ".github/workflows" in genome_text


def test_generate_genome_supports_subset_sections_and_json_output(tmp_path: Path) -> None:
    write(
        tmp_path / "app.py",
        """
        from fastapi import FastAPI
        app = FastAPI()

        @app.get('/health')
        def health():
            return {'ok': True}
        """,
    )
    write(tmp_path / ".gitignore", ".env\n")
    write(tmp_path / ".env.example", "API_KEY=dev-secret-token\n")

    payload = run_genome(tmp_path, "--sections", "api,security", "--format", "json")
    genome_text = (tmp_path / ".codex" / "context" / "genome.md").read_text(encoding="utf-8")

    assert payload["status"] == "ok"
    assert payload["sections_scanned"] == ["api", "security"]
    assert set(payload["sections"].keys()) == {"api", "security"}
    assert "## 1. API Surface" in genome_text
    assert "## 2. Security Posture" in genome_text
    assert "Architecture Overview" not in genome_text


def test_generate_genome_handles_empty_repo(tmp_path: Path) -> None:
    payload = run_genome(tmp_path, "--format", "json")
    genome_text = (tmp_path / ".codex" / "context" / "genome.md").read_text(encoding="utf-8")

    assert payload["status"] == "ok"
    assert payload["total_files"] == 0
    assert "Not detected" in genome_text
