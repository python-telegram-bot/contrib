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
"""This module contains the class Role, which allows to restrict access to handlers."""
import time
from collections.abc import Mapping
from threading import Lock, Event
from typing import (
    ClassVar,
    Union,
    List,
    Set,
    Tuple,
    FrozenSet,
    Dict,
    Iterator,
    NoReturn,
    Any,
)

from telegram import ChatMember, TelegramError, Bot, Chat, Update
from telegram.ext import UpdateFilter

_REPLACED_LOCK: str = 'ptbcontrib_roles_replaced_lock'


class Role(UpdateFilter):
    """This class represents a security level used by :class:`telegram.ext.Roles`. Roles have a
    hierarchy, i.e. a role can do everthing, its child roles can do. To compare two roles you may
    use the following syntax::

        role_1 < role_2
        role 2 >= role_3

    ``role_1 < role_2`` will be true, if ``role_2`` is a parent of ``role_1`` or a parent of one
    of ``role_1`` s parents and similarly for ``role_1 < role_2``.
    ``role_2 >= role_3`` will be true, if ``role_3`` is ``role_2`` or ``role_2 > role_3`` and
    similarly for ``role_2 <= role_3``.

    Note:
        * If two roles are not related, i.e. neither is a (indirect) parent of the other, comparing
         the roles will always yield ``False``.
        * Updates that have neither effective chat nor effective user will not be allowed.

    Warning:
        ``role_1 == role_2`` does not test for the hierarchical order of the roles, but in fact if
        both roles are the same object. To test for equality in terms of hierarchical order, i.e.
        if :attr:`child_roles` and :attr:`chat_ids` coincide, use :attr:`equals`.

    Roles can be combined using bitwise operators:

    And:

        >>> (Role(name='group_1') & Role(name='user_2'))

    Grants access only for ``user_2`` within the chat ``group_1``.

    Or:

        >>> (Role(name='group_1') | Role(name='user_2'))

    Grants access for ``user_2`` and the whole chat ``group_1``.

    Not:

        >>> ~ Role(name='user_1', child_roles=Role(name='user_2'))

    Restricts access for ``user_1`` and ``user_2``.

    Note:
        Negated roles do `not` exclude their parent roles.

    Also works with more than two roles:

        >>> (Role(name='group_1') & (Role(name='user_2') | Role(name='user_3')))
        >>> Role(name='group_1') & (~ Role(name='user_2'))

    Note:
        Roles use the same short circuiting logic that pythons `and`, `or` and `not`.
        This means that for example:

            >>> Role(chat_ids=123) | Role(chat_ids=456)

        With an update from user ``123``, will only ever evaluate the first role.

    Warning:
        :attr:`chat_ids` will give a *copy* of the saved chat ids as :class:`frozenset`. This
        is to ensure thread safety. To add/remove a chat, you should use :meth:`add_chat_ids` and
        :meth:`remove_chat_ids`. Only update the entire set by ``filter.chat_ids = new_set``, if
        you are entirely sure that it is not causing race conditions, as this will complete replace
        the current set of allowed chats.

    Attributes:
        chat_ids (set(:obj:`int`)): The ids of the users/chats of this role. Updates
            will only be parsed, if the id of :attr:`telegram.Update.effective_user` or
            :attr:`telegram.Update.effective_chat` respectiveley is listed here. May be empty.

    Args:
        chat_ids (:obj:`int` | iterable(:obj:`int`), optional): The ids of the users/chats of this
            role. Updates will only be parsed, if the id of :attr:`telegram.Update.effective_user`
            or :attr:`telegram.Update.effective_chat` respectiveley is listed here.
        child_roles (:class:`telegram.ext.Role` | set(:class:`telegram.ext.Role`)), optional):
            Child roles of this role.
        name (:obj:`str`, optional): A name for this role.
    """

    _DEFAULT_ADMIN_NAME: ClassVar[str] = 'ptbcontrib_roles_default_admin'
    _admin_lock = Lock()
    _admin_event = Event()
    _admin: ClassVar['Role'] = None  # type: ignore[assignment]

    def __init__(
        self,
        chat_ids: Union[int, List[int], Tuple[int, ...]] = None,
        child_roles: Union['Role', List['Role'], Tuple['Role', ...]] = None,
        name: str = None,
    ) -> None:
        self._name = name
        self._inverted = False
        self.__lock = Lock()

        self._chat_ids = self._parse_chat_id(chat_ids)
        self._child_roles: Set['Role'] = set()
        self._set_child_roles(child_roles)

        # We need the if clause for the init of _admin
        if name != self._DEFAULT_ADMIN_NAME:
            self.__init_admin()
            self._admin_event.wait()
            self._admin.add_child_role(self)

    @staticmethod
    def _parse_chat_id(chat_id: Union[int, List[int], Tuple[int, ...], None]) -> Set[int]:
        if chat_id is None:
            return set()
        if isinstance(chat_id, int):
            return {chat_id}
        return set(chat_id)

    @staticmethod
    def __init_admin() -> None:
        with Role._admin_lock:
            if Role._admin is None:
                Role._admin = Role(name=Role._DEFAULT_ADMIN_NAME)
                Role._admin_event.set()

    def _set_custom_admin(self, new_admin: 'Role') -> None:
        with self._admin_lock:
            self._admin.remove_child_role(self)
        new_admin.add_child_role(self)

    @staticmethod
    def _parse_child_role(
        child_role: Union['Role', List['Role'], Tuple['Role', ...], None]
    ) -> Set['Role']:
        if child_role is None:
            return set()
        if isinstance(child_role, Role):
            return {child_role}
        return set(child_role)

    def _set_child_roles(
        self, child_role: Union['Role', List['Role'], Tuple['Role', ...], None]
    ) -> None:
        with self.__lock:
            self._child_roles = self._parse_child_role(child_role)

    @property
    def chat_ids(self) -> FrozenSet[int]:
        """Chat IDs of this role as frozenset (to ensure thread safety)."""
        with self.__lock:
            return frozenset(self._chat_ids)

    @property
    def child_roles(self) -> FrozenSet['Role']:
        """Child roles of this role. This role can do anything, its child roles can do.
        May be empty.

        Returns:
            Set(:class:`telegram.ext.Role`):
        """
        with self.__lock:
            return frozenset(self._child_roles)

    def __invert__(self) -> 'InvertedRole':
        return InvertedRole(self)

    def filter(  # pylint: disable=W0221
        self,
        update: Update,
        target: 'Role' = None,
        inverted: bool = False,
    ) -> bool:
        # Always allow admins
        if self is not self._admin and self._admin.filter(update):
            return True

        user = update.effective_user
        chat = update.effective_chat

        # If the update has neither effective chat nor user, we don't handle it
        if not (user or chat):
            return False

        # First check if the user/chat is in the current roles allowed chats
        if user and user.id in self.chat_ids:
            return not inverted
        if chat and chat.id in self.chat_ids:
            return not inverted

        if inverted:
            # If this is an inverted role (i.e. ~role) and we arrived here, the user is
            # either
            # ... in a child role of this. In this case it must be excluded.
            # ... not in a child role of this and must *not* be excluded. In particular, we
            # dont want to exclude the parents (see below).
            return not any(child.filter(update, target=target) for child in self.child_roles)

        # If we have no result here, we need to check the roles tree in order to check if
        # a parent role allows us to handle the update
        if target:
            root = self
        else:
            # The initial call will start looking from the admin parent
            root = self._admin
            target = self
        # We check all children that are parents of the target role
        return any(
            child.filter(update, target=target) for child in root.child_roles if target <= child
        )

    def add_member(self, chat_id: Union[int, List[int], Tuple[int, ...]]) -> None:
        """
        Add one or more chat(s)/user(s) to the allowed chat/user ids. Will do nothing, if user/chat
        is already present.

        Args:
            chat_id(:obj:`int` | List[:obj:`int`], optional): Which chat ID(s) to allow
                through.
        """
        with self.__lock:
            self._chat_ids |= self._parse_chat_id(chat_id)

    def kick_member(self, chat_id: Union[int, List[int], Tuple[int, ...]]) -> None:
        """Kicks one ore more user(s)/chat(s) to from role. Will do nothing, if user/chat is not
        present.

        Args:
            chat_id(:obj:`int` | List[:obj:`int`], optional): The users/chats id
        """
        with self.__lock:
            self._chat_ids -= self._parse_chat_id(chat_id)

    def add_child_role(self, child_role: 'Role') -> None:
        """Adds a child role to this role. Will do nothing, if child role is already present.

        Args:
            child_role (:class:`telegram.ext.Role`): The child role
        """
        if self is child_role:
            raise ValueError('You must not add a role as its own child!')
        if self <= child_role:
            raise ValueError('You must not add a parent role as a child!')
        with self.__lock:
            self._child_roles |= {child_role}

    def remove_child_role(self, child_role: 'Role') -> None:
        """Removes a child role from this role. Will do nothing, if child role is not present.

        Args:
            child_role (:class:`telegram.ext.Role`): The child role
        """
        with self.__lock:
            self._child_roles.discard(child_role)

    def __lt__(self, other: object) -> bool:
        # Test for hierarchical order
        if isinstance(other, Role):
            return self is not other and any(self <= child for child in other.child_roles)
        return False

    def __le__(self, other: object) -> bool:
        # Test for hierarchical order
        return self is other or self < other

    def __gt__(self, other: object) -> bool:
        # Test for hierarchical order
        if isinstance(other, Role):
            return self is not other and any(other <= child for child in self.child_roles)
        return False

    def __ge__(self, other: object) -> bool:
        # Test for hierarchical order
        return self is other or self > other

    def __eq__(self, other: object) -> bool:
        return self is other

    def __ne__(self, other: object) -> bool:
        return not self == other

    def equals(self, other: 'Role') -> bool:
        """Test if two roles are equal in terms of hierarchy. Returns :obj:``True``, if the
        :attr:`chat_ids` coincide and the child roles are equal in terms of this method.

        Note:
            The result of this comparison may change by adding or removing child roles or
            members.

        Args:
            other (:class:`telegram.ext.Role`):

        Returns:
            :obj:`bool`:
        """
        if self.chat_ids == other.chat_ids:
            if len(self.child_roles) == len(other.child_roles):
                if len(self.child_roles) == 0:
                    return True
                for child_role in self.child_roles:
                    if not any(child_role.equals(ocr) for ocr in other.child_roles):
                        return False
                for ocr in other.child_roles:
                    if not any(ocr.equals(cr) for cr in self.child_roles):
                        return False
                return True
        return False

    def __hash__(self) -> int:
        return id(self)

    @property
    def name(self) -> str:  # pylint: disable=C0116
        if self._name:
            return f'Role({self._name})'
        if self.chat_ids:
            return f'Role({set(self.chat_ids)})'
        return 'Role({})'

    def __getstate__(self) -> Dict[str, Any]:
        """
        Gets called, when object is being pickled. Sets all variables ending on ``_lock`` to
        :obj:`None`.
        Returns: The dictionary describing the current state of the object.
        """
        state = self.__dict__.copy()
        for key, value in state.items():
            if isinstance(value, type(Lock())):
                state[key] = _REPLACED_LOCK
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """
        Gets called, when object is being un-pickled. Sets all variables ending on ``_lock`` to
        a new :class:`threading.Lock` instance.
        Args:
            state: The pickled state of the object as produced by :meth:`__getstate__`.
        """
        for key, value in state.items():
            if isinstance(value, str) and value == _REPLACED_LOCK:
                state[key] = Lock()
        self.__dict__.update(state)

        self.__init_admin()
        self._admin_event.wait()
        self._admin.add_child_role(self)


