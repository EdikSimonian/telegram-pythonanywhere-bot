import json
import os
import random
from datetime import datetime

from bot.clients import bot, BOT_INFO, store
from bot.config import COMMIT_SHA, HF_SPACE_ID, HOSTING_LABEL, MODEL, RATE_LIMIT
from bot.ai import ask_ai
from bot.helpers import is_allowed, keep_typing, send_reply, should_respond
from bot.history import clear_history
from bot.preferences import get_provider, set_provider
from bot.rate_limit import is_rate_limited


VERBOSE_LOG = os.environ.get("BOT_VERBOSE_LOG", "").strip().lower() in (
    "1", "true", "yes", "on"
)


def _log(message, direction: str, text: str) -> None:
    if not VERBOSE_LOG:
        return

    user = message.from_user
    user_name = f"@{user.username}" if user.username else (user.first_name or str(user.id))
    bot_name = f"@{BOT_INFO.username}"

    snippet = (text or "").replace("\n", " ")[:500]

    sender, receiver = (user_name, bot_name) if direction == "in" else (bot_name, user_name)
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {sender} → {receiver}: {snippet}", flush=True)


# ----------------------------
# COMMANDS
# ----------------------------

COMMANDS = [
    ("start", "welcome"),
    ("help", "list commands"),
    ("reset", "clear chat"),
    ("about", "bot info"),
    ("sha", "version"),

    ("model", "switch model"),
    ("models", "list models"),

    ("joke", "joke"),
    ("quote", "quote"),
    ("fact", "fact"),
    ("compliment", "compliment"),

    ("explain", "explain topic"),
    ("challenge", "coding challenge"),
    ("analogy", "analogy"),
    ("motivate", "motivation"),
    ("translate", "translate code"),
    ("debug", "debug code"),
    ("review", "review code"),
    ("quiz", "quiz"),
    ("summarize", "summarize"),

    ("convert", "convert files"),
    ("roadmap", "learning path"),
    ("streak", "streak tracker"),
    ("interview", "mock interview"),
    ("run", "simulate code"),

    ("roll", "dice"),
    ("roast", "roast"),
    ("remember", "save note"),
    ("recall", "show notes"),
    ("forget", "delete notes"),
]


# ----------------------------
# MODELS (Cerebras only + HF optional)
# ----------------------------

CEREBRAS_MODELS = [
    {
        "key": "gpt-oss-120b",
        "name": "gpt-oss-120b",
        "description": "Best reasoning + coding model",
    },
    {
        "key": "qwen-3-235b-a22b-instruct-2507",
        "name": "qwen-3-235b-a22b-instruct-2507",
        "description": "Strong multilingual model",
    },
]


def available_models():
    models = list(CEREBRAS_MODELS)

    if HF_SPACE_ID:
        models.append({
            "key": "hf",
            "name": "ArmGPT",
            "description": "Armenian HF model",
        })

    return models


def active_model(user_id):
    provider = get_provider(user_id)
    models = available_models()

    for m in models:
        if m["key"] == provider:
            return m

    return models[0]


def _resolve_model(choice, models=None):
    if models is None:
        models = available_models()

    choice = (choice or "").lower()

    for m in models:
        if choice in (m["key"].lower(), m["name"].lower()):
            return m

    return None


def command_menu():
    return list(COMMANDS)


# ----------------------------
# BASIC COMMANDS
# ----------------------------

@bot.message_handler(commands=["start"], func=is_allowed)
def cmd_start(message):
    bot.send_message(message.chat.id, "AI coding assistant ready. Use /help")


@bot.message_handler(commands=["help"], func=is_allowed)
def cmd_help(message):
    bot.send_message(
        message.chat.id,
        "\n".join(f"/{c} — {d}" for c, d in COMMANDS)
    )


@bot.message_handler(commands=["reset"], func=is_allowed)
def cmd_reset(message):
    clear_history(message.from_user.id)
    bot.send_message(message.chat.id, "Cleared.")


@bot.message_handler(commands=["about"], func=is_allowed)
def cmd_about(message):
    model = active_model(message.from_user.id)

    lines = [
        f"Model: {model['name']}",
        f"Hosting: {HOSTING_LABEL}",
        f"Storage: {'enabled' if store else 'disabled'}",
    ]

    if COMMIT_SHA:
        lines.append(f"Version: {COMMIT_SHA}")

    bot.send_message(message.chat.id, "\n".join(lines))


