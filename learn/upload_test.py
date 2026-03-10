"""Uploader using Telethon (MTProto) to allow uploads up to 2GB.

Edit the constants below with your `api_id`, `api_hash`, and `CHAT_ID`.
On first run Telethon may prompt for a login code (interactive) to create a session file.

Install dependency:
    pip install telethon

Run:
    python learn/upload_test.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import Optional

from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.tl.functions.upload import SaveBigFilePartRequest
from telethon.tl.types import InputFileBig, DocumentAttributeFilename
import random
import math

# Maximum single-file size for a Telegram message (2 GiB)
MAX_SINGLE_FILE = 2 * 1024 * 1024 * 1024

# Optional native crypto extension speeds up MTProto encryption/decryption
try:
    import tgcrypto  # type: ignore
    TGCRYPTO_AVAILABLE = True
except Exception:
    TGCRYPTO_AVAILABLE = False

# TEST CONFIG: replace these with your API credentials and chat id
API_ID = 22171359                # replace with your api_id (int)
API_HASH = "93d92a2ce86631d5520c51548e3f9424"  # replace with your api_hash (string)
CHAT_ID = "Test DB"   # the target chat id or username
FILE_PATH = r"D:\\Photo_Video\\Backup FotoVideo\\2023\\Drone FPV\\RedStar Xiaomi\\YDXJ0134.MP4"
SESSION_NAME = "telethon_upload_session"
# Set to True to try Pyrogram transport instead of Telethon
USE_PYROGRAM = True
# Use low-level saveBigFilePart parallel uploader (experimental)
USE_SAVEBIG_PARALLEL = True


async def test_credentials(client: TelegramClient, chat_id: str) -> bool:
    """Test that client is authorized and chat exists.

    Returns True when both checks pass.
    """
    try:
        me = await client.get_me()
        print(f"Logged in as: {getattr(me, 'username', getattr(me, 'first_name', me))}")
    except Exception as e:
        print("Client login error:", e)
        return False

    try:
        ent = None
        # try numeric id first
        try:
            cid = int(chat_id)
        except Exception:
            cid = None

        if cid is not None:
            ent = await client.get_entity(cid)
        else:
            # try username/@username or exact entity
            try:
                ent = await client.get_entity(chat_id)
            except Exception:
                # fallback: search dialogs by title (chat display name)
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


async def send_large_file(api_id: int, api_hash: str, chat_id: str, file_path: str, caption: Optional[str] = None) -> None:
    """Send a potentially large file using Telethon's `send_file` (handles chunking).

    This will create a local session file the first time it runs and may prompt for login.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)

    async with TelegramClient(SESSION_NAME, api_id, api_hash) as client:
        ok = await test_credentials(client, chat_id)
        if not ok:
            raise RuntimeError("Credentials/chat test failed")

        try:
            print("Uploading... this may take a while for large files")

            # progress callback factory to reduce print frequency and show MB/s + ETA
            def make_progress(throttle: float = 0.5):
                state = {"t0": time.time(), "last_t": 0.0}

                def progress(current, total):
                    now = time.time()
                    # throttle updates to avoid flooding the console
                    if now - state["last_t"] < throttle and current != total:
                        return
                    elapsed = now - state["t0"] if now > state["t0"] else 0.0001
                    speed = current / elapsed  # bytes/sec
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
                        sys.stdout.write(f"\rUploaded {current} bytes @ {speed_mb:.2f} MB/s")
                    sys.stdout.flush()
                    state["last_t"] = now

                return progress

            # Increase part size to reduce protocol overhead (4 MiB chunks)
            await client.send_file(chat_id, file_path, caption=caption, progress_callback=make_progress(), part_size_kb=16384)
            # ensure newline after progress
            print("\nUpload finished")
        except RPCError as e:
            print("Telegram RPC error during upload:", e)
            raise


