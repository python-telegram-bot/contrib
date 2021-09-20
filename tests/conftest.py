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
import os
from collections import defaultdict
from queue import Queue
from threading import Thread, Event
from time import sleep

import pytest
import pytz

from telegram import Bot, User
from telegram.ext import Dispatcher, JobQueue, Updater, Defaults

GITHUB_ACTION = os.getenv('GITHUB_ACTION', False)

if GITHUB_ACTION:
    pytest_plugins = ['tests.plugin_github_group']

# THIS IS OBVIOUSLY COMPROMISED
# DO NOT USE IN PRODUCTION!
PRIVATE_KEY = b"-----BEGIN RSA PRIVATE KEY-----\r\nMIIEowIBAAKCAQEA0AvEbNaOnfIL3GjB8VI4M5IaWe+GcK8eSPHkLkXREIsaddum\r\nwPBm/+w8lFYdnY+O06OEJrsaDtwGdU//8cbGJ/H/9cJH3dh0tNbfszP7nTrQD+88\r\nydlcYHzClaG8G+oTe9uEZSVdDXj5IUqR0y6rDXXb9tC9l+oSz+ShYg6+C4grAb3E\r\nSTv5khZ9Zsi/JEPWStqNdpoNuRh7qEYc3t4B/a5BH7bsQENyJSc8AWrfv+drPAEe\r\njQ8xm1ygzWvJp8yZPwOIYuL+obtANcoVT2G2150Wy6qLC0bD88Bm40GqLbSazueC\r\nRHZRug0B9rMUKvKc4FhG4AlNzBCaKgIcCWEqKwIDAQABAoIBACcIjin9d3Sa3S7V\r\nWM32JyVF3DvTfN3XfU8iUzV7U+ZOswA53eeFM04A/Ly4C4ZsUNfUbg72O8Vd8rg/\r\n8j1ilfsYpHVvphwxaHQlfIMa1bKCPlc/A6C7b2GLBtccKTbzjARJA2YWxIaqk9Nz\r\nMjj1IJK98i80qt29xRnMQ5sqOO3gn2SxTErvNchtBiwOH8NirqERXig8VCY6fr3n\r\nz7ZImPU3G/4qpD0+9ULrt9x/VkjqVvNdK1l7CyAuve3D7ha3jPMfVHFtVH5gqbyp\r\nKotyIHAyD+Ex3FQ1JV+H7DkP0cPctQiss7OiO9Zd9C1G2OrfQz9el7ewAPqOmZtC\r\nKjB3hUECgYEA/4MfKa1cvaCqzd3yUprp1JhvssVkhM1HyucIxB5xmBcVLX2/Kdhn\r\nhiDApZXARK0O9IRpFF6QVeMEX7TzFwB6dfkyIePsGxputA5SPbtBlHOvjZa8omMl\r\nEYfNa8x/mJkvSEpzvkWPascuHJWv1cEypqphu/70DxubWB5UKo/8o6cCgYEA0HFy\r\ncgwPMB//nltHGrmaQZPFT7/Qgl9ErZT3G9S8teWY4o4CXnkdU75tBoKAaJnpSfX3\r\nq8VuRerF45AFhqCKhlG4l51oW7TUH50qE3GM+4ivaH5YZB3biwQ9Wqw+QyNLAh/Q\r\nnS4/Wwb8qC9QuyEgcCju5lsCaPEXZiZqtPVxZd0CgYEAshBG31yZjO0zG1TZUwfy\r\nfN3euc8mRgZpSdXIHiS5NSyg7Zr8ZcUSID8jAkJiQ3n3OiAsuq1MGQ6kNa582kLT\r\nFPQdI9Ea8ahyDbkNR0gAY9xbM2kg/Gnro1PorH9PTKE0ekSodKk1UUyNrg4DBAwn\r\nqE6E3ebHXt/2WmqIbUD653ECgYBQCC8EAQNX3AFegPd1GGxU33Lz4tchJ4kMCNU0\r\nN2NZh9VCr3nTYjdTbxsXU8YP44CCKFG2/zAO4kymyiaFAWEOn5P7irGF/JExrjt4\r\nibGy5lFLEq/HiPtBjhgsl1O0nXlwUFzd7OLghXc+8CPUJaz5w42unqT3PBJa40c3\r\nQcIPdQKBgBnSb7BcDAAQ/Qx9juo/RKpvhyeqlnp0GzPSQjvtWi9dQRIu9Pe7luHc\r\nm1Img1EO1OyE3dis/rLaDsAa2AKu1Yx6h85EmNjavBqP9wqmFa0NIQQH8fvzKY3/\r\nP8IHY6009aoamLqYaexvrkHVq7fFKiI6k8myMJ6qblVNFv14+KXU\r\n-----END RSA PRIVATE KEY-----"  # noqa: E501
TOKEN = '1281106207:AAHXR4nqP-ZYsPLnrHooton3zUGGnsoNjZ8'


