"""Small systemd-unit fragments shared by the gateway service generator."""

from __future__ import annotations


def watchdog_directives(watchdog_seconds: int) -> tuple[str, str]:
    """Return the service type and watchdog directives for a managed gateway.

    Source installs can be launched through credential wrappers.  The gateway
    child therefore needs access to the notification socket until it atomically
    adopts ``MainPID`` and narrows ``NotifyAccess`` in its READY message.
    """
    if watchdog_seconds <= 0:
        return "simple", ""
    return "notify", f"NotifyAccess=all\nWatchdogSec={watchdog_seconds}s\n"