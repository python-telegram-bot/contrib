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
import pytest
from ptbcontrib.redis_persistence import RedisPersistence
import telegram


class FakeRedis(dict):
    def set(self, key, value):
        if type(value) != bytes:
            raise TypeError("value type must be 'bytes'")
        self[key] = value

    def exists(self, key):
        return int(key in self.keys())


class TestRedisPersistence:

    fake_db = FakeRedis()
    TEST_DATA = {
        RedisPersistence.BOT_DATA: b'{"msg":"hopefully this works"}',
        RedisPersistence.CHAT_DATA: b'{"56565":{}}',
        RedisPersistence.USER_DATA: b'{"1":{}}',
    }

    def test_flushing_data(self, bot):
        self.updater = telegram.ext.Updater(bot=bot, persistence=RedisPersistence(db=self.fake_db))

        def write_data(update, context):
            context.bot_data['msg'] = 'hopefully this works'

        self.updater.dispatcher.add_handler(telegram.ext.MessageHandler(None, write_data))
        self.updater.dispatcher.process_update(
            telegram.Update(
                12345,
                message=telegram.Message(
                    19876,
                    None,
                    telegram.Chat(56565, 'test_obj'),
                    from_user=telegram.User(1, '', False),
                    text='whatever',
                ),
            )
        )
        self.updater.persistence.flush()

        assert dict(self.updater.persistence.db) == self.TEST_DATA

    def test_invalid_arguments_exception(self):
        with pytest.raises(ValueError):
            RedisPersistence()
