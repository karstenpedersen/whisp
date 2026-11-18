# whisp

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- A Telegram account

## Setup

The program needs an access token and chat id to a Telegram bot.

Start by copying the `.env.example` file to `.env`. 

### New Telegram Bot

We can create a new Telegram bot by sending `/newbot` to `@BotFather` on Telegram and following its instructions.

This will eventually create a new bot and give you an access token to send messages to it.

Put this access token into your `.env` file at the `TELEGRAM_BOT_TOKEN` field.

### Getting Chat ID

We also need a chat id to our bot.

We can get a chat id by sending a message to our bot, and then quickly running the following command:

```
uv run whisp bot-info
```

On success, this will print a number which will be the `TELEGRAM_CHAT_ID`. Put this into our `.env` file.

Note: If it prints `None`, then send a new message and run the above command again.


## Usage

When we have sat up our Telegram bot we can now run our program:

```
# List available devices
uv run whisp devices

# Run the program
uv run whisp listen --device <device-number>
```

Note: Device number is the number from the `devices` command on the audio input device you want to use.