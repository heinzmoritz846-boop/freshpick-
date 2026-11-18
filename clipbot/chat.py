"""Anonymous read-only Twitch chat (justinfan). Usernames are never parsed or stored."""
from __future__ import annotations
import socket
import ssl
import threading
import time
from typing import Callable

HOST, PORT = "irc.chat.twitch.tv", 6697


def watch_chat(channel: str, on_message: Callable[[str], None], stop: threading.Event) -> None:
    channel = channel.lower().lstrip("#")
    backoff = 5
    while not stop.is_set():
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((HOST, PORT), timeout=30) as raw, ctx.wrap_socket(raw, server_hostname=HOST) as s:
                s.settimeout(120)
                s.sendall(b"PASS SCHMOOPIIE\r\nNICK justinfan48213\r\n")
                s.sendall(f"JOIN #{channel}\r\n".encode())
                backoff = 5
                buf = b""
                while not stop.is_set():
                    data = s.recv(4096)
                    if not data:
                        break
                    buf += data
                    while b"\r\n" in buf:
                        line, buf = buf.split(b"\r\n", 1)
                        text = line.decode("utf-8", "ignore")
                        if text.startswith("PING"):
                            s.sendall(b"PONG :tmi.twitch.tv\r\n")
                        elif " PRIVMSG #" in text:
                            msg = text.split(" PRIVMSG #", 1)[1].split(" :", 1)
                            if len(msg) == 2:
                                on_message(msg[1])  # only the text, never the sender
        except Exception as e:  # reconnect on any network error
            print(f"[chat:{channel}] {e!r}, retry in {backoff}s", flush=True)
        stop.wait(backoff)
        backoff = min(backoff * 2, 120)
