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
"""This module contains classes and methods for granular, hierarchical user access management."""

from .roles import Role, Roles, ChatAdminsRole, ChatCreatorRole, InvertedRole
from .roleshandler import RolesHandler, setup_roles, BOT_DATA_KEY

__all__ = [
    'Roles',
    'Role',
    'ChatCreatorRole',
    'ChatAdminsRole',
    'InvertedRole',
    'RolesHandler',
    'setup_roles',
    'BOT_DATA_KEY',
]
