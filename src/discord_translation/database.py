import logging
import sqlite3
from pathlib import Path

import discord

PROJECT_ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(PROJECT_ROOT / "database.db")
conn.execute("PRAGMA foreign_keys = ON")


def setup_db():

    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guilds (
            guild_ID INTEGER PRIMARY KEY
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_channels (
            guild_ID INTEGER NOT NULL,
            channel_ID INTEGER NOT NULL,
            language_NAME TEXT NOT NULL,
            PRIMARY KEY (guild_ID, channel_ID),
            FOREIGN KEY (guild_ID)
                REFERENCES guilds (guild_ID)
                ON DELETE CASCADE
        )
    """)

    conn.commit()


# setters
def _create_guild(guild_ID):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO guilds (guild_ID) VALUES (?) "
            "ON CONFLICT(guild_ID) DO NOTHING",
            (guild_ID,),
        )
        conn.commit()
    finally:
        cursor.close()


def create_channel(guild_ID, channel_ID, language_NAME):
    _create_guild(guild_ID)

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO guild_channels (guild_ID, channel_ID, language_NAME)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_ID, channel_ID)
            DO UPDATE SET language_NAME = excluded.language_NAME
        """,
            (guild_ID, channel_ID, language_NAME),
        )
        conn.commit()
    finally:
        cursor.close()


# getters
def get_guild(guild_ID):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT guild_ID FROM guilds WHERE guild_ID = ?", (guild_ID,))
        return cursor.fetchone()
    finally:
        cursor.close()


async def get_channels(guild: discord.Guild):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT channel_ID, language_NAME
            FROM guild_channels
            WHERE guild_ID = ?
            ORDER BY channel_ID
            """,
            (guild.id,),
        )
        rows = cursor.fetchall()

        existing_rows = []

        for channel_id, language_name in rows:
            try:
                # Use the cache first; fetch from Discord if it's not cached
                channel = guild.get_channel(channel_id)
                if channel is None:
                    channel = await guild.fetch_channel(channel_id)

                # Don't treat a channel from another guild as valid
                if channel.guild.id != guild.id:
                    raise discord.NotFound(
                        response=None,
                        message="Channel is not in this guild",
                    )

                existing_rows.append((channel_id, language_name))

            except discord.NotFound:
                cursor.execute(
                    """
                    DELETE FROM guild_channels
                    WHERE guild_ID = ? AND channel_ID = ?
                    """,
                    (guild.id, channel_id),
                )

            except discord.Forbidden:
                # The bot can't verify this channel, so leave its row intact
                existing_rows.append((channel_id, language_name))

            except discord.HTTPException as exc:
                # not evidence that the channel is gone
                existing_rows.append((channel_id, language_name))

                logging.warning(
                    "Could not check channel %s: status=%s, code=%s, text=%s",
                    channel_id,
                    exc.status,
                    exc.code,
                    exc.text,
                )
                existing_rows.append((channel_id, language_name))

        conn.commit()
        return existing_rows

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()


# get all, probably not needed
def get_all_guilds():
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT guild_ID FROM guilds ORDER BY guild_ID")
        return cursor.fetchall()
    finally:
        cursor.close()


def get_all_channels():
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT guild_ID, channel_ID, language_NAME
            FROM guild_channels
            ORDER BY guild_ID, channel_ID
        """)
        return cursor.fetchall()
    finally:
        cursor.close()


setup_db()
