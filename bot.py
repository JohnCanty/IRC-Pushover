#!/opt/irc-pushover-bot/venv/bin/python3
import os
import ssl
import time
from typing import List

import requests
import irc.bot
import irc.connection


ENV_PATH = "/opt/irc-pushover-bot/.env"
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


def load_env(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()


def env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "on"}


def env_list(name: str) -> List[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [x.strip().lower() for x in raw.split(",") if x.strip()]


class PushBot(irc.bot.SingleServerIRCBot):
    def __init__(self) -> None:
        self.irc_host = os.environ["IRC_HOST"]
        self.irc_port = int(os.getenv("IRC_PORT", "6697"))
        self.irc_nick = os.environ.get("IRC_NICK", "pushbot")
        self.irc_username = os.environ.get("IRC_USERNAME", self.irc_nick)
        self.irc_realname = os.environ.get("IRC_REALNAME", self.irc_nick)
        self.irc_channel = os.environ["IRC_CHANNEL"]
        self.irc_server_password = os.getenv("IRC_SERVER_PASSWORD", "") or None
        self.irc_use_tls = env_bool("IRC_USE_TLS", True)
        self.sasl_username = os.getenv("IRC_SASL_USERNAME", "")
        self.sasl_password = os.getenv("IRC_SASL_PASSWORD", "")
        self.match_keywords = env_list("MATCH_KEYWORDS")

        self.pushover_token = os.environ["PUSHOVER_TOKEN"]
        self.pushover_user = os.environ["PUSHOVER_USER"]
        self.pushover_title = os.getenv("PUSHOVER_TITLE", "IRC Alert")

        connect_factory = irc.connection.Factory(wrapper=self._tls_wrap) if self.irc_use_tls else None

        server = (self.irc_host, self.irc_port, self.irc_server_password)
        super().__init__(
            [server],
            self.irc_nick,
            self.irc_realname,
            username=self.irc_username,
            connect_factory=connect_factory,
        )

    @staticmethod
    def _tls_wrap(sock):
        context = ssl.create_default_context()
        return context.wrap_socket(sock, server_hostname=os.getenv("IRC_HOST"))

    def on_welcome(self, connection, event):
        connection.cap("REQ", "sasl")
        connection.join(self.irc_channel)

    def on_cap(self, connection, event):
        args = event.arguments
        if len(args) >= 2 and args[0] == "*" and args[1].startswith("ACK") and "sasl" in args[-1].lower():
            connection.send_raw("AUTHENTICATE PLAIN")

    def on_authenticate(self, connection, event):
        if not self.sasl_username or not self.sasl_password:
            connection.cap("END")
            return
        import base64
        payload = f"{self.sasl_username}\0{self.sasl_username}\0{self.sasl_password}".encode("utf-8")
        connection.send_raw("AUTHENTICATE " + base64.b64encode(payload).decode("ascii"))

    def on_903(self, connection, event):
        connection.cap("END")

    def on_904(self, connection, event):
        connection.cap("END")

    def on_pubmsg(self, connection, event):
        nick = event.source.nick if event.source else "unknown"
        message = event.arguments[0]

        if nick == self.irc_nick:
            return

        if self.match_keywords:
            lowered = message.lower()
            if not any(k in lowered for k in self.match_keywords):
                return

        self.send_pushover(f"[{self.irc_channel}] <{nick}> {message}")

    def send_pushover(self, message: str) -> None:
        resp = requests.post(
            PUSHOVER_URL,
            data={
                "token": self.pushover_token,
                "user": self.pushover_user,
                "title": self.pushover_title,
                "message": message,
            },
            timeout=15,
        )
        resp.raise_for_status()


def main() -> None:
    load_env(ENV_PATH)

    while True:
        try:
            bot = PushBot()
            bot.start()
        except Exception as exc:
            print(f"bot error: {exc}", flush=True)
            time.sleep(10)


if __name__ == "__main__":
    main()