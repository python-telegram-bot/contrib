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
import datetime as dtm
import os
import pickle
from typing import Optional

import pytest
import sys
import time

from copy import deepcopy
from telegram import (
    Message,
    User,
    InlineQuery,
    Update,
    ChatMember,
    Chat,
    TelegramError,
)
from telegram.ext import BasePersistence, CallbackContext, MessageHandler, Filters

from ptbcontrib.roles import (
    Role,
    Roles,
    ChatAdminsRole,
    ChatCreatorRole,
    setup_roles,
    BOT_DATA_KEY,
    RolesHandler,
    RolesBotData,
)


@pytest.fixture(scope='function')
def update():
    return Update(
        0,
        Message(
            0, dtm.datetime.utcnow(), Chat(0, 'private'), from_user=User(0, 'TestUser', False)
        ),
    )


@pytest.fixture(scope='function')
def roles(bot):
    return Roles(bot)


@pytest.fixture(scope='function')
def parent_role():
    return Role(name='parent_role')


@pytest.fixture(scope='function')
def role():
    return Role(name='role')


@pytest.fixture(scope='function')
def chat_admins_role(bot):
    return ChatAdminsRole(bot, 0.05)


@pytest.fixture(scope='function')
def chat_creator_role(bot):
    return ChatCreatorRole(bot)


@pytest.fixture(autouse=True)
def change_directory(tmp_path):
    orig_dir = os.getcwd()
    # Switch to a temporary directory so we don't have to worry about cleaning up files
    # (str() for py<3.6)
    os.chdir(str(tmp_path))
    yield
    # Go back to original directory
    os.chdir(orig_dir)


@pytest.fixture(scope="function")
def base_persistence():
    class OwnPersistence(BasePersistence):
        def get_bot_data(self):
            raise NotImplementedError

        def get_chat_data(self):
            raise NotImplementedError

        def get_user_data(self):
            raise NotImplementedError

        def get_conversations(self, name):
            raise NotImplementedError

        def update_bot_data(self, data):
            raise NotImplementedError

        def update_chat_data(self, chat_id, data):
            raise NotImplementedError

        def update_conversation(self, name, key, new_state):
            raise NotImplementedError

        def update_user_data(self, user_id, data):
            raise NotImplementedError

    return OwnPersistence(store_chat_data=True, store_user_data=True, store_bot_data=True)


