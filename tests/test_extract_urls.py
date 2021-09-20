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
from telegram import Message, MessageEntity
from ptbcontrib import extract_urls


class TestExtractURLs:
    def test_extract_urls_entities(self):
        test_entities = [
            {'length': 6, 'offset': 0, 'type': 'text_link', 'url': 'http://github.com'},
            {'length': 17, 'offset': 23, 'type': 'url'},
            {'length': 14, 'offset': 42, 'type': 'text_link', 'url': 'http://google.com'},
        ]
        test_text = 'Github can be found at http://github.com. Google is here.'
        test_message = Message(
            message_id=1,
            from_user=None,
            date=None,
            chat=None,
            text=test_text,
            entities=[MessageEntity(**e) for e in test_entities],
        )
        results = extract_urls.extract_urls(test_message)

        assert len(results) == 2
        assert test_entities[0]['url'] == results[0]
        assert test_entities[2]['url'] == results[1]

    def test_extract_urls_caption(self):
        test_entities = [
            {'length': 6, 'offset': 0, 'type': 'text_link', 'url': 'http://github.com'},
            {'length': 17, 'offset': 23, 'type': 'url'},
            {'length': 14, 'offset': 42, 'type': 'text_link', 'url': 'http://google.com'},
        ]
        caption = 'Github can be found at http://github.com. Google is here.'
        test_message = Message(
            message_id=1,
            from_user=None,
            date=None,
            chat=None,
            caption=caption,
            caption_entities=[MessageEntity(**e) for e in test_entities],
        )
        results = extract_urls.extract_urls(test_message)

        assert len(results) == 2
        assert test_entities[0]['url'] == results[0]
        assert test_entities[2]['url'] == results[1]

    def test_extract_urls_order(self):
        test_entities = [
            {'length': 6, 'offset': 0, 'type': 'text_link', 'url': 'http://github.com'},
            {'length': 17, 'offset': 27, 'type': 'text_link', 'url': 'http://google.com'},
            {'length': 17, 'offset': 55, 'type': 'url'},
        ]
        test_text = 'Github can not be found at http://google.com. It is at http://github.com.'
        test_message = Message(
            message_id=1,
            from_user=None,
            date=None,
            chat=None,
            text=test_text,
            entities=[MessageEntity(**e) for e in test_entities],
        )
        results = extract_urls.extract_urls(test_message)

        assert len(results) == 2
        assert test_entities[0]['url'] == results[0]
        assert test_entities[1]['url'] == results[1]

    def test_extract_message_links(self):
        test_entities = [
            {
                'length': 17,
                'offset': 0,
                'type': 'url',
            },
            {
                'length': 11,
                'offset': 18,
                'type': 'text_link',
                'url': 'https://t.me/group_name/123456',
            },
            {'length': 12, 'offset': 30, 'type': 'text_link', 'url': 't.me/c/1173342352/256'},
            {
                'length': 11,
                'offset': 43,
                'type': 'text_link',
                'url': 'https://t.me/joinchat/BHFkvxrbaIpgGsEJnO_pew',
            },
            {
                'length': 10,
                'offset': 55,
                'type': 'text_link',
                'url': 'https://t.me/pythontelegrambotgroup',
            },
        ]
        test_text = 'https://google.de public_link private_link invite_link group_link'
        test_message = Message(
            message_id=1,
            from_user=None,
            date=None,
            chat=None,
            text=test_text,
            entities=[MessageEntity(**e) for e in test_entities],
        )

        results = extract_urls.extract_message_links(test_message)
        assert len(results) == 2
        assert results[0] == test_entities[1]['url']
        assert results[1] == test_entities[2]['url']

        results = extract_urls.extract_message_links(test_message, private_only=True)
        assert len(results) == 1
        assert results[0] == test_entities[2]['url']

        results = extract_urls.extract_message_links(test_message, public_only=True)
        assert len(results) == 1
        assert results[0] == test_entities[1]['url']

    def test_extract_message_links_value_error(self):
        with pytest.raises(ValueError):
            extract_urls.extract_message_links(None, public_only=True, private_only=True)
