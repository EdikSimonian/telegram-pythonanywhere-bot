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
    "1",
    "true",
    "yes",
    "on",
)


def _log(message, direction: str, text: str) -> None:
    """Print a one-line trace of a message in verbose mode.

    direction is "in" (user → bot) or "out" (bot → user). Text is
    truncated to 500 characters so long AI replies don't flood the
    terminal. Newlines are collapsed for single-line readability.
    """
    if not VERBOSE_LOG:
        return
    user = message.from_user
    user_name = (
        f"@{user.username}" if user.username else (user.first_name or f"user:{user.id}")
    )
    bot_name = f"@{BOT_INFO.username}"
    snippet = (text or "").replace("\n", " ").replace("\r", " ")
    if len(snippet) > 500:
        snippet = snippet[:500] + "..."
    if direction == "in":
        sender, receiver = user_name, bot_name
    else:
        sender, receiver = bot_name, user_name
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {sender} → {receiver}: {snippet}", flush=True)



# Single source of truth for the bot's command list. Drives both /help
# and the Telegram "/" autocomplete menu (registered via set_my_commands
# in bot.clients.register_commands). Add a new command here when you add
# its handler, or it won't show up in the menu.
COMMANDS = [
    ("start", "welcome message"),
    ("help", "show this message"),
    ("reset", "clear conversation history"),
    ("about", "about this bot"),
    ("model", "show or switch the AI model"),
    ("models", "list available AI models"),
    ("joke", "tell a programming joke"),
    ("quote", "tell a coding quote"),
    ("fact", "tell a coding fact"),
    ("compliment", "give a compliment"),
    ("explain", "explain a coding topic"),
    ("challenge", "get a coding challenge"),
    ("analogy", "explain a concept by analogy"),
    ("motivate", "get a motivational boost"),
    ("translate", "translate code to another language"),
    ("debug", "find the bug in your code"),
    ("review", "get a short code review"),
    ("quiz", "take a quick quiz on a topic"),
    ("summarize", "summarize a block of text"),
    ("roll", "roll the dice"),
    ("roast", "get roasted"),
    ("remember", "save a note"),
    ("recall", "list your notes"),
    ("forget", "clear your notes"),
]


def available_models():
    """Registry of selectable AI models — the single source of truth for
    /model and /models.

    "main" (the OpenAI-compatible provider, e.g. Cerebras) is always
    present; "hf" (ArmGPT) is offered only when HF_SPACE_ID is configured.
    Each entry maps a provider `key` (see bot.preferences) to a display
    `name` and a short `description`. Add a model here to surface it in
    both commands at once.
    """
    models = [
        {
            "key": "main",
            "name": MODEL,
            "description": "Fast, multilingual, remembers your conversation",
        }
    ]
    if HF_SPACE_ID:
        models.append(
            {
                "key": "hf",
                "name": "ArmGPT",
                "description": "Armenian-only base model — slow, no memory",
            }
        )
    return models


def active_model(user_id):
    """Return the registry entry for the user's currently selected model.

    Falls back to the first available model if the saved provider is not
    in the registry (e.g. a stale "hf" preference after HF was unset)."""
    provider = get_provider(user_id)
    models = available_models()
    for model in models:
        if model["key"] == provider:
            return model
    return models[0]


def _resolve_model(choice, models=None):
    """Map a user-typed value to a registry entry, or None if no match.

    Matching is case-insensitive and accepts either the provider key
    ("main"/"hf") or the display name ("ArmGPT", "gpt-oss-120b"), so
    both `/model hf` and `/model armgpt` select the same model."""
    if models is None:
        models = available_models()
    choice = choice.strip().lower()
    for model in models:
        if choice in (model["key"].lower(), model["name"].lower()):
            return model
    return None


def command_menu():
    """(command, description) pairs for /help and the Telegram "/" menu.

    Kept as a function (rather than exposing COMMANDS directly) so callers
    have a stable seam if the menu ever needs to become conditional again."""
    return list(COMMANDS)


@bot.message_handler(commands=["start"], func=is_allowed)
def cmd_start(message):
    bot.send_message(
        message.chat.id,
        "Hello! I'm your AI coding assistant. If you don't know what to ask, try /help for a list of commands.",
    )