class TestRole:
    def test_creation(self, parent_role):
        r = Role(child_roles=[parent_role, parent_role])
        assert r.chat_ids == set()
        assert str(r) == 'Role({})'
        assert r.child_roles == {parent_role}
        assert isinstance(r._admin, Role)
        assert str(r._admin) == f'Role({Role._DEFAULT_ADMIN_NAME})'

        r = Role(1)
        assert r.chat_ids == {1}
        assert str(r) == 'Role({1})'

        r = Role([1, 2])
        assert r.chat_ids == {1, 2}
        assert str(r) == 'Role({1, 2})'

        r = Role([1, 2], name='role')
        assert r.chat_ids == {1, 2}
        assert str(r) == 'Role(role)'

    def test_add_member(self, role):
        assert role.chat_ids == set()
        role.add_member(1)
        assert role.chat_ids == {1}
        role.add_member(2)
        assert role.chat_ids == {1, 2}
        role.add_member(1)
        assert role.chat_ids == {1, 2}

    def test_kick_member(self, role):
        assert role.chat_ids == set()
        role.add_member(1)
        role.add_member(2)
        assert role.chat_ids == {1, 2}
        role.kick_member(1)
        assert role.chat_ids == {2}
        role.kick_member(1)
        assert role.chat_ids == {2}
        role.kick_member(2)
        assert role.chat_ids == set()

    def test_add_remove_child_role(self, role, parent_role):
        assert role.child_roles == set()
        parent2 = Role(chat_ids=456, name='pr2')
        role.add_child_role(parent_role)
        assert role.child_roles == {parent_role}
        role.add_child_role(parent2)
        assert role.child_roles == {parent_role, parent2}

        role.remove_child_role(parent_role)
        assert role.child_roles == {parent2}
        role.remove_child_role(parent2)
        assert role.child_roles == set()

        with pytest.raises(ValueError, match='You must not add a role as its own child!'):
            role.add_child_role(role)

        parent_role.add_child_role(role)
        with pytest.raises(ValueError, match='You must not add a parent role as a child!'):
            role.add_child_role(parent_role)

    def test_equals(self, role, parent_role):
        r = Role(name='test1')
        r2 = Role(name='test2')
        r3 = Role(name='test3', chat_ids=[1, 2])
        r4 = Role(name='test4')
        assert role.equals(parent_role)
        role.add_child_role(r)
        assert not role.equals(parent_role)
        parent_role.add_child_role(r2)
        assert role.equals(parent_role)
        parent_role.add_child_role(r3)
        role.add_child_role(r4)
        assert not role.equals(parent_role)
        role.remove_child_role(r4)
        parent_role.remove_child_role(r3)

        role.add_member(1)
        assert not role.equals(parent_role)
        parent_role.add_member(1)
        assert role.equals(parent_role)
        role.add_member(2)
        assert not role.equals(parent_role)
        parent_role.add_member(2)
        assert role.equals(parent_role)
        role.kick_member(2)
        assert not role.equals(parent_role)
        parent_role.kick_member(2)
        assert role.equals(parent_role)

        r.add_member(1)
        assert not role.equals(parent_role)
        r2.add_member(1)
        assert role.equals(parent_role)

    def test_comparison(self, role, parent_role):
        assert not role <= 1
        assert not role >= 1

        assert not role < parent_role
        assert not parent_role < role
        assert role <= role
        assert role >= role
        assert parent_role <= parent_role
        assert parent_role >= parent_role

        parent_role.add_child_role(role)
        assert role < parent_role
        assert role <= parent_role
        assert parent_role >= role
        assert parent_role > role

        parent_role.remove_child_role(role)
        assert not role < parent_role
        assert not parent_role < role

    def test_hash(self, role, parent_role):
        assert role != parent_role
        assert hash(role) != hash(parent_role)

        assert role == role
        assert hash(role) == hash(role)

        assert parent_role == parent_role
        assert hash(parent_role) == hash(parent_role)

    def test_deepcopy(self, role, parent_role):
        child = Role(name='cr', chat_ids=[1, 2, 3])
        role.add_child_role(child)
        role.add_member(7)
        copied_role = deepcopy(role)

        assert role is not copied_role
        assert role.equals(copied_role)
        assert role.chat_ids is not copied_role.chat_ids
        assert role.chat_ids == copied_role.chat_ids
        (copied_child,) = copied_role.child_roles
        assert child is not copied_child
        assert child.equals(copied_child)

    def test_filter_user(self, update, role, parent_role):
        update.message.chat = None
        assert not role(update)

        role.add_member(0)
        assert role(update)

        update.message.from_user.id = 1
        assert not role(update)

        parent_role.add_child_role(role)
        parent_role.add_member(1)
        assert role(update)

    def test_filter_chat(self, update, role, parent_role):
        update.message.from_user = None
        assert not role(update)

        role.add_member(0)
        assert role(update)

        update.message.chat.id = 1
        assert not role(update)

        parent_role.add_child_role(role)
        parent_role.add_member(1)
        assert role(update)

    def test_filter_merged_roles(self, update, role):
        role.add_member(0)
        r = Role(0)
        assert not (role & (~r))(update)

        r = Role(1)
        assert not (role & r)(update)
        assert (role | r)(update)

    def test_filter_allow_parent(self, update, role, parent_role):
        role.add_member(0)
        parent_role.add_member(1)
        parent_role.add_child_role(role)

        test_role = ~role
        assert not test_role(update)
        update.message.from_user.id = 1
        update.message.chat.id = 1
        assert test_role(update)

    def test_filter_exclude_children(self, update, role, parent_role):
        parent_role.add_child_role(role)
        parent_role.add_member(0)
        role.add_member(1)

        test_role = ~parent_role
        assert not test_role(update)
        update.message.from_user.id = 1
        update.message.chat.id = 1
        assert not test_role(update)
        update.message.from_user.id = 2
        update.message.chat.id = 1
        assert not test_role(update)

    def test_filter_without_user_and_chat(self, update, role):
        role.add_member(0)
        update.message = None
        assert not role(update)
        assert not (~role)(update)

    def test_always_allow_admin(self, update, role):
        role._admin.add_member(0)
        try:
            assert (~Role(0))(update)
            assert (Role(0) & ~Role(0))(update)
            assert (Role(1) & ~Role(0))(update)
            assert (Role(1) & ~Role(2))(update)
            assert (Role(0) | ~Role(0))(update)
            assert (Role(1) | ~Role(0))(update)
            assert (Role(1) | ~Role(2))(update)
        finally:
            role._admin.kick_member(0)

    def test_pickle(self, role, parent_role):
        role.add_member([0, 1, 3])
        parent_role.add_member([4, 5, 6])
        child_role = Role(name='child_role', chat_ids=[7, 8, 9])
        role.add_child_role(child_role)
        parent_role.add_child_role(child_role)

        data = {
            'role': role,
            'parent': parent_role,
            'child': child_role,
        }
        with open('pickle', 'wb') as file:
            pickle.dump(data, file)
        with open('pickle', 'rb') as file:
            data = pickle.load(file)

        assert data['role'].equals(role)
        assert data['parent'].equals(parent_role)
        assert data['child'].equals(child_role)

        (child_1,) = data['role'].child_roles
        (child_2,) = data['parent'].child_roles
        assert child_1 is child_2

        assert data['role'] in Role._admin.child_roles
        assert data['parent'] in Role._admin.child_roles
        assert data['child'] in Role._admin.child_roles
        assert data['child'] <= data['role']
        assert data['child'] <= data['parent']
        assert not data['role'] <= data['parent']