class InvertedRole(UpdateFilter):
    """Represents a filter that has been inverted.

    Args:
        f: The filter to invert.

    """

    def __init__(self, role: Role):
        self.role = role

    def filter(self, update: Update) -> bool:
        return self.role.filter(update, inverted=True)

    def __repr__(self) -> str:
        return f"<inverted {self.role}>"


class ChatAdminsRole(Role):  # pylint: disable=R0901
    """A :class:`telegram.ext.Role` that allows only the administrators of a chat. Private chats
    are always allowed. To minimize the number of API calls, for each chat the admins will be
    cached.

    Note:
        Instance of this class can't be inverted, as that would make little sense.

    Attributes:
        timeout (:obj:`int`): The caching timeout in seconds. For each chat, the admins will be
            cached and refreshed only after this timeout.

    Args:
        bot (:class:`telegram.Bot`): A bot to use for getting the administrators of a chat.
        timeout (:obj:`int`, optional): The caching timeout in seconds. For each chat, the admins
            will be cached and refreshed only after this timeout. Defaults to ``1800`` (half an
            hour).
    """

    def __init__(self, bot: Bot, timeout: float = 1800):
        super().__init__(name='chat_admins')
        self.bot = bot
        self.cache: Dict[int, Tuple[float, List[int]]] = {}
        self.timeout = timeout

    def __invert__(self) -> NoReturn:
        raise RuntimeError('Instances of ChatAdminsRole can not be inverted')

    def filter(self, update: Update, target: Role = None, inverted: bool = False) -> bool:
        # Always allow admins
        if self is not self._admin and self._admin.filter(update):
            return True

        user = update.effective_user
        chat = update.effective_chat

        if user and chat:
            # Always true in private chats
            if chat.type == Chat.PRIVATE:
                return True

            # Check for cached info first
            if (
                self.cache.get(chat.id, None)
                and (time.time() - self.cache[chat.id][0]) < self.timeout
            ):
                return user.id in self.cache[chat.id][1]

            admins = [m.user.id for m in self.bot.get_chat_administrators(chat.id)]
            self.cache[chat.id] = (time.time(), admins)
            return user.id in admins
        return False