@bot.message_handler(commands=["joke"], func=is_allowed)
def cmd_joke(message):
 reply = ask_ai(
  message.from_user.id,
  "Tell me one original, clean programming or tech joke. "
  "Keep it short (1-2 lines) and make sure it actually lands with a clever punchline. "
  "Reply with only the joke — no preamble, no explanation.",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["quote"], func=is_allowed)
def cmd_quote(message):
 reply = ask_ai(
  message.from_user.id,
  "Share one memorable quote about programming, software, or technology. "
  "Attribute it to the real author if known. "
  "Format it as:\n\"<quote>\"\n— <author>\n"
  "Reply with only the quote — no preamble, no explanation.",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["fact"], func=is_allowed)
def cmd_fact(message):
 reply = ask_ai(
  message.from_user.id,
  "Share one genuinely surprising, true fact about computing, programming, or tech history. "
  "Keep it to 1-3 sentences and make it something most people wouldn't already know. "
  "Reply with only the fact — no preamble, no explanation.",
 )
 bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=["compliment"], func=is_allowed)
def cmd_compliment(message):
 reply = ask_ai(
  message.from_user.id,
  "Give me one warm, genuine, and original compliment. "
  "Make it uplifting and specific rather than generic flattery, and keep it to 1-2 sentences. "
  "Reply with only the compliment — no preamble, no explanation.",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["explain"], func=is_allowed)
def cmd_explain(message):
 topic = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
 if not topic:
  bot.send_message(message.chat.id, "Usage: /explain <topic>  (e.g. /explain recursion)")
  return
 reply = ask_ai(
  message.from_user.id,
  f"Explain this coding topic clearly and simply for a beginner: {topic}. "
  "Use plain language, keep it concise, and include one short example if it helps. "
  "Reply with only the explanation — no preamble.",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["challenge"], func=is_allowed)
def cmd_challenge(message):
 reply = ask_ai(
  message.from_user.id,
  "Give me one small, self-contained programming challenge suitable for a student. "
  "State the task clearly with an example input and expected output. "
  "Keep it beginner-friendly and solvable in a few lines of code. "
  "Do NOT include the solution. Reply with only the challenge — no preamble.",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["analogy"], func=is_allowed)
def cmd_analogy(message):
 concept = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
 if not concept:
  bot.send_message(message.chat.id, "Usage: /analogy <concept>  (e.g. /analogy pointers)")
  return
 reply = ask_ai(
  message.from_user.id,
  f"Explain this coding concept using one clear, relatable real-world analogy: {concept}. "
  "Keep it short and make the analogy do the work. Reply with only the analogy — no preamble.",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["motivate"], func=is_allowed)
def cmd_motivate(message):
 reply = ask_ai(
  message.from_user.id,
  "Give me one short, genuine, and uplifting motivational message for a student "
  "who is learning to code and might feel stuck or frustrated. "
  "Keep it warm and encouraging, 1-2 sentences. Reply with only the message — no preamble.",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["translate"], func=is_allowed)
def cmd_translate(message):
 parts = (message.text or "").split(maxsplit=2)
 if len(parts) < 3 or not parts[2].strip():
  bot.send_message(
   message.chat.id,
   "Usage: /translate <language> <code>\n"
   "Example: /translate javascript print('hi')",
  )
  return
 lang = parts[1].strip()
 code = parts[2].strip()
 reply = ask_ai(
  message.from_user.id,
  f"Translate the following code into {lang}. "
  "Keep the same behavior and logic. Reply with only the translated code in a code block, "
  f"followed by one short sentence noting anything that changed.\n\nCode:\n{code}",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["debug"], func=is_allowed)
def cmd_debug(message):
 code = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
 if not code:
  bot.send_message(message.chat.id, "Usage: /debug <code>\nPaste the code that isn't working.")
  return
 reply = ask_ai(
  message.from_user.id,
  "Find the bug in the following code. Explain what's wrong in 1-2 sentences, "
  "then show the corrected code in a code block. If there is no bug, say so. "
  f"Keep it concise. Reply with only the answer — no preamble.\n\nCode:\n{code}",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["review"], func=is_allowed)
