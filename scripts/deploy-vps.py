#!/usr/bin/env python3
"""
Script de deploy freela-food na VPS.

Credentials são lidas de variáveis de ambiente:
  export VPS_HOST=93.127.211.7
  export VPS_USER=root
  export VPS_PASSWORD=xxx
  export DEPLOY_ENV_FILE=.env.deploy
  python scripts/deploy-vps.py

Ou criar .env.deploy (NÃO COMMITE) com:
  VPS_HOST=...
  VPS_USER=root
  VPS_PASSWORD=...
  GIT_REPO=...
  COMPOSE_FILE=docker-compose.deploy.yml

Steps:
  1. SSH na VPS
  2. Pull latest code
  3. Upload .env (filtrado, sem VPS vars)
  4. Build Docker
  5. Up containers
  6. Verify health
"""

import os
import sys
import time
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("Erro: paramiko não instalado. Execute: uv add paramiko")
    sys.exit(1)


def load_env_file(path: str) -> dict[str, str]:
    """Carrega arquivo .env e retorna como dict."""
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


class RemoteCommandError(RuntimeError):
    """Comando remoto terminou com exit code diferente de zero."""

    def __init__(self, command: str, exit_code: int, output: str) -> None:
        super().__init__(f"exit {exit_code}: {command[:100]}")
        self.command = command
        self.exit_code = exit_code
        self.output = output


def run_remote(
    ssh: paramiko.SSHClient, command: str, timeout: int = 300, check: bool = True
) -> tuple[str, str]:
    """Executa comando remoto e retorna (stdout, stderr).

    Com check=True (padrão), exit code != 0 levanta RemoteCommandError.
    """
    print(f"  → {command[:100]}{'...' if len(command) > 100 else ''}")
    _, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    exit_code = stdout.channel.recv_exit_status()
    if out.strip():
        print(f"    OUT: {out.strip()[:300]}")
    if err.strip() and exit_code != 0:
        print(f"    ERR: {err.strip()[:300]}")
    if check and exit_code != 0:
        raise RemoteCommandError(command, exit_code, out[-2000:] + err[-2000:])
    return out, err


def connect_ssh(ssh: paramiko.SSHClient, host: str, user: str, password: str) -> None:
    """Conecta exigindo chave de host conhecida (~/.ssh/known_hosts).

    Host desconhecido é recusado (proteção contra MITM): conecte uma vez com
    `ssh user@host` e confira o fingerprint antes de usar este script.
    """
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
    ssh.connect(host, username=user, password=password, timeout=30)


def upload_env(sftp: paramiko.SFTPClient, remote_path: str, lines: list[str]) -> None:
    """Grava o .env remoto com permissão 0600 antes de escrever os segredos."""
    with sftp.file(remote_path, "w") as f:
        sftp.chmod(remote_path, 0o600)
        f.writelines(lines)