class ChatCreatorRole(Role):  # pylint: disable=R0901
    """A :class:`telegram.ext.Role` that allows only the creator of a chat. Private chats are
    always allowed. To minimize the number of API calls, for each chat the creator will be saved.

    Note:
        Instance of this class can't be inverted, as that would make little sense.

    Args:
        bot (:class:`telegram.Bot`): A bot to use for getting the creator of a chat.
    """

    def __init__(self, bot: Bot) -> None:
        super().__init__(name='chat_creator')
        self.bot = bot
        self.cache: Dict[int, int] = {}

    def __invert__(self) -> NoReturn:
        raise RuntimeError('Instances of ChatCreatorRole can not be inverted')

    def filter(  # pylint: disable=R0911
        self, update: Update, target: Role = None, inverted: bool = False
    ) -> bool:
        # Always allow admins
        if self is not self._admin and self._admin.filter(update):
            return True

        user = update.effective_user
        chat = update.effective_chat

        if user and chat:
            # Always true in private chats
            if chat.type == Chat.PRIVATE:
                return True

            # Check for cached info first
            if self.cache.get(chat.id, None):
                return user.id == self.cache[chat.id]
            try:
                member = self.bot.get_chat_member(chat.id, user.id)
                if member.status == ChatMember.CREATOR:
                    self.cache[chat.id] = user.id
                    return True
                return False
            except TelegramError:
                # user is not a chat member or bot has no access
                return False
        return False


