"""Tests for the Telegram command-menu registration.

`command_menu()` (bot.handlers) is the single source of truth for both
/help and the "/" autocomplete menu; `register_commands()` (bot.clients)
ships it to Telegram via set_my_commands at every worker boot and after
every /api/deploy — so like register_webhook it must never raise.
"""

from unittest.mock import patch


def test_command_menu_includes_expected_commands():
    from bot.handlers import command_menu

    names = [name for name, _ in command_menu()]
    for expected in ("start", "help", "quiz", "debug", "review", "summarize"):
        assert expected in names
    # every entry is a (name, description) pair with non-empty text
    assert all(name and desc for name, desc in command_menu())


def test_command_menu_model_conditional_on_hf():
    import bot.handlers

    with patch("bot.handlers.HF_SPACE_ID", ""):
        assert "model" not in [n for n, _ in bot.handlers.command_menu()]
    with patch("bot.handlers.HF_SPACE_ID", "fake/space"):
        assert "model" in [n for n, _ in bot.handlers.command_menu()]


def test_register_commands_calls_set_my_commands():
    with patch("bot.clients.bot") as mock_bot:
        from bot.clients import register_commands

        msg = register_commands()
        mock_bot.set_my_commands.assert_called_once()
        cmds = mock_bot.set_my_commands.call_args[0][0]
        assert len(cmds) >= 1
        assert "Registered" in msg


def test_register_commands_does_not_raise_on_failure():
    with patch("bot.clients.bot") as mock_bot:
        mock_bot.set_my_commands.side_effect = Exception("boom")
        from bot.clients import register_commands

        msg = register_commands()
        assert "failed" in msg.lower()