def main() -> None:
    # ─── Carregar credenciais (NUNCA hardcoded) ─────────
    # Tenta ler .env.deploy se existir (NÃO COMMITE!)
    deploy_env_path = Path(__file__).parent.parent / ".env.deploy"

    env: dict[str, str] = {}
    if deploy_env_path.exists():
        env = load_env_file(str(deploy_env_path))

    # Vars de ambiente têm prioridade
    vps_host = os.getenv("VPS_HOST") or env.get("VPS_HOST", "")
    vps_user = os.getenv("VPS_USER") or env.get("VPS_USER", "root")
    vps_pass = os.getenv("VPS_PASSWORD") or env.get("VPS_PASSWORD", "")
    project_dir = os.getenv("VPS_PROJECT_DIR") or env.get("VPS_PROJECT_DIR", "/opt/freela-food")
    compose_file = os.getenv("COMPOSE_FILE") or env.get("COMPOSE_FILE", "docker-compose.deploy.yml")
    git_repo = os.getenv("GIT_REPO") or env.get(
        "GIT_REPO", "https://github.com/LufeDigitalWave/freela-food.git"
    )

    if not vps_host or not vps_pass:
        print("❌ VPS_HOST e VPS_PASSWORD são obrigatórios")
        print("   Configure via env vars ou .env.deploy (NÃO COMMITE)")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  DEPLOY: freela-food → {vps_host}")
    print(f"{'=' * 60}\n")

    # ─── Conectar SSH ──────────────────────────────────
    print("[1/7] Conectando SSH...")
    ssh = paramiko.SSHClient()
    try:
        connect_ssh(ssh, vps_host, vps_user, vps_pass)
        print("  ✓ SSH conectado\n")
    except Exception as e:
        print(f"  ✗ SSH falhou: {e}\n")
        sys.exit(1)

    try:
        # ─── Docker check ──────────────────────────────
        print("[2/7] Verificando Docker...")
        out, _ = run_remote(ssh, "docker --version && docker compose version 2>&1")
        if "Docker" not in out:
            print("  ✗ Docker não disponível\n")
            sys.exit(1)
        print("  ✓ Docker OK\n")

        # ─── Clone/Pull ───────────────────────────────
        print(f"[3/7] Atualizando código em {project_dir}...")
        run_remote(ssh, f"mkdir -p {project_dir}")
        out, _ = run_remote(
            ssh,
            f"cd {project_dir} && "
            f"(git rev-parse --git-dir > /dev/null 2>&1 && git pull origin main 2>&1) || "
            f"(git clone {git_repo} . 2>&1)",
            timeout=120,
        )
        print("  ✓ Código atualizado\n")

        # ─── Upload .env ──────────────────────────────
        print("[4/7] Uploading .env (prod)...")
        # Lê o conteúdo de .env.deploy e filtra VPS vars
        env_content_lines = []
        if deploy_env_path.exists():
            with open(deploy_env_path) as f:
                for line in f:
                    stripped = line.strip()
                    # Pular variáveis de deploy (NÃO devem ir pro .env de runtime)
                    if (
                        stripped.startswith("VPS_")
                        or stripped.startswith("GIT_")
                        or stripped.startswith("COMPOSE_FILE")
                    ):
                        continue
                    env_content_lines.append(line)

        sftp = ssh.open_sftp()
        upload_env(sftp, f"{project_dir}/.env", env_content_lines)
        sftp.close()
        print(f"  ✓ .env criado em {project_dir}\n")

        # ─── Build ─────────────────────────────────────
        print("[5/7] Building Docker images (pode levar minutos)...")
        out, err = run_remote(
            ssh,
            f"cd {project_dir} && docker compose -f {compose_file} build 2>&1",
            timeout=600,
        )
        print("  ✓ Build completo\n")

        # ─── Up ───────────────────────────────────────
        print("[6/7] Subindo containers...")
        run_remote(ssh, f"cd {project_dir} && docker compose -f {compose_file} up -d 2>&1")
        print("  → Esperando 20s para health checks...")
        time.sleep(20)
        print("  ✓ Containers up\n")

        # ─── Verify ───────────────────────────────────
        print("[7/7] Verificando saúde dos serviços...")
        out, _ = run_remote(
            ssh, f"cd {project_dir} && docker compose -f {compose_file} ps", check=False
        )

        # Health check via Caddy
        health_out, _ = run_remote(ssh, "curl -sf http://localhost/health || echo 'HEALTH_FAILED'")
        healthy = "HEALTH_FAILED" not in health_out

        print(f"\n{'=' * 60}")
        print(f"  DEPLOY {'✓ SUCESSO' if healthy else '⚠ PARCIAL'}")
        print(f"{'=' * 60}")
        print(f"\n  Endpoints:")
        print(f"    API:    http://{vps_host}/health")
        print(f"    App:    http://{vps_host}/")
        print(
            f"\n  Logs: ssh {vps_user}@{vps_host} 'cd {project_dir} && docker compose -f {compose_file} logs -f'\n"
        )
        if not healthy:
            sys.exit(1)

    except RemoteCommandError as e:
        print(f"\n  ✗ Deploy interrompido: {e}\n")
        sys.exit(1)
    finally:
        ssh.close()


if __name__ == "__main__":
    main()