async def upload_savebig_parallel(client: TelegramClient, chat_id: str, file_path: str, part_size: int = 4 * 1024 * 1024, parallel: int = 4, caption: Optional[str] = None):
    """Upload file parts in parallel using upload.saveBigFilePart and then send as InputFileBig.

    Experimental: uses low-level MTProto `upload.saveBigFilePart`. You may need `tgcrypto`.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)

    total_size = os.path.getsize(file_path)
    fname = os.path.basename(file_path)

    # If file fits in one message, upload normally; otherwise split into multiple messages
    segment_count = math.ceil(total_size / MAX_SINGLE_FILE)
    segment_index = 0

    with open(file_path, "rb") as f:
        while segment_index < segment_count:
            seg_offset = segment_index * MAX_SINGLE_FILE
            seg_size = min(MAX_SINGLE_FILE, total_size - seg_offset)
            parts = math.ceil(seg_size / part_size)

            # file_id must be a 64-bit non-negative int
            file_id = random.randrange(1 << 62)

            sem = asyncio.Semaphore(parallel)

            async def send_part(part_index: int, data: bytes):
                async with sem:
                    t0 = time.time()
                    await client(SaveBigFilePartRequest(file_id, part_index, parts, data))
                    t1 = time.time()
                    elapsed = max(1e-6, t1 - t0)
                    speed = len(data) / elapsed
                    speed_mb = speed / (1024 * 1024)
                    print(f"Uploaded part {part_index + 1}/{parts} — {speed_mb:.2f} MB/s")

            # seek to segment start and prepare tasks for this segment
            f.seek(seg_offset)
            tasks = []
            part_index = 0
            while part_index < parts:
                chunk = f.read(part_size)
                if not chunk:
                    break
                tasks.append(asyncio.ensure_future(send_part(part_index, chunk)))
                part_index += 1

            print(f"Uploading segment {segment_index + 1}/{segment_count} ({parts} parts) with parallel={parallel}...")
            await asyncio.gather(*tasks)

            # assemble InputFileBig and send for this segment
            seg_name = fname if segment_count == 1 else f"{fname}.part{segment_index+1:03d}"
            input_file = InputFileBig(file_id=file_id, parts=parts, name=seg_name)
            attrs = [DocumentAttributeFilename(seg_name)]
            seg_caption = caption
            if segment_count > 1:
                seg_caption = (caption or "") + f" (part {segment_index+1}/{segment_count})"
            print(f"All parts uploaded for segment {segment_index+1}. Sending InputFileBig...")
            await client.send_file(chat_id, input_file, caption=seg_caption, attributes=attrs)

            segment_index += 1


async def send_savebig_wrapper(api_id: int, api_hash: str, chat_id: str, file_path: str, caption: Optional[str] = None):
    async with TelegramClient(SESSION_NAME, api_id, api_hash) as client:
        ok = await test_credentials(client, chat_id)
        if not ok:
            raise RuntimeError("Credentials/chat test failed")
        await upload_savebig_parallel(client, chat_id, file_path, part_size= 512 * 1024, parallel=4, caption=caption)


def try_pyrogram_upload(api_id: int, api_hash: str, chat_id: str, file_path: str, caption: Optional[str] = None) -> int:
    """Try uploading using Pyrogram (sync client). Returns exit code.

    Requires: `pip install pyrogram tgcrypto`
    """
    try:
        from pyrogram import Client
    except Exception as e:
        raise RuntimeError("Pyrogram not installed. Install with: pip install pyrogram tgcrypto") from e

    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)

    session = "pyro_upload_session"

    def make_progress():
        t0 = time.time()

        def progress(current, total):
            now = time.time()
            elapsed = max(0.0001, now - t0)
            speed = current / elapsed
            speed_mb = speed / (1024 * 1024)
            if total:
                pct = (current / total) * 100
                remaining = max(0, total - current)
                eta = int(remaining / speed) if speed > 0 else -1
                sys.stdout.write(
                    f"\r{pct:5.1f}% — {current/(1024*1024):.2f}/{total/(1024*1024):.2f} MB "
                    f"@ {speed_mb:.2f} MB/s — ETA {eta}s"
                )
            else:
                sys.stdout.write(f"\rUploaded {current} bytes @ {speed_mb:.2f} MB/s")
            sys.stdout.flush()

        return progress

    # Pyrogram Client expects the session name as the first positional arg (or `name=`)
    with Client(session, api_id=api_id, api_hash=api_hash) as app:
        try:
            me = app.get_me()
            print(f"Logged in as: {getattr(me, 'username', getattr(me, 'first_name', me))}")
        except Exception as e:
            print("Pyrogram login error:", e)
            return 2

        try:
            print("Pyrogram uploading...")
            app.send_document(chat_id, file_path, caption=caption, progress=make_progress())
            print("\nPyrogram upload finished")
        except Exception as e:
            print("Pyrogram upload failed:", e)
            return 1

    return 0


async def try_pyrogram_savefilepart(api_id: int, api_hash: str, chat_id: str, file_path: str, part_size: int = 4 * 1024 * 1024, caption: Optional[str] = None) -> int:
    """Sequentially upload file parts using Pyrogram raw SaveFilePart, then send as InputFileBig.

    This is a synchronous implementation (no parallelism) to avoid thread-safety issues.
    Requires: `pip install pyrogram tgcrypto`
    """
    try:
        from pyrogram import Client
        from pyrogram import raw
    except Exception as e:
        raise RuntimeError("Pyrogram not installed. Install with: pip install pyrogram tgcrypto") from e

    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)

    session = "pyro_upload_session"

    async with Client(session, api_id=api_id, api_hash=api_hash) as app:
        try:
            me = await app.get_me()
            print(f"Logged in as: {getattr(me, 'username', getattr(me, 'first_name', me))}")
        except Exception as e:
            print("Pyrogram login error:", e)
            return 2

        total_size = os.path.getsize(file_path)
        fname = os.path.basename(file_path)
        segment_count = math.ceil(total_size / MAX_SINGLE_FILE)

        with open(file_path, "rb") as f:
            for seg_idx in range(segment_count):
                seg_offset = seg_idx * MAX_SINGLE_FILE
                seg_size = min(MAX_SINGLE_FILE, total_size - seg_offset)
                parts = math.ceil(seg_size / part_size)
                seg_file_id = random.randrange(1 << 62)
                seg_name = fname if segment_count == 1 else f"{fname}.part{seg_idx+1:03d}"
                seg_caption = (caption or "") + (f" (part {seg_idx+1}/{segment_count})" if segment_count > 1 else "")

                # upload parts for this segment sequentially
                f.seek(seg_offset)
                for part_index in range(parts):
                    chunk = f.read(part_size)
                    if not chunk:
                        break
                    attempt = 0
                    max_retries = 5
                    base_backoff = 0.5
                    while True:
                        attempt += 1
                        t0 = time.time()
                        try:
                            await app.invoke(
                                raw.functions.upload.SaveBigFilePart(
                                    file_id=seg_file_id,
                                    file_part=part_index,
                                    file_total_parts=parts,
                                    bytes=chunk,
                                )
                            )
                            t1 = time.time()
                            elapsed = max(1e-6, t1 - t0)
                            speed = len(chunk) / elapsed
                            speed_mb = speed / (1024 * 1024)
                            print(f"Uploaded part {part_index + 1}/{parts} for segment {seg_idx+1} — {speed_mb:.2f} MB/s")
                            break
                        except Exception as e:
                            print(f"[{attempt}] Retrying \"upload.SaveBigFilePart\" due to: {e}")
                            if attempt >= max_retries:
                                print("Max retries reached for part", part_index)
                                return 1
                            backoff = base_backoff * (2 ** (attempt - 1))
                            jitter = random.uniform(0, 0.5)
                            await asyncio.sleep(backoff + jitter)
                    
                await app.send_document(chat_id, raw.types.InputFileBig(seg_file_id, parts, seg_name), caption=seg_caption)

                # After all parts uploaded for this segment, send assembled message with Telethon
                print(f"All parts uploaded for segment {seg_idx+1} ({seg_size} bytes). Sending message via Telethon...")

    return 0


def main() -> int:
    if API_ID == 123456 or API_HASH.startswith("REPLACE") or CHAT_ID.startswith("REPLACE"):
        print("Error: please edit the script and set `API_ID`, `API_HASH`, and `CHAT_ID` constants.")
        return 2
    if TGCRYPTO_AVAILABLE:
        print("tgcrypto: available — Telethon will use native crypto for faster uploads")
    else:
        print("tgcrypto: not installed — install with `pip install tgcrypto` for much faster MTProto transfers")
    try:
        if USE_PYROGRAM:
            # try Pyrogram synchronous client (requires `pyrogram` package)
            try:
                return asyncio.run(try_pyrogram_savefilepart(API_ID, API_HASH, CHAT_ID, FILE_PATH, part_size= 512 * 1024, caption="Test upload (Pyrogram SaveFilePart)"))
                #return try_pyrogram_upload(API_ID, API_HASH, CHAT_ID, FILE_PATH, caption="Test upload (Pyrogram)")
            except Exception as e:
                print("Pyrogram upload failed:", e)
                return 1
        elif USE_SAVEBIG_PARALLEL:
            try:
                asyncio.run(send_savebig_wrapper(API_ID, API_HASH, CHAT_ID, FILE_PATH, caption="Test upload (saveBigParallel)"))
            except Exception as e:
                print("saveBig parallel upload failed:", e)
                return 1
        else:
            asyncio.run(send_large_file(API_ID, API_HASH, CHAT_ID, FILE_PATH, caption="Test upload (Telethon)"))
    except FileNotFoundError:
        print(f"Error: file not found: {FILE_PATH}")
        return 3
    except Exception as e:
        print("Upload failed:", e)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
