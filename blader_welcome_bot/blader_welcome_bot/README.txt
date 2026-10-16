# Blader Welcome Bot

## Discord Developer Portal
1. Create an application and add a Bot.
2. In Bot settings, enable **Server Members Intent** and **Message Content Intent**.
3. Invite the bot with `View Channels`, `Send Messages`, `Attach Files`, and `Read Message History` permissions. It also needs permission to view the welcome channel.
4. Keep the bot token secret; never paste it into chat or commit it to a public repository.

## Run locally
- Install Python 3.11 or newer.
- Run `pip install -r requirements.txt`
- Set `DISCORD_TOKEN` as an environment variable.
- Run `python bot.py`

## Railway
1. Upload these files to a private GitHub repository.
2. Create a Railway project from that repository.
3. Add a service variable named `DISCORD_TOKEN` with your bot token.
4. Deploy as a worker/service. The Procfile starts `python bot.py`.
5. Free Railway resources are limited and may not keep the bot online continuously.

## Commands
- `!welcome-message-open` — enables welcome cards in the channel where an administrator runs it.
- `!welcome-message-close` — disables welcome cards.
Only members with **Manage Server** permission can run these commands.

The channel selection is stored in `welcome_config.json`. On Railway, local files can be ephemeral across redeploys; if settings reset, run the open command again.
