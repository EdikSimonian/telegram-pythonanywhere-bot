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
    ("optimize", "optimize code for speed and clarity"),
    ("test", "generate unit tests for your code"),
    ("document", "add docstrings and comments to code"),
    ("complexity", "analyze time & space complexity"),
    ("regex", "build or explain a regular expression"),
    ("convert", "convert numbers, bases, and units"),
    ("cheatsheet", "quick reference for a topic"),
    ("quiz", "take a quick quiz on a topic"),
    ("summarize", "summarize a block of text"),
    ("roll", "roll the dice"),
    ("roast", "get roasted"),
    ("remember", "save a note"),
    ("recall", "list your notes"),
    ("forget", "clear your notes"),
]


def command_menu():
    """Full (command, description) list including the conditional /model
    command. Shared by /help and the Telegram command-menu registration."""
    cmds = list(COMMANDS)
    if HF_SPACE_ID:
        cmds.append(("model", "switch AI provider"))
    return cmds


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


# --- New coding tools -------------------------------------------------------

@bot.message_handler(commands=["optimize"], func=is_allowed)
def cmd_optimize(message):
    code = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
    if not code:
        bot.send_message(message.chat.id, "Usage: /optimize <code>\nPaste the code you'd like optimized.")
        return
    reply = ask_ai(
        message.from_user.id,
        "Optimize the following code for performance and readability. "
        "Note what you improved in 1-2 sentences, then show the optimized version "
        "in a code block. Keep the same behavior. "
        f"Reply with only the answer — no preamble.\n\nCode:\n{code}",
    )
    bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=["test"], func=is_allowed)
def cmd_test(message):
    code = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
    if not code:
        bot.send_message(message.chat.id, "Usage: /test <code>\nPaste the function or code you'd like tests for.")
        return
    reply = ask_ai(
        message.from_user.id,
        "Write clear unit tests for the following code. Cover the main cases plus one "
        "or two edge cases, using the language's standard testing style. "
        f"Reply with only the tests in a code block — no preamble.\n\nCode:\n{code}",
    )
    bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=["document"], func=is_allowed)
def cmd_document(message):
    code = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
    if not code:
        bot.send_message(message.chat.id, "Usage: /document <code>\nPaste the code you'd like documented.")
        return
    reply = ask_ai(
        message.from_user.id,
        "Add clear docstrings and brief inline comments to the following code. "
        "Do not change what the code does. Keep comments concise and useful. "
        f"Reply with only the documented code in a code block — no preamble.\n\nCode:\n{code}",
    )
    bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=["complexity"], func=is_allowed)
def cmd_complexity(message):
    code = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
    if not code:
        bot.send_message(message.chat.id, "Usage: /complexity <code>\nPaste the code you'd like analyzed.")
        return
    reply = ask_ai(
        message.from_user.id,
        "Analyze the time and space complexity (Big-O) of the following code. "
        "State both clearly, then explain why in 1-2 sentences. If it can be improved, "
        f"mention the better complexity briefly. Reply with only the analysis — no preamble.\n\nCode:\n{code}",
    )
    bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=["regex"], func=is_allowed)
def cmd_regex(message):
    desc = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
    if not desc:
        bot.send_message(
            message.chat.id,
            "Usage: /regex <what to match>\nExample: /regex a valid email address",
        )
        return
    reply = ask_ai(
        message.from_user.id,
        f"Create a regular expression for: {desc}. Show the regex in a code block, then "
        "explain each part in a few short bullet points and give one matching example. "
        "Keep it concise. Reply with only the answer — no preamble.",
    )
    bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=["cheatsheet"], func=is_allowed)
def cmd_cheatsheet(message):
    topic = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
    if not topic:
        bot.send_message(message.chat.id, "Usage: /cheatsheet <topic>  (e.g. /cheatsheet git)")
        return
    reply = ask_ai(
        message.from_user.id,
        f"Create a short, practical cheatsheet for: {topic}. List the most useful commands "
        "or concepts with a one-line description each, grouped if it helps. Keep it compact "
        "and skimmable. Reply with only the cheatsheet — no preamble.",
    )
    bot.send_message(message.chat.id, reply)


# --- Converter --------------------------------------------------------------
# /convert does exact number-base math itself (bin/oct/dec/hex) and only falls
# back to the AI for everything else (units, temperature, etc.). That keeps the
# common case instant and reliable instead of guessing.