class Roles(Mapping):
    """This class represents a collection of :class:`telegram.ext.Role` s that can be used to
    manage access control to functionality of a bot. Each role can be accessed by its name, e.g.::

        roles.add_role('my_role')
        role = roles['my_role']

    Note:
        In fact, :class:`telegram.ext.Roles` is a :class:`collections.Mapping` and as such can be
        be used almost like a dictionary.

    Attributes:
        admins (:class:`telegram.ext.Role`): A role reserved for administrators of the bot. All
            roles added to this instance will be child roles of :attr:`ADMINS`.
        chat_admins (:class:`telegram.ext.roles.ChatAdminsRole`): Use this role to restrict access
            to admins of a chat. Handlers with this role wont handle updates that don't have an
            ``effective_chat``. Admins are cached for each chat.
        chat_creator (:class:`telegram.ext.roles.ChatCreatorRole`): Use this role to restrict
            access to the creator of a chat. Handlers with this role wont handle updates that don't
            have an ``effective_chat``.

    Args:
        bot (:class:`telegram.Bot`): A bot associated with this instance.
    """

    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.__lock = Lock()
        self.__roles: Dict[str, Role] = {}
        self.bot = bot

        self.admins = Role(name='admins')
        self.chat_admins = ChatAdminsRole(bot=self.bot)
        self.chat_creator = ChatCreatorRole(bot=self.bot)

        self.chat_admins._set_custom_admin(self.admins)
        self.chat_creator._set_custom_admin(self.admins)

    def set_bot(self, bot: Bot) -> None:
        """If for some reason you can't pass the bot on initialization, you can set it with this
        method. Make sure to set the bot before the first call of :attr:`chat_admins` or
        :attr:`chat_creator`.

        Args:
            bot (:class:`telegram.Bot`): The bot to set.

        Raises:
            ValueError
        """
        if isinstance(self.bot, Bot):
            raise ValueError('Bot is already set for this Roles instance')
        self.bot = bot

    def __getitem__(self, item: str) -> Role:
        with self.__lock:
            return self.__roles[item]

    def __iter__(self) -> Iterator[str]:
        return iter(self.__roles)

    def __len__(self) -> int:
        with self.__lock:
            return len(self.__roles)

    def add_admin(self, chat_id: Union[int, List[int], Tuple[int, ...]]) -> None:
        """Adds a user/chat to the :attr:`admins` role. Will do nothing if user/chat is already
        present.

        Args:
            chat_id (:obj:`int`): The users id
        """
        self.admins.add_member(chat_id)

    def kick_admin(self, chat_id: Union[int, List[int], Tuple[int, ...]]) -> None:
        """Kicks a user/chat from the :attr:`admins` role. Will do nothing if user/chat is not
        present.

        Args:
            chat_id (:obj:`int`): The users/chats id
        """
        self.admins.kick_member(chat_id)

    def add_role(
        self,
        name: str,
        chat_ids: Union[int, List[int], Tuple[int, ...]] = None,
        child_roles: Union['Role', List['Role'], Tuple['Role', ...]] = None,
    ) -> None:
        """Creates and registers a new role. :attr:`admins` will automatically be added to the
        roles parent roles, i.e. admins can do everything. The role can be accessed by it's
        name.

        Args:
            name (:obj:`str`, optional): A name for this role.
            chat_ids (:obj:`int` | iterable(:obj:`int`), optional): The ids of the users/chats of
                this role.
            child_roles (:class:`telegram.ext.Role` | set(:class:`telegram.ext.Role`), optional):
                Child roles of this role.

        Raises:
            ValueError
        """
        if name in self:
            raise ValueError('Role name is already taken.')
        role = Role(chat_ids=chat_ids, child_roles=child_roles, name=name)
        role._set_custom_admin(self.admins)  # pylint: disable=W0212
        with self.__lock:
            self.__roles[name] = role

    def remove_role(self, name: str) -> Role:
        """Removes a role.

        Args:
            name (:obj:`str`): The name of the role to be removed

        Returns:
            The removed role.
        """
        with self.__lock:
            role = self.__roles.pop(name)
        self.admins.remove_child_role(role)
        Role._admin.add_child_role(role)  # pylint: disable=W0212
        return role

    def __getstate__(self) -> Dict[str, Any]:
        """
        Gets called, when object is being pickled. Sets all variables ending on ``_lock`` to
        :obj:`None`.
        Returns: The dictionary describing the current state of the object.
        """
        state = self.__dict__.copy()
        for key, value in state.items():
            if isinstance(value, type(Lock())):
                state[key] = _REPLACED_LOCK
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """
        Gets called, when object is being un-pickled. Sets all variables ending on ``_lock`` to
        a new :class:`threading.Lock` instance.
        Args:
            state: The pickled state of the object as produced by :meth:`__getstate__`.
        """
        for key, value in state.items():
            if isinstance(value, str) and value == _REPLACED_LOCK:
                state[key] = Lock()
        self.__dict__.update(state)

        for role in self.values():
            role._set_custom_admin(self.admins)
