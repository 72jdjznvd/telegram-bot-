# Telegram Echo Bot

A simple Telegram bot built with [python-telegram-bot](https://python-telegram-bot.org/) that echoes every message back to the sender.

## Setup

1. **Set your bot token** — add `BOT_TOKEN` to the Replit Secrets panel (the lock icon in the sidebar). Get a token from [@BotFather](https://t.me/BotFather) on Telegram.

2. **Install dependencies**:
   ```bash
   pip install -r telegram-bot/requirements.txt
   ```

3. **Run the bot**:
   ```bash
   python telegram-bot/bot.py
   ```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Greet the user and explain what the bot does |
| _(any text)_ | Echo the message back |

## Extending the bot

To add a new command, create an async handler function and register it:

```python
async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello from my command!")

app.add_handler(CommandHandler("mycommand", my_command))
```
