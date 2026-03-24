"""Downloader using Telethon (MTProto) to download large files from a chat.

Edit the constants below with your `api_id`, `api_hash`, and `CHAT_ID`.
On first run Telethon may prompt for a login code (interactive) to create a session file.

Install dependency:
    pip install telethon

Run:
    python learn/download_test.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import Optional

from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.tl.types import Message

# Optional native crypto extension
try:
    import tgcrypto  # type: ignore
    TGCRYPTO_AVAILABLE = True
except Exception:
    TGCRYPTO_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # python-dotenv not installed or no .env present — fall back to environment
    pass

def _env_bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "y", "on")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHAT_ID = os.getenv("CHAT_ID", "Test")
DEST_PATH = os.getenv("DEST_PATH", r"C:\\Telegram_UI\\DownloadTest")
SESSION_NAME = os.getenv("SESSION_NAME", "telethon_upload_session")
USE_PYROGRAM = _env_bool("USE_PYROGRAM", True)


async def test_credentials(client: TelegramClient, chat_id: str) -> bool:
    try:
        me = await client.get_me()
        print(f"Logged in as: {getattr(me, 'username', getattr(me, 'first_name', me))}")
    except Exception as e:
        print("Client login error:", e)
        return False

    try:
        ent = None
        try:
            cid = int(chat_id)
        except Exception:
            cid = None

        if cid is not None:
            ent = await client.get_entity(cid)
        else:
            try:
                ent = await client.get_entity(chat_id)
            except Exception:
                async for dialog in client.iter_dialogs():
                    if dialog.name == chat_id:
                        ent = dialog.entity
                        break

        if ent:
            print("Chat id: OK (found entity)")
        else:
            print(f"Chat id: invalid (no entity found for '{chat_id}')")
            return False
    except Exception as e:
        print("Chat id: error ->", e)
        return False

    return True


def make_progress(throttle: float = 0.5):
    state = {"t0": time.time(), "last_t": 0.0}

    def progress(current, total):
        now = time.time()
        if now - state["last_t"] < throttle and current != total:
            return
        elapsed = now - state["t0"] if now > state["t0"] else 0.0001
        speed = current / elapsed
        speed_mb = speed / (1024 * 1024)
        if total:
            pct = (current / total) * 100
            remaining = max(0, total - current)
            eta = remaining / speed if speed > 0 else float("inf")
            eta_s = int(eta)
            sys.stdout.write(
                f"\r{pct:5.1f}% — {current/(1024*1024):.2f}/{total/(1024*1024):.2f} MB "
                f"@ {speed_mb:.2f} MB/s — ETA {eta_s}s"
            )
        else:
            sys.stdout.write(f"\rDownloaded {current} bytes @ {speed_mb:.2f} MB/s")
        sys.stdout.flush()
        state["last_t"] = now

    return progress


async def find_latest_media_message(client: TelegramClient, chat_id: str) -> Optional[Message]:
    """Return the most recent message in the chat that contains media (or None)."""
    try:
        async for msg in client.iter_messages(chat_id, limit=100):
            if getattr(msg, "media", None) is not None:
                return msg
    except Exception:
        return None
    return None


async def download_latest(api_id: int, api_hash: str, chat_id: str, dest_folder: str) -> None:
    """Find the latest media message in `chat_id` and download it to `dest_folder`."""
    os.makedirs(dest_folder, exist_ok=True)

    async with TelegramClient(SESSION_NAME, api_id, api_hash) as client:
        ok = await test_credentials(client, chat_id)
        if not ok:
            raise RuntimeError("Credentials/chat test failed")

        msg = await find_latest_media_message(client, chat_id)
        if msg is None:
            raise RuntimeError("No media message found in chat")

        # determine filename
        name = None
        if getattr(msg, "file", None) is not None:
            name = getattr(msg.file, "name", None)
        if not name:
            # fallback to message id + media type
            name = f"msg_{msg.id}.bin"

        dest_path = os.path.join(dest_folder, name)

        try:
            print(f"Downloading message {msg.id} to: {dest_path}")
            await client.download_media(msg, file=dest_path, progress_callback=make_progress())
            print("\nDownload finished")
        except RPCError as e:
            print("Telegram RPC error during download:", e)
            raise


def try_pyrogram_download(api_id: int, api_hash: str, chat_id: str, dest_folder: str) -> int:
    """Try downloading the latest media using Pyrogram (sync client). Returns exit code."""
    try:
        from pyrogram import Client
    except Exception as e:
        raise RuntimeError("Pyrogram not installed. Install with: pip install pyrogram") from e

    if not os.path.isdir(dest_folder):
        os.makedirs(dest_folder, exist_ok=True)

    session = "pyro_upload_session"

    def py_prog(current, total):
        # Pyrogram progress signature is (current, total)
        make_progress()(current, total)

    with Client(session, api_id=api_id, api_hash=api_hash) as app:
        try:
            me = app.get_me()
            print(f"Logged in as: {getattr(me, 'username', getattr(me, 'first_name', me))}")
        except Exception as e:
            print("Pyrogram login error:", e)
            return 2
        try:
            # Try multiple pyrogram history APIs for compatibility across versions
            msg = None
            if hasattr(app, "get_history"):
                history = app.get_history(chat_id, limit=100)
                msg = next((m for m in history if getattr(m, "media", None) is not None), None)
            elif hasattr(app, "iter_history"):
                for m in app.iter_history(chat_id, limit=100):
                    if getattr(m, "media", None) is not None:
                        msg = m
                        break
            elif hasattr(app, "get_messages"):
                # Try common get_messages signatures across Pyrogram versions
                history = None
                try:
                    history = app.get_messages(chat_id, limit=100)
                except TypeError:
                    try:
                        history = app.get_messages(chat_id, 100)
                    except TypeError:
                        try:
                            # some versions may expect only ids or different params
                            history = app.get_messages(chat_id)
                        except Exception:
                            history = None

                if history:
                    # history may be a list-like or generator
                    try:
                        msg = next((m for m in history if getattr(m, "media", None) is not None), None)
                    except TypeError:
                        # if history is not iterable, leave msg None
                        msg = None
            else:
                raise AttributeError("Pyrogram Client has no history API")

            if msg is None:
                print("No media message found in chat (Pyrogram)")
                return 3

            # Robust filename extraction
            name = None
            if getattr(msg, "file", None) is not None:
                name = getattr(msg.file, "file_name", None) or getattr(msg.file, "file_name", None)
            if not name:
                # fallbacks for different pyrogram message shapes
                name = getattr(msg, "file_name", None) or getattr(msg, "document", None) and getattr(msg.document, "file_name", None)
            if not name:
                name = f"msg_{getattr(msg, 'message_id', getattr(msg, 'id', '?'))}.bin"

            dest_path = os.path.join(dest_folder, name)
            print(f"Pyrogram downloading message {getattr(msg, 'message_id', getattr(msg, 'id', '?'))} to: {dest_path}")
            app.download_media(msg, file_name=dest_path, progress=py_prog)
            print("\nPyrogram download finished")
        except AttributeError as ae:
            # Pyrogram version compatibility: fall back to Telethon async downloader
            print("Pyrogram client missing history API, falling back to Telethon:", ae)
            try:
                asyncio.run(download_latest(API_ID, API_HASH, chat_id, dest_folder))
                return 0
            except Exception as e:
                print("Telethon fallback failed:", e)
                return 1
        except Exception as e:
            print("Pyrogram download failed:", e)
            return 1

    return 0


def main() -> int:
    if API_ID == 123456 or API_HASH.startswith("REPLACE") or CHAT_ID.startswith("REPLACE"):
        print("Error: please edit the script and set `API_ID`, `API_HASH`, and `CHAT_ID` constants.")
        return 2
    if TGCRYPTO_AVAILABLE:
        print("tgcrypto: available — Telethon will use native crypto for faster transfers")
    else:
        print("tgcrypto: not installed — install with `pip install tgcrypto` for faster MTProto transfers")

    try:
        if USE_PYROGRAM:
            try:
                return try_pyrogram_download(API_ID, API_HASH, CHAT_ID, DEST_PATH)
            except Exception as e:
                print("Pyrogram download failed:", e)
                return 1
        else:
            asyncio.run(download_latest(API_ID, API_HASH, CHAT_ID, DEST_PATH))
    except Exception as e:
        print("Download failed:", e)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
