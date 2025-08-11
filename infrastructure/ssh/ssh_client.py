from __future__ import annotations

import shlex
from typing import List, Tuple

import paramiko

from config import ServerConfig


class SSHLogClient:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self._timeout = timeout_seconds

    def _connect(self, server: ServerConfig) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()

        connect_kwargs = {
            "hostname": server.host,
            "port": server.port,
            "username": server.username,
            "timeout": self._timeout,
            "look_for_keys": True,
            "allow_agent": True,
        }
        if server.password:
            connect_kwargs["password"] = server.password
        if server.private_key_path:
            pkey = None
            try:
                pkey = paramiko.RSAKey.from_private_key_file(server.private_key_path)
            except Exception:
                try:
                    pkey = paramiko.Ed25519Key.from_private_key_file(server.private_key_path)
                except Exception:
                    pkey = None
            if pkey is not None:
                connect_kwargs["pkey"] = pkey

        client.connect(**connect_kwargs)
        return client

    def _exec(self, client: paramiko.SSHClient, cmd: str) -> Tuple[str, str, int]:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=self._timeout)
        out = stdout.read().decode("utf-8", errors="ignore")
        err = stderr.read().decode("utf-8", errors="ignore")
        exit_status = stdout.channel.recv_exit_status()
        return out, err, exit_status

    def _exec_with_sudo_n(self, client: paramiko.SSHClient, cmd: str) -> Tuple[str, str, int]:
        return self._exec(client, f"sudo -n {cmd}")

    def _exec_with_sudo_password(self, client: paramiko.SSHClient, cmd: str, password: str) -> Tuple[str, str, int]:
        # Use -S to read password from stdin; -p '' to suppress prompt text
        stdin, stdout, stderr = client.exec_command(f"sudo -S -p '' {cmd}", timeout=self._timeout)
        try:
            stdin.write(password + "\n")
            stdin.flush()
        except Exception:
            pass
        out = stdout.read().decode("utf-8", errors="ignore")
        err = stderr.read().decode("utf-8", errors="ignore")
        exit_status = stdout.channel.recv_exit_status()
        return out, err, exit_status

    def _exec_auto_privileged(self, client: paramiko.SSHClient, server: ServerConfig, cmd: str) -> Tuple[str, int]:
        out, err, code = self._exec(client, cmd)
        if code == 0:
            return out, code
        # Try sudo -n (non-interactive)
        out2, err2, code2 = self._exec_with_sudo_n(client, cmd)
        if code2 == 0:
            return out2, code2
        # Try sudo with password if we have one
        if server.password:
            out3, err3, code3 = self._exec_with_sudo_password(client, cmd, server.password)
            return out3, code3
        return out, code

    def fetch_tail(self, server: ServerConfig, log_path: str, tail_lines: int = 2000) -> List[str]:
        client = None
        try:
            client = self._connect(server)
            quoted_path = shlex.quote(log_path)
            cmd = f"tail -n {int(tail_lines)} {quoted_path}"
            out, _ = self._exec_auto_privileged(client, server, cmd)
            return out.splitlines()
        finally:
            try:
                if client is not None:
                    client.close()
            except Exception:
                pass

    def fetch_journal_unit_tail(self, server: ServerConfig, unit_name: str, tail_lines: int = 2000) -> List[str]:
        client = None
        try:
            client = self._connect(server)
            quoted_unit = shlex.quote(unit_name)
            cmd = f"journalctl -u {quoted_unit} -n {int(tail_lines)} --no-pager"
            out, _ = self._exec_auto_privileged(client, server, cmd)
            return out.splitlines()
        finally:
            try:
                if client is not None:
                    client.close()
            except Exception:
                pass

    def fetch_ssh_auto(self, server: ServerConfig, tail_lines: int = 2000) -> Tuple[List[str], str]:
        client = None
        try:
            client = self._connect(server)
            # Detect presence of journalctl
            out_j, _, code_j = self._exec(client, "command -v journalctl >/dev/null 2>&1; echo $?")
            has_journal = out_j.strip().endswith("0")

            # Parse /etc/os-release
            out_os, _, _ = self._exec(client, "cat /etc/os-release 2>/dev/null || true")
            os_id = ""
            os_like = ""
            for line in out_os.splitlines():
                if line.startswith("ID="):
                    os_id = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("ID_LIKE="):
                    os_like = line.split("=", 1)[1].strip().strip('"')
            like_lower = os_like.lower()
            is_debian_family = (
                os_id.lower() in {"debian", "ubuntu", "raspbian"}
                or "debian" in like_lower
                or "ubuntu" in like_lower
            )

            preferred_unit = "ssh" if is_debian_family else "sshd"
            preferred_file = "/var/log/auth.log" if is_debian_family else "/var/log/secure"

            if has_journal:
                quoted_unit = shlex.quote(preferred_unit)
                out, code = self._exec_auto_privileged(client, server, f"journalctl -u {quoted_unit} -n {int(tail_lines)} --no-pager")
                if code == 0 and out:
                    return out.splitlines(), f"journal:{preferred_unit}"
                alt_unit = "sshd" if preferred_unit == "ssh" else "ssh"
                quoted_alt = shlex.quote(alt_unit)
                out, code = self._exec_auto_privileged(client, server, f"journalctl -u {quoted_alt} -n {int(tail_lines)} --no-pager")
                if code == 0 and out:
                    return out.splitlines(), f"journal:{alt_unit}"

            out, code = self._exec_auto_privileged(client, server, f"tail -n {int(tail_lines)} {shlex.quote(preferred_file)}")
            if code == 0 and out:
                return out.splitlines(), preferred_file

            alt_file = "/var/log/secure" if preferred_file.endswith("auth.log") else "/var/log/auth.log"
            out, _ = self._exec_auto_privileged(client, server, f"tail -n {int(tail_lines)} {shlex.quote(alt_file)}")
            return out.splitlines(), alt_file
        finally:
            try:
                if client is not None:
                    client.close()
            except Exception:
                pass
