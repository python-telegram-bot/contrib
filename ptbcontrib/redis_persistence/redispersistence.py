#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2021
# The ptbcontrib developers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
"""This module implements RedisPersistence class."""

from typing import Any
import redis
from telegram.ext import DictPersistence


class RedisPersistence(DictPersistence):
    """
    Bot's persistence between restarts implemented via a Redis database.
    Note: in the database, all keys created by this class are prefixed with 'ptb:'.
    Args:
        url: (:obj:`str`, optional) - URL of the database.
            Either this argument or 'db' must be specified.
        db: (:obj:`redis.Redis`, optional) - An existing connection to the Redis database.
            Either this argument or 'url' must be specified.
        store_user_data: (:obj:`bool`, optional) - Whether user_data should be saved by this
            persistence class. Defaults to True.
        store_chat_data: (:obj:`bool`, optional) - Whether chat_data should be saved by this
            persistence class. Defaults to True.
        store_bot_data: (:obj:`bool`, optional) - Whether bot_data should be saved by this
            persistence class. Defaults to True.
        store_callback_data: (:obj:`bool`, optional) - Whether callback_data should be saved by
            this persistence class. Defaults to False.

    Attributes:
        db: :obj:`redis.Redis` - Connection to the Redis database.
        store_user_data: :obj:`bool` - Whether user_data should be saved by this
            persistence class.
        store_chat_data: :obj:`bool` - Whether chat_data should be saved by this
            persistence class.
        store_bot_data: :obj:`bool` - Whether bot_data should be saved by this
            persistence class.
        store_callback_data: :obj:`bool` - Whether callback_data should be saved by this
            persistence class.
    """

    USER_DATA = 'ptb:user-data'
    CHAT_DATA = 'ptb:chat-data'
    BOT_DATA = 'ptb:bot-data'
    CALLBACK_DATA = 'ptb:callback-data'
    CONVERSATIONS = 'ptb:conversations'

    def __init__(self, url: str = None, db: redis.Redis = None, **kwargs: Any) -> None:

        if url is not None:
            self.conn = redis.Redis.from_url(url)
        elif db is not None:
            self.conn = db
        else:
            raise ValueError("Either 'url' or 'db' argument must be specified")

        super().__init__(
            **kwargs,
            user_data_json=self.conn.get(self.USER_DATA).decode()
            if self.conn.exists(self.USER_DATA)
            else '',
            chat_data_json=self.conn.get(self.CHAT_DATA).decode()
            if self.conn.exists(self.CHAT_DATA)
            else '',
            bot_data_json=self.conn.get(self.BOT_DATA).decode()
            if self.conn.exists(self.BOT_DATA)
            else '',
            callback_data_json=self.conn.get(self.CALLBACK_DATA).decode()
            if self.conn.exists(self.CALLBACK_DATA)
            else '',
            conversations_json=self.conn.get(self.CONVERSATIONS).decode()
            if self.conn.exists(self.CONVERSATIONS)
            else '',
        )

    def flush(self) -> None:
        """Will be called by :class:`telegram.ext.Updater` upon receiving a stop signal. Gives the
        persistence a chance to finish up saving or close a database connection gracefully.
        """
        if self.store_bot_data:
            self.conn.set(self.BOT_DATA, self.bot_data_json.encode())
        if self.store_chat_data:
            self.conn.set(self.CHAT_DATA, self.chat_data_json.encode())
        if self.store_user_data:
            self.conn.set(self.USER_DATA, self.user_data_json.encode())
        if self.store_callback_data:
            self.conn.set(self.CALLBACK_DATA, self.callback_data_json.encode())
        if self._conversations_json or self._conversations:
            self.conn.set(self.CONVERSATIONS, self.conversations_json.encode())
