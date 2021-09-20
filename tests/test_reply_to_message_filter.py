#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020
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
import datetime
import pytest
from telegram import Message, Update, Chat, User
from telegram.ext import Filters

from ptbcontrib.reply_to_message_filter import ReplyToMessageFilter


@pytest.fixture(scope='function')
def update():
    return Update(
        0,
        Message(
            0,
            datetime.datetime.utcnow(),
            Chat(0, 'private'),
            from_user=User(0, 'Testuser', False),
            via_bot=User(0, "Testbot", True),
            sender_chat=Chat(0, 'Channel'),
            reply_to_message=Message(
                0,
                datetime.datetime.utcnow(),
                Chat(0, 'private'),
                from_user=User(0, 'Testuser', False),
                via_bot=User(0, "Testbot", True),
                sender_chat=Chat(0, 'Channel'),
            ),
        ),
    )


class TestReplyToMessageFilter:
    def test_basic(self, update):
        update.message.reply_to_message.text = 'test'
        assert ReplyToMessageFilter(Filters.all)(update)
        assert ReplyToMessageFilter(Filters.text)(update)
        update.message.reply_to_message.text = None
        assert not ReplyToMessageFilter(Filters.text)(update)
        update.message.reply_to_message = None
        assert not ReplyToMessageFilter(Filters.all)(update)

    def test_combination(self, update):
        assert not (Filters.text & ~ReplyToMessageFilter(Filters.text))(update)
        update.message.text = 'test'
        update.message.reply_to_message.text = 'text'
        assert not (Filters.text & ~ReplyToMessageFilter(Filters.text))(update)
        update.message.text = None
        update.message.reply_to_message.text = None
        assert not (Filters.text & ~ReplyToMessageFilter(Filters.text))(update)
        update.message.text = 'test'
        assert (Filters.text & ~ReplyToMessageFilter(Filters.text))(update)

    def test_update_filter(self, update):
        assert not ReplyToMessageFilter(Filters.update.channel_post)(update)
        update.channel_post = update.message
        update.message = None
        assert ReplyToMessageFilter(Filters.update.channel_post)(update)

    def test_regex_filter(self, update):
        regex_filter = Filters.regex(r'(\d+)')
        assert not ReplyToMessageFilter(regex_filter)(update)
        update.message.reply_to_message.text = 'foo 123, bar'
        result = ReplyToMessageFilter(regex_filter)(update)
        assert isinstance(result, dict)

        result = ReplyToMessageFilter(Filters.text & regex_filter)(update)
        assert isinstance(result, dict)
        assert (Filters.text & ReplyToMessageFilter(regex_filter))(update) is False
        update.message.text = 'test'
        result = (Filters.text & ReplyToMessageFilter(regex_filter))(update)
        assert isinstance(result, dict)

        update.message.text = 'foo 456, bar'
        result = (regex_filter & ReplyToMessageFilter(regex_filter))(update)
        assert isinstance(result, dict)
        assert len(result['matches']) == 2
