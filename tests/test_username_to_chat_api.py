import pytest
from telegram import Chat, error

try:
    import telegram.vendor.ptb_urllib3.urllib3 as urllib3
except ImportError:  # pragma: no cover
    import urllib3

try:
    import ujson as json
except ImportError:
    import json

from ptbcontrib.username_to_chat_api import UsernameToChatAPI


class TestUsernameToChatAPI:
    def test_normal_run(self, monkeypatch, bot):
        api_result = {
            "ok": True,
            "result": {
                "id": 123,
                "type": "private",
                "username": "username",
                "first_name": "name",
                "last_name": "last_name",
                "bio": "A description.",
            },
        }

        response = urllib3.response.HTTPResponse(
            body=json.dumps(api_result).encode("UTF-8"), status=200
        )

        def mockreturn(*args, **kwargs):
            return response

        monkeypatch.setattr(urllib3.PoolManager, "request", mockreturn)
        wrapper = UsernameToChatAPI("URL", "key", bot)
        chat = wrapper.resolve("username")
        assert type(chat) == Chat
        assert chat.id == 123
        assert chat.type == Chat.PRIVATE
        assert chat.username == "username"
        assert chat.first_name == "name"
        assert chat.last_name == "last_name"
        assert chat.bio == "A description."

    def test_normal_run_channel(self, monkeypatch, bot):
        api_result = {
            "ok": True,
            "result": {
                "id": 123,
                "type": "channel",
                "username": "username",
                "title": "channel_name",
                "description": "A description.",
            },
        }

        response = urllib3.response.HTTPResponse(
            body=json.dumps(api_result).encode("UTF-8"), status=200
        )

        def mockreturn(*args, **kwargs):
            return response

        monkeypatch.setattr(urllib3.PoolManager, "request", mockreturn)
        wrapper = UsernameToChatAPI("URL", "key", bot)
        chat = wrapper.resolve("username")
        assert type(chat) == Chat
        assert chat.id == 123
        assert chat.type == Chat.CHANNEL
        assert chat.username == "username"
        assert chat.title == "channel_name"
        assert chat.description == "A description."

    @pytest.mark.parametrize(
        "error_code,description, error_object",
        [
            (401, "Unauthorized", error.Unauthorized),
            (400, "Bad Request: chat not found", error.BadRequest),
            (429, "Telegram forces us to wait", error.RetryAfter),
            (499, "This cant happen", error.TelegramError),
        ],
    )
    def test_errors(self, monkeypatch, bot, error_code, description, error_object):
        api_result = {"ok": False, "error_code": error_code, "description": description}
        if error_code == 429:
            # this add the flood wait time when the flood wait error happens
            api_result["retry_after"] = 12

        response = urllib3.response.HTTPResponse(
            body=json.dumps(api_result).encode("UTF-8"), status=error_code
        )

        def mockreturn(*args, **kwargs):
            return response

        monkeypatch.setattr(urllib3.PoolManager, "request", mockreturn)
        wrapper = UsernameToChatAPI("URL", "key", bot)
        with pytest.raises(error_object):
            wrapper.resolve("username")

        if error_code == 429:
            try:
                wrapper.resolve("username")
            except error.RetryAfter as e:
                # specific check that the flood wait time out is provided
                assert e.retry_after == 12