# Base names users can type -> numeric base.
_BASES = {
    "bin": 2, "binary": 2,
    "oct": 8, "octal": 8,
    "dec": 10, "decimal": 10,
    "hex": 16, "hexadecimal": 16,
}


def _try_base_convert(arg):
    """Try an exact number-base conversion (bin/oct/dec/hex).

    Returns a formatted result string on success, or None if `arg` doesn't
    look like a base conversion — so the caller can fall back to the AI.

    Understands:
      "255 to hex"      decimal in, hex out
      "0xff to dec"     0x / 0o / 0b prefixes set the source base
      "ff hex to bin"   an explicit source-base word also works
    """
    tokens = arg.lower().split()
    if "to" not in tokens:
        return None
    i = tokens.index("to")
    left, right = tokens[:i], tokens[i + 1:]
    if not left or not right:
        return None

    target = right[0]
    if target not in _BASES:
        return None
    target_base = _BASES[target]

    raw = left[0]
    src_base = _BASES[left[1]] if len(left) >= 2 and left[1] in _BASES else None

    # Fall back to 0x/0o/0b prefixes when no source-base word was given.
    if src_base is None:
        if raw.startswith("0x"):
            src_base, raw = 16, raw[2:]
        elif raw.startswith("0o"):
            src_base, raw = 8, raw[2:]
        elif raw.startswith("0b"):
            src_base, raw = 2, raw[2:]
        else:
            src_base = 10  # bare numbers are read as decimal

    if not raw:
        return None
    try:
        value = int(raw, src_base)
    except ValueError:
        return None  # not valid in that base -> let the AI handle it

    sign = "-" if value < 0 else ""
    mag = abs(value)
    formats = {2: "b", 8: "o", 16: "x"}
    if target_base in formats:
        body = format(mag, formats[target_base])
        prefix = {2: "0b", 8: "0o", 16: "0x"}[target_base]
    else:
        body = str(mag)
        prefix = ""
    return f"{arg} = {sign}{prefix}{body}"


@bot.message_handler(commands=["convert"], func=is_allowed)
def cmd_convert(message):
    arg = message.text.split(maxsplit=1)[1].strip() if " " in message.text else ""
    if not arg:
        bot.send_message(
            message.chat.id,
            "Usage: /convert <value> to <target>\n\n"
            "Number bases (instant, exact):\n"
            "  /convert 255 to hex\n"
            "  /convert 0xff to dec\n"
            "  /convert 0b1010 to dec\n"
            "  /convert ff hex to bin\n\n"
            "Units and everything else (via AI, approximate):\n"
            "  /convert 10 km to miles\n"
            "  /convert 100 C to F",
        )
        return
    # Fast path: exact base conversion, no AI call needed.
    result = _try_base_convert(arg)
    if result is not None:
        bot.send_message(message.chat.id, result)
        return
    # Fallback: let the AI handle units, temperature, and the rest.
    reply = ask_ai(
        message.from_user.id,
        f"Convert this value: {arg}. Give the final converted value with its unit, "
        "rounded sensibly. If the conversion is ambiguous or impossible, say so in one "
        "line. Reply with only the result — no preamble.",
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


if HF_SPACE_ID:

    @bot.message_handler(commands=["model"], func=is_allowed)
    def cmd_model(message):
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) == 1:
            current = get_provider(message.from_user.id)
            bot.send_message(
                message.chat.id,
                f"Current provider: {current}\n\n"
                "Options:\n"
                "/model main — Cerebras (fast, multilingual, with memory)\n"
                "/model hf — ArmGPT (Armenian only, slow, no memory)",
            )
            return
        choice = parts[1].strip().lower()
        if choice not in ("main", "hf"):
            bot.send_message(
                message.chat.id, "Invalid choice. Use: /model main or /model hf"
            )
            return
        if not set_provider(message.from_user.id, choice):
            bot.send_message(
                message.chat.id, "Could not save preference. Try again later."
            )
            return
        if choice == "hf":
            bot.send_message(
                message.chat.id,
                "Switched to hf (ArmGPT).\n\n"
                "Note: this is a tiny base completion model trained only on Armenian text. "
                "It will continue whatever you write rather than answer questions, "
                "and it does not understand English. Replies take ~30-60s and there is no memory.",
            )
        else:
            bot.send_message(message.chat.id, "Switched to Main Provider.")


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