class TestChatAdminsRole:
    def test_creation(self, bot):
        admins = ChatAdminsRole(bot, timeout=7)
        assert admins.timeout == 7
        assert admins.bot is bot

    def test_simple(self, chat_admins_role, update, monkeypatch):
        def admins(*args, **kwargs):
            return [
                ChatMember(User(0, 'TestUser0', False), 'administrator'),
                ChatMember(User(1, 'TestUser1', False), 'creator'),
            ]

        monkeypatch.setattr(chat_admins_role.bot, 'get_chat_administrators', admins)

        update.message.from_user.id = 2
        update.message.chat.type = Chat.GROUP
        assert not chat_admins_role(update)
        update.message.from_user.id = 1
        assert chat_admins_role(update)
        update.message.from_user.id = 0
        assert chat_admins_role(update)

    def test_private_chat(self, chat_admins_role, update):
        update.message.from_user.id = 2
        update.message.chat.id = 2

        assert chat_admins_role(update)

    def test_no_chat(self, chat_admins_role, update):
        update.message = None
        update.inline_query = InlineQuery(1, User(0, 'TestUser', False), 'query', 0)

        assert not chat_admins_role(update)

    def test_no_user(self, chat_admins_role, update):
        update.message = None
        update.channel_post = Message(1, dtm.datetime.utcnow(), Chat(0, 'channel'))

        assert not chat_admins_role(update)

    def test_always_allow_admins(self, chat_admins_role, update, monkeypatch):
        def admins(*args, **kwargs):
            return [
                ChatMember(User(0, 'TestUser0', False), 'administrator'),
                ChatMember(User(1, 'TestUser1', False), 'creator'),
            ]

        monkeypatch.setattr(chat_admins_role.bot, 'get_chat_administrators', admins)
        update.message.chat.type = Chat.GROUP
        update.message.from_user.id = 2
        try:
            assert not chat_admins_role(update)
            chat_admins_role._admin.add_member(2)
            assert chat_admins_role(update)
        finally:
            chat_admins_role._admin.kick_member(2)

    def test_caching(self, chat_admins_role, update, monkeypatch):
        def admins(*args, **kwargs):
            return [
                ChatMember(User(0, 'TestUser0', False), 'administrator'),
                ChatMember(User(1, 'TestUser1', False), 'creator'),
            ]

        monkeypatch.setattr(chat_admins_role.bot, 'get_chat_administrators', admins)

        update.message.from_user.id = 2
        update.message.chat.type = Chat.GROUP
        assert not chat_admins_role(update)
        assert isinstance(chat_admins_role.cache[0], tuple)
        assert pytest.approx(chat_admins_role.cache[0][0]) == time.time()
        assert chat_admins_role.cache[0][1] == [0, 1]

        def admins(*args, **kwargs):
            raise ValueError('This method should not be called!')

        monkeypatch.setattr(chat_admins_role.bot, 'get_chat_administrators', admins)

        update.message.from_user.id = 1
        assert chat_admins_role(update)

        time.sleep(0.05)

        def admins(*args, **kwargs):
            return [ChatMember(User(2, 'TestUser0', False), 'administrator')]

        monkeypatch.setattr(chat_admins_role.bot, 'get_chat_administrators', admins)

        update.message.from_user.id = 2
        assert chat_admins_role(update)
        assert isinstance(chat_admins_role.cache[0], tuple)
        assert pytest.approx(chat_admins_role.cache[0][0]) == time.time()
        assert chat_admins_role.cache[0][1] == [2]

    def test_no_invert(self, chat_admins_role):
        with pytest.raises(RuntimeError, match='can not be inverted'):
            ~chat_admins_role


