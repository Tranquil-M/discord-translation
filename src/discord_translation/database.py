import sqlite3
from pathlib import Path

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
def create_guild(guild_ID):
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
    create_guild(guild_ID)

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


def get_all_guilds():
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT guild_ID FROM guilds ORDER BY guild_ID")
        return cursor.fetchall()
    finally:
        cursor.close()


def get_channels(guild_ID):
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT channel_ID, language_NAME
            FROM guild_channels
            WHERE guild_ID = ?
            ORDER BY channel_ID
        """,
            (guild_ID,),
        )
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
