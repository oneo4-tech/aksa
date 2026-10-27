"""Tests for the AKSA OS command line entry point."""

import pytest
from aksa_os.cli import main


def fake_server(calls):
    def run(app, *, host, port):
        calls.append((app, host, port))

    return run


def test_main_serves_the_app_on_localhost():
    calls = []
    assert main(["--port", "0"], fake_server(calls)) == 0
    [(app, host, port)] = calls
    assert app is not None
    assert host == "127.0.0.1"
    assert port == 0


def test_main_refuses_another_host():
    calls = []

    with pytest.raises(SystemExit):
        main(["--host", "0.0.0.0"], fake_server(calls))
    assert calls == []


def test_main_check_reports_settings_without_starting_the_server(capsys):
    calls = []
    assert main(["--check"], fake_server(calls)) == 0
    assert calls == []
    assert "127.0.0.1" in capsys.readouterr().out
