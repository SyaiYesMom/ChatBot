import asyncio
import logging
from typing import Optional

from telegram import Update

MAX_MESSAGE_LENGTH = 4000


async def safe_reply(
    update: Update,
    text: Optional[str],
    *,
    disable_notification: bool = False,
) -> None:
    """Kirim balasan ke user, otomatis pecah jika melewati limit Telegram dan retry saat timeout."""
    if not update or not update.message or not text:
        return

    chunks = [
        text[i : i + MAX_MESSAGE_LENGTH]
        for i in range(0, len(text), MAX_MESSAGE_LENGTH)
    ]

    for chunk in chunks:
        for attempt in range(3):
            try:
                await update.message.reply_text(
                    chunk,
                    disable_notification=disable_notification,
                )
                break
            except Exception as err:
                if attempt < 2:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                logging.error(
                    "Gagal mengirim pesan ke Telegram setelah beberapa kali retry: %s",
                    err,
                    exc_info=True,
                )

