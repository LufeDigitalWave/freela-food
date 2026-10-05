"""Testes unitários para scripts/deploy-vps.py (sem rede, paramiko simulado)."""

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "deploy-vps.py"


@pytest.fixture
def deploy(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    fake_paramiko = types.ModuleType("paramiko")
    fake_paramiko.SSHClient = MagicMock  # type: ignore[attr-defined]
    fake_paramiko.SFTPClient = MagicMock  # type: ignore[attr-defined]
    fake_paramiko.RejectPolicy = MagicMock(name="RejectPolicy")  # type: ignore[attr-defined]
    fake_paramiko.AutoAddPolicy = MagicMock(name="AutoAddPolicy")  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "paramiko", fake_paramiko)
    spec = importlib.util.spec_from_file_location("deploy_vps", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ssh_returning(exit_code: int, out: str = "", err: str = "") -> MagicMock:
    stdout = MagicMock()
    stdout.read.return_value = out.encode()
    stdout.channel.recv_exit_status.return_value = exit_code
    stderr = MagicMock()
    stderr.read.return_value = err.encode()
    ssh = MagicMock()
    ssh.exec_command.return_value = (MagicMock(), stdout, stderr)
    return ssh


def test_run_remote_raises_on_nonzero_exit(deploy: types.ModuleType):
    ssh = _ssh_returning(1, err="build failed")
    with pytest.raises(deploy.RemoteCommandError) as exc:
        deploy.run_remote(ssh, "docker compose build")
    assert exc.value.exit_code == 1


def test_run_remote_returns_output_on_success(deploy: types.ModuleType):
    ssh = _ssh_returning(0, out="ok")
    out, _ = deploy.run_remote(ssh, "true")
    assert out == "ok"


def test_run_remote_check_false_tolerates_failure(deploy: types.ModuleType):
    ssh = _ssh_returning(3, out="partial")
    out, _ = deploy.run_remote(ssh, "docker compose ps", check=False)
    assert out == "partial"


def test_connect_rejects_unknown_host_keys(deploy: types.ModuleType):
    ssh = MagicMock()
    deploy.connect_ssh(ssh, "203.0.113.10", "root", "pw")
    ssh.load_system_host_keys.assert_called_once()
    policy = ssh.set_missing_host_key_policy.call_args.args[0]
    assert policy is deploy.paramiko.RejectPolicy.return_value
    deploy.paramiko.AutoAddPolicy.assert_not_called()


def test_upload_env_sets_0600_before_writing(deploy: types.ModuleType):
    calls: list[str] = []
    handle = MagicMock()
    handle.__enter__.return_value = handle
    handle.writelines.side_effect = lambda _lines: calls.append("write")
    sftp = MagicMock()
    sftp.file.return_value = handle
    sftp.chmod.side_effect = lambda _path, _mode: calls.append("chmod")

    deploy.upload_env(sftp, "/opt/app/.env", ["A=1\n"])

    sftp.chmod.assert_called_once_with("/opt/app/.env", 0o600)
    assert calls == ["chmod", "write"]