def cmd_review(message):
 code = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
 if not code:
  bot.send_message(message.chat.id, "Usage: /review <code>\nPaste the code you'd like reviewed.")
  return
 reply = ask_ai(
  message.from_user.id,
  "Give a short, constructive code review of the following code. "
  "Point out any bugs, style issues, and one concrete improvement. "
  "Be encouraging and keep it concise. "
  f"Reply with only the review — no preamble.\n\nCode:\n{code}",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["quiz"], func=is_allowed)
def cmd_quiz(message):
 topic = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
 if not topic:
  bot.send_message(message.chat.id, "Usage: /quiz <topic>  (e.g. /quiz python lists)")
  return
 question = ask_ai(
  message.from_user.id,
  f"Create one short quiz question about: {topic}. "
  "Ask a single clear question that has a definite correct answer. "
  "Do NOT reveal or hint at the answer. Reply with only the question — no preamble.",
 )
 sent = bot.send_message(message.chat.id, f"❓ {question}\n\nReply with your answer.")
 bot.register_next_step_handler(sent, _grade_quiz, question)
def _grade_quiz(message, question):
 answer = (message.text or "").strip()
 if not answer:
  bot.send_message(message.chat.id, "No answer given — quiz cancelled.")
  return
 reply = ask_ai(
  message.from_user.id,
  f"Quiz question: {question}\n"
  f"Student's answer: {answer}\n\n"
  "Say whether the answer is correct, then give the correct answer with a one-sentence "
  "explanation. Be encouraging and concise.",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["summarize"], func=is_allowed)
def cmd_summarize(message):
 text = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
 if not text:
  bot.send_message(message.chat.id, "Usage: /summarize <text>\nPaste the text you'd like summarized.")
  return
 reply = ask_ai(
  message.from_user.id,
  "Summarize the following text concisely, capturing the key points as a short "
  "paragraph or a few bullet points. Do not add opinions or information that isn't "
  f"in the text. Reply with only the summary — no preamble.\n\nText:\n{text}",
 )
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["roll"], func=is_allowed)
def cmd_roll(message):
 result = random.randint(1, 6)
 bot.send_message(message.chat.id, f"🎲 You rolled a {result}!")

@bot.message_handler(commands=["roast"], func=is_allowed)
def cmd_roast(message):
 sent = bot.send_message(message.chat.id, "Who should I roast? Send me a name.")
 bot.register_next_step_handler(sent, _do_roast)
def _do_roast(message):
 name = (message.text or "").strip()
 if not name:
  bot.send_message(message.chat.id, "No name given — roast cancelled.")
  return
 reply = ask_ai(
  message.from_user.id,
  f"Write a short, brutal, savage roast of {name}. "
  "Go hard — be sharp, witty, and merciless. Don't hold back or soften it, "
  "but keep it clever comedy (no slurs, no protected-class attacks, nothing genuinely hateful). "
  "Keep it to 1-3 punchy lines. Reply with only the roast — no preamble, no disclaimers.",
 )
 bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=["remember"], func=is_allowed)
def cmd_remember(message):
 if store is None:
  bot.send_message(message.chat.id, "Notes need storage, which isn't set up right now.")
  return
 note = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
 if not note:
  bot.send_message(message.chat.id, "Usage: /remember <something to note>")
  return
 key = f"notes:{message.from_user.id}"
 raw = store.get(key)
 notes = json.loads(raw) if raw else []  # strings only — decode the list on the way out
 notes.append(note)  # append, don't replace
 store.set(key, json.dumps(notes))  # encode the list on the way in
 bot.send_message(message.chat.id, f"Saved! You now have {len(notes)} note(s).")


@bot.message_handler(commands=["recall"], func=is_allowed)
def cmd_recall(message):
 if store is None:
  bot.send_message(message.chat.id, "Notes need storage, which isn't set up right now.")
  return
 raw = store.get(f"notes:{message.from_user.id}")
 notes = json.loads(raw) if raw else []
 if not notes:
  bot.send_message(message.chat.id, "You have no saved notes. Add one with /remember <text>")
  return
 lines = [f"{i}. {note}" for i, note in enumerate(notes, start=1)]
 bot.send_message(message.chat.id, "Your notes:\n" + "\n".join(lines))


@bot.message_handler(commands=["forget"], func=is_allowed)
def cmd_forget(message):
 if store is None:
  bot.send_message(message.chat.id, "Notes need storage, which isn't set up right now.")
  return
 store.delete(f"notes:{message.from_user.id}")
 bot.send_message(message.chat.id, "All your notes have been cleared.")