@pytest.fixture(scope='session')
def bot():
    return make_bot()


DEFAULT_BOTS = {}


@pytest.fixture(scope='function')
def default_bot(request):
    param = request.param if hasattr(request, 'param') else {}

    defaults = Defaults(**param)
    default_bot = DEFAULT_BOTS.get(defaults)
    if default_bot:
        return default_bot
    else:
        default_bot = make_bot(**{'defaults': defaults})
        DEFAULT_BOTS[defaults] = default_bot
        return default_bot


@pytest.fixture(scope='function')
def tz_bot(timezone):
    defaults = Defaults(tzinfo=timezone)
    default_bot = DEFAULT_BOTS.get(defaults)
    if default_bot:
        return default_bot
    else:
        default_bot = make_bot(**{'defaults': defaults})
        DEFAULT_BOTS[defaults] = default_bot
        return default_bot


def create_dp(bot):
    # Dispatcher is heavy to init (due to many threads and such) so we have a single session
    # scoped one here, but before each test, reset it (dp fixture below)
    dispatcher = Dispatcher(bot, Queue(), job_queue=JobQueue(), workers=2, use_context=True)
    dispatcher.job_queue.set_dispatcher(dispatcher)

    # we mock bot.{get_me, get_my_commands} b/c those are used in the @info decorator
    def get_me(*args, **kwargs):
        user = User(1, 'TestBot', True)
        dispatcher.bot._bot = user
        return user

    def get_my_commands(*args, **kwargs):
        return []

    orig_get_me = dispatcher.bot.get_me
    orig_get_my_commands = dispatcher.bot.get_my_commands
    dispatcher.bot.get_me = get_me
    dispatcher.bot.get_my_commands = get_my_commands

    thr = Thread(target=dispatcher.start)
    thr.start()
    sleep(2)
    yield dispatcher

    dispatcher.bot.get_me = orig_get_me
    dispatcher.bot.get_my_commands = orig_get_my_commands

    sleep(1)
    if dispatcher.running:
        dispatcher.stop()
    thr.join()


@pytest.fixture(scope='session')
def _dp(bot):
    yield from create_dp(bot)


@pytest.fixture(scope='function')
def dp(_dp):
    # Reset the dispatcher first
    while not _dp.update_queue.empty():
        _dp.update_queue.get(False)
    _dp.chat_data = defaultdict(dict)
    _dp.user_data = defaultdict(dict)
    _dp.bot_data = {}
    _dp.persistence = None
    _dp.handlers = {}
    _dp.groups = []
    _dp.error_handlers = {}
    # For some reason if we setattr with the name mangled, then some tests(like async) run forever,
    # due to threads not acquiring, (blocking). This adds these attributes to the __dict__.
    object.__setattr__(_dp, '__stop_event', Event())
    object.__setattr__(_dp, '__exception_event', Event())
    object.__setattr__(_dp, '__async_queue', Queue())
    object.__setattr__(_dp, '__async_threads', set())
    _dp.persistence = None
    _dp.use_context = False
    if _dp._Dispatcher__singleton_semaphore.acquire(blocking=0):
        Dispatcher._set_singleton(_dp)
    yield _dp
    Dispatcher._Dispatcher__singleton_semaphore.release()


@pytest.fixture(scope='function')
def cdp(dp):
    dp.use_context = True
    yield dp
    dp.use_context = False


@pytest.fixture(scope='function')
def updater(bot):
    up = Updater(bot=bot, workers=2, use_context=False)
    yield up
    if up.running:
        up.stop()


def pytest_configure(config):
    config.addinivalue_line('filterwarnings', 'ignore::ResourceWarning')
    # TODO: Write so good code that we don't need to ignore ResourceWarnings anymore


def make_bot(**kwargs):
    return Bot(TOKEN, private_key=PRIVATE_KEY, **kwargs)


@pytest.fixture(params=['Europe/Berlin', 'Asia/Singapore', 'UTC'])
def tzinfo(request):
    return pytz.timezone(request.param)


@pytest.fixture()
def timezone(tzinfo):
    return tzinfo


def env_var_2_bool(env_var: object) -> bool:
    if isinstance(env_var, bool):
        return env_var
    if not isinstance(env_var, str):
        return False
    return env_var.lower().strip() == 'true'