class TestChatCreatorRole:
    def test_creation(self, bot):
        creator = ChatCreatorRole(bot)
        assert creator.bot is bot

    def test_simple(self, chat_creator_role, monkeypatch, update):
        def member(*args, **kwargs):
            if args[1] == 0:
                return ChatMember(User(0, 'TestUser0', False), 'administrator')
            if args[1] == 1:
                return ChatMember(User(1, 'TestUser1', False), 'creator')
            raise TelegramError('User is not a member')

        monkeypatch.setattr(chat_creator_role.bot, 'get_chat_member', member)

        update.message.from_user.id = 0
        update.message.chat.id = -1
        update.message.chat.type = Chat.GROUP
        assert not chat_creator_role(update)
        update.message.from_user.id = 1
        update.message.chat.id = 1
        assert chat_creator_role(update)
        update.message.from_user.id = 2
        update.message.chat.id = -2
        assert not chat_creator_role(update)

    def test_no_chat(self, chat_creator_role, update):
        update.message = None
        update.inline_query = InlineQuery(1, User(0, 'TestUser', False), 'query', 0)

        assert not chat_creator_role(update)

    def test_no_user(self, chat_creator_role, update):
        update.message = None
        update.channel_post = Message(1, dtm.datetime.utcnow(), Chat(0, 'channel'))

        assert not chat_creator_role(update)

    def test_private_chat(self, chat_creator_role, update):
        update.message.from_user.id = 2
        update.message.chat.id = 2

        assert chat_creator_role(update)

    def test_always_allow_admins(self, chat_creator_role, update, monkeypatch):
        def admins(*args, **kwargs):
            return [
                ChatMember(User(0, 'TestUser0', False), 'administrator'),
                ChatMember(User(1, 'TestUser1', False), 'creator'),
            ]

        monkeypatch.setattr(chat_creator_role.bot, 'get_chat_administrators', admins)
        update.message.chat.type = Chat.GROUP
        update.message.from_user.id = 2
        try:
            assert not chat_creator_role(update)
            chat_creator_role._admin.add_member(2)
            assert chat_creator_role(update)
        finally:
            chat_creator_role._admin.kick_member(2)

    def test_caching(self, chat_creator_role, monkeypatch, update):
        def member(*args, **kwargs):
            if args[1] == 0:
                return ChatMember(User(0, 'TestUser0', False), 'administrator')
            if args[1] == 1:
                return ChatMember(User(1, 'TestUser1', False), 'creator')
            raise TelegramError('User is not a member')

        monkeypatch.setattr(chat_creator_role.bot, 'get_chat_member', member)

        update.message.from_user.id = 1
        update.message.chat.type = Chat.GROUP
        assert chat_creator_role(update)
        assert chat_creator_role.cache == {0: 1}

        def member(*args, **kwargs):
            raise ValueError('This method should not be called!')

        monkeypatch.setattr(chat_creator_role.bot, 'get_chat_member', member)

        update.message.from_user.id = 1
        assert chat_creator_role(update)

        update.message.from_user.id = 2
        assert not chat_creator_role(update)

    def test_no_invert(self, chat_creator_role):
        with pytest.raises(RuntimeError, match='can not be inverted'):
            ~chat_creator_role