@bot.message_handler(commands=["help"], func=is_allowed)
def cmd_help(message):
    lines = [f"/{name} — {desc}" for name, desc in command_menu()]
    bot.send_message(message.chat.id, "\n".join(lines))


@bot.message_handler(commands=["reset"], func=is_allowed)
def cmd_reset(message):
    clear_history(message.from_user.id)
    bot.send_message(message.chat.id, "Conversation cleared. Starting fresh!")


@bot.message_handler(commands=["about"], func=is_allowed)
def cmd_about(message):
    if HF_SPACE_ID:
        provider = get_provider(message.from_user.id)
        model_line = f"{MODEL} (main)" if provider == "main" else f"{HF_SPACE_ID} (hf)"
    else:
        model_line = MODEL
    storage_line = "SQLite" if store is not None else "stateless (no memory)"
    lines = [
        f"Model  : {model_line}",
        f"Storage: {storage_line}",
        f"Hosting: {HOSTING_LABEL}",
    ]
    if COMMIT_SHA:
        lines.append(f"Version: {COMMIT_SHA}")
    bot.send_message(message.chat.id, "\n".join(lines))


@bot.message_handler(commands=["model"], func=is_allowed)
def cmd_model(message):
    """Show the active AI model, or switch with `/model <name>`.

    With no argument it reports the current model. With an argument it
    switches, accepting either the provider key or the display name."""
    parts = (message.text or "").split(maxsplit=1)
    models = available_models()
    if len(parts) == 1 or not parts[1].strip():
        current = active_model(message.from_user.id)
        text = f"Current model: {current['name']}"
        if len(models) > 1:
            text += "\n\nUse /models to list all, or /model <name> to switch."
        bot.send_message(message.chat.id, text)
        return
    choice = parts[1].strip()
    target = _resolve_model(choice, models)
    if target is None:
        bot.send_message(
            message.chat.id,
            f"Unknown model: {choice}. Use /models to see what's available.",
        )
        return
    if not set_provider(message.from_user.id, target["key"]):
        bot.send_message(message.chat.id, "Could not save preference. Try again later.")
        return
    if target["key"] == "hf":
        bot.send_message(
            message.chat.id,
            "Switched to ArmGPT (hf).\n\n"
            "Note: this is a tiny base completion model trained only on Armenian text. "
            "It will continue whatever you write rather than answer questions, "
            "and it does not understand English. Replies take ~30-60s and there is no memory.",
        )
    else:
        bot.send_message(
            message.chat.id, f"Switched to the Main model ({target['name']})."
        )


@bot.message_handler(commands=["models"], func=is_allowed)
def cmd_models(message):
    """List every available AI model with its description and active status."""
    models = available_models()
    current = active_model(message.from_user.id)
    lines = ["Available models:"]
    for model in models:
        marker = " — active" if model["key"] == current["key"] else ""
        lines.append(f"• {model['name']}{marker}")
        lines.append(f"   {model['description']}")
    if len(models) > 1:
        lines.append("")
        lines.append("Switch with /model <name>.")
    bot.send_message(message.chat.id, "\n".join(lines))


@bot.message_handler(content_types=["text"], func=is_allowed)
def handle_message(message):
    if not should_respond(message):
        return
    text = (message.text or "").replace(f"@{BOT_INFO.username}", "").strip()
    if not text:
        # Edited messages, forwards, or stickers-with-empty-caption can
        # arrive with no usable text. Don't burn rate-limit / AI calls on them.
        return
    _log(message, "in", text)
    if is_rate_limited(message.from_user.id):
        limit_msg = f"You've reached the daily limit of {RATE_LIMIT} messages. Try again tomorrow."
        bot.send_message(message.chat.id, limit_msg)
        _log(message, "out", f"[rate limited] {limit_msg}")
        return
    try:
        with keep_typing(message.chat.id):
            reply = ask_ai(message.from_user.id, text)
        send_reply(message, reply)
        _log(message, "out", reply)
    except Exception as e:
        print(f"Error in handle_message: {e}")
        bot.send_message(message.chat.id, "Something went wrong. Please try again.")
        _log(message, "out", f"[error] {e}")
        