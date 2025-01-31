#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2025
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

"""This module contains extended keyboard classes with extra functionality for PTB keyboards."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from telegram import InlineKeyboardButton

from ptbcontrib.extended_keyboards import ExtendedInlineKeyboardMarkup

if TYPE_CHECKING:
    pass

btn_1 = InlineKeyboardButton(
    text="1",
    callback_data="a1",
)
btn_2 = InlineKeyboardButton(
    text="2",
    callback_data="b2",
)
btn_3 = InlineKeyboardButton(
    text="3",
    callback_data="c3",
)
btn_4 = InlineKeyboardButton(
    text="4",
    callback_data="d4",
)
btn_5 = InlineKeyboardButton(
    text="5",
    callback_data="e5",
)

row_1 = (
    btn_1,
    btn_2,
)
row_2 = (
    btn_3,
    btn_4,
)
row_3 = (btn_5,)

inline_keyboard = (
    row_1,
    row_2,
    row_3,
)
extended_keyboard = ExtendedInlineKeyboardMarkup(
    inline_keyboard=inline_keyboard,
)


class TestExtendedInlineKeyboardMarkup:
    @staticmethod
    def test_to_list():
        expected = [
            [
                btn_1,
                btn_2,
            ],
            [
                btn_3,
                btn_4,
            ],
            [
                btn_5,
            ],
        ]
        assert extended_keyboard.to_list() == expected

    class TestFindBtnByCbk:
        """test_find_btn_by_cbk"""

        @staticmethod
        def test_strict():
            assert extended_keyboard.find_btn_by_cbk(
                cbk="a1",
                strict=True,
            ) == (
                btn_1,
                0,
                0,
            )
            assert (
                extended_keyboard.find_btn_by_cbk(
                    cbk="a",
                    strict=True,
                )
                is None
            )
            assert (
                extended_keyboard.find_btn_by_cbk(
                    cbk="Not found a Not found",
                    strict=True,
                )
                is None
            )

        @staticmethod
        def test_not_strict():
            assert extended_keyboard.find_btn_by_cbk(
                cbk="a",
                strict=False,
            ) == (
                btn_1,
                0,
                0,
            )
            assert extended_keyboard.find_btn_by_cbk(
                cbk="b",
                strict=False,
            ) == (
                btn_2,
                0,
                1,
            )
            assert extended_keyboard.find_btn_by_cbk(
                cbk="c",
                strict=False,
            ) == (
                btn_3,
                1,
                0,
            )
            assert extended_keyboard.find_btn_by_cbk(
                cbk="d",
                strict=False,
            ) == (
                btn_4,
                1,
                1,
            )
            assert extended_keyboard.find_btn_by_cbk(
                cbk="e",
                strict=False,
            ) == (
                btn_5,
                2,
                0,
            )
            assert (
                extended_keyboard.find_btn_by_cbk(
                    cbk="Not found a Not found",
                    strict=False,
                )
                is None
            )

    @staticmethod
    def test_get_keyboard_buttons():
        """ikm.inline_keyboard[0][0], 0, 0 - found btn, row and column indexes"""
        expected = [
            btn_1,
            btn_2,
            btn_3,
            btn_4,
            btn_5,
        ]
        assert extended_keyboard.get_buttons() == expected

    class TestSplit:
        """test_split"""

        @staticmethod
        def test_single_button_in_row():
            expected = [
                [
                    btn_1,
                ],
                [
                    btn_2,
                ],
                [
                    btn_3,
                ],
                [
                    btn_4,
                ],
                [
                    btn_5,
                ],
            ]
            result = extended_keyboard.split(
                buttons_in_row=1,
            )
            assert result == expected

        @staticmethod
        def test_equal_buttons_in_row():
            expected = [
                [
                    btn_1,
                    btn_2,
                ],
                [
                    btn_3,
                    btn_4,
                ],
                [
                    btn_5,
                ],
            ]
            result = extended_keyboard.split(
                buttons_in_row=2,
            )
            assert result == expected

        @staticmethod
        def test_unequal_buttons_in_row():
            expected = [
                [
                    btn_1,
                    btn_2,
                    btn_3,
                ],
                [
                    btn_4,
                    btn_5,
                ],
            ]
            result = extended_keyboard.split(
                buttons_in_row=3,
            )
            assert result == expected

        @staticmethod
        def test_not_enough_buttons_in_row():
            expected = [extended_keyboard.get_buttons()]
            result = extended_keyboard.split(
                buttons_in_row=100,
            )
            assert result == expected

        @staticmethod
        def test_empty_rows_disallowed():
            with pytest.raises(
                expected_exception=extended_keyboard.Exceptions.EmptyRowsDisallowed,
            ):
                extended_keyboard.split(
                    buttons_in_row=100,
                    empty_rows_allowed=False,
                )

        @staticmethod
        def test_strict():
            with pytest.raises(
                expected_exception=extended_keyboard.Exceptions.NotEnoughButtons,
            ):
                extended_keyboard.split(
                    buttons_in_row=100,
                    strict=True,
                )
