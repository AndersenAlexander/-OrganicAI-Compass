from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _powershell() -> str:
    executable = shutil.which("powershell.exe") or shutil.which("pwsh")
    if not executable:
        pytest.skip("PowerShell is not available.")
    return executable


def _run_helper_script(tmp_path: Path, body: str) -> subprocess.CompletedProcess[str]:
    project_root = Path(__file__).resolve().parents[2]
    helper = project_root / "scripts" / "postgres-test-native-command.ps1"
    script = tmp_path / "native-helper-test.ps1"
    script.write_text(
        f". '{helper}'\n{body}\n",
        encoding="utf-8",
    )
    return subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_native_wrapper_accepts_alembic_info_stderr_and_parses_stdout_json(tmp_path: Path):
    python = sys.executable
    result = _run_helper_script(
        tmp_path,
        f"""
$result = Invoke-NativeCommandCaptured -FilePath '{python}' -ArgumentList @(
    '-c',
    'import json, sys; sys.stderr.write("INFO [alembic.runtime.migration] Context impl PostgresqlImpl.\\n"); print(json.dumps({{"status":"passed","postgresql":True,"sqliteFallback":False,"protectedNameGuard":"passed","schemaDriftCount":0}}))'
)
Assert-NativeCommandSucceeded $result 'synthetic preparation'
$json = Convert-PrepareStdoutJson $result.StdOut
Assert-PostgresPrepareJsonPassed $json
[pscustomobject]@{{
    exitCode = $result.ExitCode
    stderrHasAlembicInfo = ($result.StdErr -match 'alembic.runtime.migration')
    parsedStatus = $json.status
    schemaDriftCount = $json.schemaDriftCount
}} | ConvertTo-Json -Compress
""",
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload == {
        "exitCode": 0,
        "stderrHasAlembicInfo": True,
        "parsedStatus": "passed",
        "schemaDriftCount": 0,
    }


def test_native_wrapper_nonzero_failure_includes_redacted_stderr(tmp_path: Path):
    python = sys.executable
    result = _run_helper_script(
        tmp_path,
        f"""
$result = Invoke-NativeCommandCaptured -FilePath '{python}' -ArgumentList @(
    '-c',
    'import sys; sys.stderr.write(''failed postgresql+psycopg2://user:real-password@127.0.0.1:55432/organicai_task13b03_test\\n''); sys.exit(7)'
)
$message = Format-NativeCommandFailure -Result $result -Context 'synthetic failure'
[pscustomobject]@{{
    exitCode = $result.ExitCode
    hasStderr = ($message -match 'STDERR')
    redacted = ($message -match '<redacted>')
    leaked = ($message -match 'real-password')
}} | ConvertTo-Json -Compress
""",
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload == {
        "exitCode": 7,
        "hasStderr": True,
        "redacted": True,
        "leaked": False,
    }


def test_marker_classification_accepts_informational_stderr_with_zero_exit(tmp_path: Path):
    python = sys.executable
    result = _run_helper_script(
        tmp_path,
        f"""
$result = Invoke-NativeCommandCaptured -FilePath '{python}' -ArgumentList @(
    '-c',
    'import sys; sys.stderr.write("INFO [alembic.runtime.migration] Running upgrade\\nWARNING [alembic.runtime.migration] benign warning\\n"); print("2 passed in 0.10s")'
)
$outputText = @(
    'STDOUT:',
    (Redact-PostgresSensitiveText $result.StdOut.TrimEnd()),
    '',
    'STDERR:',
    (Redact-PostgresSensitiveText $result.StdErr.TrimEnd())
) -join "`n"
$classifiedFailure = ($result.ExitCode -ne 0) -or ($outputText -match "(?i)\bskipped\b|\btimeout\b|timed out|hung")
[pscustomobject]@{{
    exitCode = $result.ExitCode
    stderrHasInfo = ($result.StdErr -match 'alembic.runtime.migration')
    classifiedFailure = $classifiedFailure
}} | ConvertTo-Json -Compress
""",
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload == {
        "exitCode": 0,
        "stderrHasInfo": True,
        "classifiedFailure": False,
    }