class TestRoles:
    def test_creation(self, bot):
        roles = Roles(bot)
        assert isinstance(roles.admins, Role)
        assert isinstance(roles.chat_admins, Role)
        assert roles.chat_admins.bot is bot
        assert isinstance(roles.chat_creator, Role)
        assert roles.chat_creator.bot is bot
        assert roles.bot is bot

    def test_set_bot(self, bot):
        roles = Roles(1)
        assert roles.bot == 1
        roles.set_bot(2)
        assert roles.bot == 2
        roles.set_bot(bot)
        assert roles.bot is bot
        with pytest.raises(ValueError, match='already set'):
            roles.set_bot(bot)

    def test_add_kick_admin(self, roles):
        assert roles.admins.chat_ids == set()
        roles.add_admin(1)
        assert roles.admins.chat_ids == {1}
        roles.add_admin(2)
        assert roles.admins.chat_ids == {1, 2}
        roles.kick_admin(1)
        assert roles.admins.chat_ids == {2}
        roles.kick_admin(2)
        assert roles.admins.chat_ids == set()

    @pytest.mark.skipif(sys.version_info < (3, 6), reason="dicts are not ordered in py<=3.5")
    def test_dict_functionality(self, roles):
        roles.add_role('role0', 0)
        roles.add_role('role1', 1)
        roles.add_role('role2', 2)

        assert 'role2' in roles
        assert 'role3' not in roles

        a = {name for name in roles}
        assert a == {f'role{k}' for k in range(3)}

        b = {name: role.chat_ids for name, role in roles.items()}
        assert b == {f'role{k}': {k} for k in range(3)}

        c = [name for name in roles.keys()]
        assert c == [f'role{k}' for k in range(3)]

        d = [r.chat_ids for r in roles.values()]
        assert d == [{k} for k in range(3)]

    def test_add_remove_role(self, roles, parent_role):
        roles.add_role('role', child_roles=[parent_role])
        role = roles['role']
        assert role.chat_ids == set()
        assert role.child_roles == {parent_role}
        assert str(role) == 'Role(role)'
        assert role <= roles.admins
        assert role not in Role._admin.child_roles

        with pytest.raises(ValueError, match='Role name is already taken.'):
            roles.add_role('role')

        roles.remove_role('role')
        assert not roles.get('role', None)
        assert not role <= roles.admins
        assert role in Role._admin.child_roles

    def test_handler_admins(self, roles, update):
        roles.add_role('role', 0)
        roles.add_admin(1)
        assert roles['role'](update)
        update.message.from_user.id = 1
        update.message.chat.id = 1
        assert roles['role'](update)
        roles.kick_admin(1)
        assert not roles['role'](update)

    def test_handler_admins_merged(self, roles, update):
        roles.add_role('role_1', 0)
        roles.add_role('role_2', 1)
        roles.add_admin(2)
        test_role = roles['role_1'] & ~roles['role_2']
        assert test_role(update)
        update.message.from_user.id = 2
        update.message.chat.id = 2
        assert test_role(update)
        roles.kick_admin(2)
        assert not test_role(update)

    @pytest.mark.filterwarnings('ignore:BasePersistence')
    def test_pickle(self, roles, bot, base_persistence):
        base_persistence.set_bot(bot)

        roles.add_role('role', [1, 2, 3])
        roles.add_role('parent', [4, 5, 6])
        roles.add_role('child', [7, 8, 9])
        roles['role'].add_child_role(roles['child'])
        roles['parent'].add_child_role(roles['child'])

        roles.admins.add_member(10)
        roles.chat_admins.cache[42] = 24
        roles.chat_creator.cache[43] = 34

        with open('pickle', 'wb') as file:
            data = base_persistence.replace_bot(roles)
            pickle.dump(data, file)
        with open('pickle', 'rb') as file:
            data = pickle.load(file)
            copied_roles = base_persistence.insert_bot(data)

        assert copied_roles['role'].equals(roles['role'])
        assert copied_roles['parent'].equals(roles['parent'])
        assert copied_roles['child'].equals(roles['child'])

        (child_1,) = roles['role'].child_roles
        (child_2,) = roles['parent'].child_roles
        assert child_1 is child_2

        assert copied_roles['role'] <= copied_roles.admins
        assert copied_roles['role'] in copied_roles.admins.child_roles
        assert copied_roles['parent'] in copied_roles.admins.child_roles
        assert copied_roles['child'] in copied_roles.admins.child_roles
        assert copied_roles['child'] <= copied_roles['role']
        assert copied_roles['child'] <= copied_roles['parent']
        assert not copied_roles['role'] <= copied_roles['parent']

        assert copied_roles.admins.equals(roles.admins)
        assert copied_roles.chat_admins.cache[42] == 24
        assert copied_roles.chat_creator.cache[43] == 34
        assert copied_roles.chat_admins.bot is roles.chat_admins.bot
        assert copied_roles.chat_creator.bot is roles.chat_creator.bot