@bot.message_handler(commands=["sha"], func=is_allowed)
def cmd_sha(message):
    bot.send_message(message.chat.id, COMMIT_SHA or "unknown")


# ----------------------------
# MODEL SWITCHING
# ----------------------------

@bot.message_handler(commands=["model"], func=is_allowed)
def cmd_model(message):
    parts = message.text.split(maxsplit=1)

    models = available_models()

    if len(parts) == 1:
        current = active_model(message.from_user.id)
        bot.send_message(message.chat.id, f"Current: {current['name']}")
        return

    target = _resolve_model(parts[1], models)

    if not target:
        bot.send_message(message.chat.id, "Unknown model")
        return

    set_provider(message.from_user.id, target["key"])
    bot.send_message(message.chat.id, f"Switched to {target['name']}")


@bot.message_handler(commands=["models"], func=is_allowed)
def cmd_models(message):
    current = active_model(message.from_user.id)

    lines = ["Models:"]
    for m in available_models():
        mark = " (active)" if m["key"] == current["key"] else ""
        lines.append(f"- {m['name']}{mark}")

    bot.send_message(message.chat.id, "\n".join(lines))


# ----------------------------
# AI FUN COMMANDS
# ----------------------------

def _ask(user_id, prompt):
    return ask_ai(user_id, prompt)


@bot.message_handler(commands=["joke"], func=is_allowed)
def cmd_joke(m):
    bot.send_message(m.chat.id, _ask(m.from_user.id, "short programming joke"))


@bot.message_handler(commands=["quote"], func=is_allowed)
def cmd_quote(m):
    bot.send_message(m.chat.id, _ask(m.from_user.id, "programming quote"))


@bot.message_handler(commands=["fact"], func=is_allowed)
def cmd_fact(m):
    bot.send_message(m.chat.id, _ask(m.from_user.id, "tech fact"))


@bot.message_handler(commands=["compliment"], func=is_allowed)
def cmd_compliment(m):
    bot.send_message(m.chat.id, _ask(m.from_user.id, "compliment about learning"))


@bot.message_handler(commands=["motivate"], func=is_allowed)
def cmd_motivate(m):
    bot.send_message(m.chat.id, _ask(m.from_user.id, "motivation for coding student"))


# ----------------------------
# LEARNING COMMANDS
# ----------------------------

@bot.message_handler(commands=["explain"], func=is_allowed)
def cmd_explain(m):
    topic = m.text.split(maxsplit=1)[1] if " " in m.text else ""
    if not topic:
        return bot.send_message(m.chat.id, "Usage: /explain <topic>")
    bot.send_message(m.chat.id, _ask(m.from_user.id, f"explain {topic} simply"))


@bot.message_handler(commands=["challenge"], func=is_allowed)
def cmd_challenge(m):
    bot.send_message(m.chat.id, _ask(m.from_user.id, "coding challenge"))


@bot.message_handler(commands=["analogy"], func=is_allowed)
def cmd_analogy(m):
    topic = m.text.split(maxsplit=1)[1] if " " in m.text else ""
    if not topic:
        return bot.send_message(m.chat.id, "Usage: /analogy <concept>")
    bot.send_message(m.chat.id, _ask(m.from_user.id, f"analogy for {topic}"))


@bot.message_handler(commands=["quiz"], func=is_allowed)
def cmd_quiz(m):
    topic = m.text.split(maxsplit=1)[1] if " " in m.text else ""
    if not topic:
        return bot.send_message(m.chat.id, "Usage: /quiz <topic>")

    q = _ask(m.from_user.id, f"quiz question about {topic}")
    sent = bot.send_message(m.chat.id, q)
    bot.register_next_step_handler(sent, lambda msg: _grade_quiz(msg, q))


def _grade_quiz(message, question):
    ans = message.text
    bot.send_message(
        message.chat.id,
        _ask(message.from_user.id, f"Q:{question} A:{ans} grade")
    )


