# IRC → Pushover Bot (Ergo + Debian + systemd)

This guide walks through the **first 12 steps** to build a simple IRC bot that listens in a channel and forwards messages to **Pushover**.

Target environment:
- Debian 13 (Tested)
- Ergo IRC server
- Python virtual environment
- systemd service

---

## Overview

The bot will:

- Connect to the IRC server (Ergo Tested)
- Join a channel
- Watch for messages (optionally filtered)
- Send notifications via Pushover

---

## Step 1 – Install Required Packages

```bash
sudo apt update
sudo apt install -y git python3 python3-venv ca-certificates curl
```

---

## Step 2 – Create a Service User

```bash
sudo useradd --system \
  --create-home \
  --home-dir /opt/irc-pushover-bot \
  --shell /usr/sbin/nologin \
  ircbot
```

---

## Step 3 – Create Application Directory and Clone Repo

```bash
sudo mkdir -p /opt/irc-pushover-bot
sudo chown -R ircbot:ircbot /opt/irc-pushover-bot
sudo -u ircbot git clone https://github.com/.git /opt/irc-pushover-bot
```

If the repo already exists and you are updating it:

```bash
sudo -u ircbot git -C /opt/irc-pushover-bot pull --ff-only
```

---

## Step 4 – Create Python Virtual Environment

```bash
sudo -u ircbot python3 -m venv /opt/irc-pushover-bot/venv
```

---

## Step 5 – Install Python Dependencies

```bash
sudo -u ircbot /opt/irc-pushover-bot/venv/bin/pip install --upgrade pip
sudo -u ircbot /opt/irc-pushover-bot/venv/bin/pip install -r /opt/irc-pushover-bot/requirements.txt
```

If `requirements.txt` is missing, install manually:

```bash
sudo -u ircbot /opt/irc-pushover-bot/venv/bin/pip install irc requests
```

---

## Step 6 – Create Environment Configuration File

```bash
sudo -u ircbot tee /opt/irc-pushover-bot/.env > /dev/null <<'EOF'
IRC_HOST=irc.FuPCInternational.com
IRC_PORT=6697
IRC_NICK=pushbot
IRC_USERNAME=pushbot
IRC_REALNAME=Pushbot
IRC_CHANNEL=#alerts
IRC_USE_TLS=true

# Optional auth
IRC_SERVER_PASSWORD=
IRC_SASL_USERNAME=pushbot
IRC_SASL_PASSWORD=REPLACE_ME

# Filters (comma-separated, optional)
MATCH_KEYWORDS=alert,urgent,john

# Pushover
PUSHOVER_TOKEN=REPLACE_WITH_APP_TOKEN
PUSHOVER_USER=REPLACE_WITH_USER_KEY
PUSHOVER_TITLE=IRC Alert
EOF
```

```bash
sudo chmod 600 /opt/irc-pushover-bot/.env
sudo chown ircbot:ircbot /opt/irc-pushover-bot/.env
```

---

## Step 7 – Verify Bot Script and Lock Permissions

```bash
sudo -u ircbot test -f /opt/irc-pushover-bot/bot.py && echo "bot.py found"
```

If you need to edit the script from the checked-out repo:

```bash
sudo -u ircbot nano /opt/irc-pushover-bot/bot.py
```

Re-apply secure ownership and permissions after updates:

```bash
sudo chown -R ircbot:ircbot /opt/irc-pushover-bot
sudo chmod 700 /opt/irc-pushover-bot
sudo chmod 750 /opt/irc-pushover-bot/bot.py
sudo chmod 640 /opt/irc-pushover-bot/requirements.txt
sudo chmod 600 /opt/irc-pushover-bot/.env
```

---

## Step 8 – Test the Bot Manually

```bash
sudo -u ircbot /opt/irc-pushover-bot/venv/bin/python /opt/irc-pushover-bot/bot.py
```

---

## Step 9 – Create systemd Service

```bash
sudo nano /etc/systemd/system/irc-pushover-bot.service
```

Paste:

```ini
[Unit]
Description=IRC to Pushover Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ircbot
Group=ircbot
WorkingDirectory=/opt/irc-pushover-bot
ExecStart=/opt/irc-pushover-bot/venv/bin/python -u /opt/irc-pushover-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Step 10 – Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now irc-pushover-bot.service
```

---

## Step 11 – View Logs

```bash
sudo journalctl -u irc-pushover-bot.service -f
```

---

## Step 12 – Restart After Changes

```bash
sudo systemctl restart irc-pushover-bot.service
```

---

## File Layout

```
/opt/irc-pushover-bot/
├── .env
├── bot.py
└── venv/
```

---

## Notes

- Use a dedicated IRC account for the bot
- Prefer SASL authentication
- Restrict keyword filters to avoid spam
- Store secrets securely (`chmod 600`)

---

## Next Steps (Optional)

- Add JOIN/PART notifications
- Add rate limiting
- Deploy in Kubernetes instead of systemd
- Add TLS client certificate authentication

---