@pytest.fixture(scope='function', autouse=True)
def clear_bot_data(dp):
    yield
    dp.bot_data = dict()


class RolesData(RolesBotData):
    def __init__(self):
        self.roles = None

    def get_roles(self) -> Optional[Roles]:
        return self.roles

    def set_roles(self, roles: Roles) -> None:
        self.roles = roles


class TestRolesHandler:
    @pytest.mark.parametrize('roles_bot_data', [True, False])
    def test_setup_roles(self, cdp, roles_bot_data):
        if roles_bot_data:
            cdp.bot_data = RolesData()
        roles = setup_roles(cdp)
        assert isinstance(roles, Roles)
        if not roles_bot_data:
            assert cdp.bot_data[BOT_DATA_KEY] is roles
        else:
            assert cdp.bot_data.get_roles() is roles
        # We test twice to make sure everything nothing goes wrong when roles is already there
        roles = setup_roles(cdp)
        assert isinstance(roles, Roles)
        if not roles_bot_data:
            assert cdp.bot_data[BOT_DATA_KEY] is roles
        else:
            assert cdp.bot_data.get_roles() is roles

    def test_setup_roles_invalid_bot_data_type(self, cdp):
        cdp.bot_data = 17
        with pytest.raises(TypeError, match='dict or implement RolesBotData'):
            setup_roles(cdp)

    def test_collect_additional_context_invalid_bot_data(self, cdp, update):
        cdp.bot_data = 'yet another deathstar'

        def callback(_, __):
            pass

        handler = MessageHandler(Filters.all, callback=callback)
        roles_handler = RolesHandler(handler, roles=None)
        context = CallbackContext.from_update(update, cdp)
        with pytest.raises(TypeError, match='dict or implement RolesBotData'):
            roles_handler.collect_additional_context(context, cdp, update, True)

    @pytest.mark.parametrize('roles_bot_data', [True, False])
    def test_callback_and_context(self, cdp, update, roles_bot_data):
        if roles_bot_data:
            cdp.bot_data = RolesData()
        self.roles = setup_roles(cdp)
        self.roles.admins.add_member(42)
        self.roles.add_role(name='role', chat_ids=[1])
        self.test_flag = False

        def callback(_, context: CallbackContext):
            self.test_flag = context.roles is self.roles

        handler = MessageHandler(Filters.all, callback=callback)
        roles_handler = RolesHandler(handler, roles=self.roles['role'])

        assert not roles_handler.check_update(update)
        update.message.from_user.id = 1
        assert roles_handler.check_update(update)
        update.message.from_user.id = 42
        assert roles_handler.check_update(update)

        cdp.add_handler(roles_handler)
        cdp.process_update(update)
        assert self.test_flag

    @pytest.mark.parametrize('roles_bot_data', [True, False])
    def test_handler_error_message(self, cdp, update, roles_bot_data):
        if roles_bot_data:
            cdp.bot_data = RolesData()
        handler = MessageHandler(Filters.all, callback=lambda u, c: 1)
        roles_handler = RolesHandler(handler, roles=Role(0))
        cdp.add_handler(roles_handler)
        self.test_flag = False

        def error_handler(_, context: CallbackContext):
            self.test_flag = 'You must set a Roles instance' in str(context.error)

        cdp.add_error_handler(error_handler)
        cdp.process_update(update)

        assert self.test_flag