@bot.message_handler(commands=["summarize"], func=is_allowed)
def cmd_summarize(m):
    text = m.text.split(maxsplit=1)[1] if " " in m.text else ""
    if not text:
        return bot.send_message(m.chat.id, "Usage: /summarize <text>")
    bot.send_message(m.chat.id, _ask(m.from_user.id, f"summarize: {text}"))


# ----------------------------
# NEW FEATURES
# ----------------------------

@bot.message_handler(commands=["convert"], func=is_allowed)
def cmd_convert(m):
    bot.send_message(m.chat.id, "File conversion placeholder (no ffmpeg).")


@bot.message_handler(commands=["roadmap"], func=is_allowed)
def cmd_roadmap(m):
    topic = m.text.split(maxsplit=1)[1] if " " in m.text else ""
    if not topic:
        return bot.send_message(m.chat.id, "Usage: /roadmap <topic>")
    bot.send_message(m.chat.id, _ask(m.from_user.id, f"learning roadmap for {topic}"))


@bot.message_handler(commands=["streak"], func=is_allowed)
def cmd_streak(m):
    if not store:
        return bot.send_message(m.chat.id, "No storage")

    key = f"streak:{m.from_user.id}"
    val = int(store.get(key) or 0) + 1
    store.set(key, str(val))
    bot.send_message(m.chat.id, f"🔥 Streak: {val}")


@bot.message_handler(commands=["interview"], func=is_allowed)
def cmd_interview(m):
    bot.send_message(m.chat.id, _ask(m.from_user.id, "mock coding interview question"))


@bot.message_handler(commands=["run"], func=is_allowed)
def cmd_run(m):
    code = m.text.split(maxsplit=1)[1] if " " in m.text else ""
    if not code:
        return bot.send_message(m.chat.id, "Usage: /run <code>")
    bot.send_message(m.chat.id, _ask(m.from_user.id, f"predict output: {code}"))


# ----------------------------
# FUN + NOTES
# ----------------------------

@bot.message_handler(commands=["roll"], func=is_allowed)
def cmd_roll(m):
    bot.send_message(m.chat.id, str(random.randint(1, 6)))


@bot.message_handler(commands=["roast"], func=is_allowed)
def cmd_roast(m):
    sent = bot.send_message(m.chat.id, "Name?")
    bot.register_next_step_handler(sent, _do_roast)


def _do_roast(m):
    name = m.text
    bot.send_message(m.chat.id, _ask(m.from_user.id, f"roast {name}"))


@bot.message_handler(commands=["remember"], func=is_allowed)
def cmd_remember(m):
    if not store:
        return bot.send_message(m.chat.id, "No storage")

    note = m.text.split(maxsplit=1)[1] if " " in m.text else ""
    if not note:
        return bot.send_message(m.chat.id, "Usage: /remember <note>")

    key = f"notes:{m.from_user.id}"
    notes = json.loads(store.get(key) or "[]")
    notes.append(note)
    store.set(key, json.dumps(notes))

    bot.send_message(m.chat.id, "Saved")


@bot.message_handler(commands=["recall"], func=is_allowed)
def cmd_recall(m):
    notes = json.loads(store.get(f"notes:{m.from_user.id}") or "[]")
    bot.send_message(m.chat.id, "\n".join(notes) if notes else "No notes")


@bot.message_handler(commands=["forget"], func=is_allowed)
def cmd_forget(m):
    store.delete(f"notes:{m.from_user.id}")
    bot.send_message(m.chat.id, "Cleared")


# ----------------------------
# MAIN HANDLER
# ----------------------------

@bot.message_handler(content_types=["text"], func=is_allowed)
def handle_message(message):
    if not should_respond(message):
        return

    text = (message.text or "").replace(f"@{BOT_INFO.username}", "").strip()
    if not text:
        return

    _log(message, "in", text)

    if is_rate_limited(message.from_user.id):
        msg = f"Rate limit reached ({RATE_LIMIT})"
        bot.send_message(message.chat.id, msg)
        return

    try:
        with keep_typing(message.chat.id):
            reply = ask_ai(message.from_user.id, text)

        send_reply(message, reply)
        _log(message, "out", reply)

    except Exception as e:
        bot.send_message(message.chat.id, "Error")
        _log(message, "out", str(e))