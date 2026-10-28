"""Generated service behavior for the opt-in systemd watchdog."""

from __future__ import annotations

import shlex

from gateway.config import GatewayConfig
from hermes_cli import _launchers
from hermes_cli import gateway as gateway_cli
from hermes_cli.gateway_systemd_unit import watchdog_directives


def _is_gateway_command(argv: list[str]) -> bool:
    try:
        gateway = argv.index("gateway")
    except ValueError:
        return False
    return argv[gateway : gateway + 2] == ["gateway", "run"]


def test_watchdog_unit_accepts_gateway_child_notifications(monkeypatch):
    monkeypatch.setattr(
        gateway_cli,
        "load_gateway_config",
        lambda: GatewayConfig.from_dict({"systemd_watchdog_seconds": 120}),
        raising=False,
    )
    monkeypatch.setattr(gateway_cli, "get_python_path", lambda: "/usr/bin/python3")
    monkeypatch.setattr(_launchers, "resolve_store_python", lambda _root: None)
    monkeypatch.setattr(
        gateway_cli,
        "_build_service_path_dirs",
        lambda project_root=None: [],
    )
    monkeypatch.setattr(gateway_cli, "_append_node_dir_for_service", lambda *_args: None)

    unit = gateway_cli.generate_systemd_unit(system=False)

    assert "Type=notify" in unit
    assert "NotifyAccess=all" in unit
    assert "NotifyAccess=main" not in unit
    assert "WatchdogSec=120s" in unit
    exec_start = next(
        shlex.split(line.split("=", 1)[1])
        for line in unit.splitlines()
        if line.startswith("ExecStart=")
    )
    assert _is_gateway_command(exec_start)


def test_disabled_watchdog_uses_simple_service():
    assert watchdog_directives(0) == ("simple", "")



def test_system_unit_reads_watchdog_from_target_home(tmp_path, monkeypatch):
    caller_home = tmp_path / "caller"
    target_home = tmp_path / "target"
    caller_home.mkdir()
    target_home.mkdir()
    (caller_home / "config.yaml").write_text(
        "gateway:\n  systemd_watchdog_seconds: 0\n",
        encoding="utf-8",
    )
    (target_home / "config.yaml").write_text(
        "gateway:\n  systemd_watchdog_seconds: 75\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(caller_home))
    monkeypatch.setattr(gateway_cli, "get_python_path", lambda: "/usr/bin/python3")
    monkeypatch.setattr(_launchers, "resolve_store_python", lambda _root: None)
    monkeypatch.setattr(
        gateway_cli,
        "_build_service_path_dirs",
        lambda project_root=None: [],
    )
    monkeypatch.setattr(gateway_cli, "_append_node_dir_for_service", lambda *_args: None)
    monkeypatch.setattr(
        gateway_cli,
        "_system_service_identity",
        lambda _user: ("service", "service", str(tmp_path / "account"), 1001),
    )
    monkeypatch.setattr(
        gateway_cli,
        "_hermes_home_for_target_user",
        lambda _home: str(target_home),
    )

    unit = gateway_cli.generate_systemd_unit(system=True, run_as_user="service")

    assert "Type=notify" in unit
    assert "WatchdogSec=75s" in unit


