"""Offline checks; the browser fixture never sees a real account or cookie."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch

from pirate_ship_api_mcp import app, session
from pirate_ship_api_mcp.core.context import ToolContext, allowed_host
from pirate_ship_api_mcp.core.errors import ErrorCode, ToolError


def cookie(domain=app.COOKIE_DOMAIN, name=session.SESSION_COOKIE):
    return {"name": name, "value": "synthetic-cookie", "domain": domain, "path": "/"}


class SessionTests(unittest.TestCase):
    def browser(self, targets):
        client = MagicMock()
        answers = {
            "Browser.getVersion": {"userAgent": "Chrome/144.0.0.0"},
            "Target.getTargets": {"targetInfos": targets},
            "Target.attachToTarget": {"sessionId": "tab-session"},
            "Network.getCookies": {"cookies": [cookie(app.COOKIE_DOMAIN, "analytics"), cookie("notpirateship.com"),
                                               cookie(".pirateship.com")]},
            "Runtime.evaluate": {"result": {"value": "America/Phoenix"}},
            "Target.detachFromTarget": {},
        }
        client.send.side_effect = lambda method, *_: answers[method]
        return client

    def test_scoped_target_cookie_call(self):
        client = self.browser([
            {"type": "page", "url": "https://notpirateship.com/", "targetId": "lookalike"},
            {"type": "page", "url": "https://ship.pirateship.com/ship", "targetId": "app"},
        ])
        with patch.object(session, "_Cdp", return_value=client):
            result = session.from_chrome("ws://127.0.0.1:1234/test")
        self.assertTrue(result.signed_in)
        self.assertEqual(result.cookies, [cookie(".pirateship.com")])
        self.assertEqual(result.timezone, "America/Phoenix")
        self.assertEqual(
            client.send.call_args_list[:4],
            [call("Browser.getVersion"), call("Target.getTargets"),
             call("Target.attachToTarget", {"targetId": "app", "flatten": True}),
             call("Network.getCookies", {"urls": ["https://ship.pirateship.com/api/graphql"]}, "tab-session")],
        )
        self.assertEqual(client.send.call_args_list[-1], call("Target.detachFromTarget", {"sessionId": "tab-session"}))
        client.close.assert_called_once_with()

    def test_never_reads_from_unrelated_or_ambiguous_pages(self):
        for targets in (
            [{"type": "page", "url": "http://ship.pirateship.com/", "targetId": "insecure"}],
            [{"type": "page", "url": app.LOGIN_URL, "targetId": i, "browserContextId": i} for i in ("one", "two")],
        ):
            client = self.browser(targets)
            with patch.object(session, "_Cdp", return_value=client), self.assertRaises(ToolError) as raised:
                session.from_chrome("ws://127.0.0.1:1234/test")
            self.assertEqual(raised.exception.code, ErrorCode.AUTH_REQUIRED)
            self.assertEqual(client.send.call_args_list, [call("Browser.getVersion"), call("Target.getTargets")])
            client.close.assert_called_once_with()

    def test_narrows_existing_caches_and_keeps_manual_login_supported(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict("os.environ", {}, clear=True):
            path = Path(folder) / "session.json"
            cookies = [cookie(), cookie(".notpirateship.com"), cookie(name="analytics")]
            path.write_text(json.dumps({"cookies": cookies}))
            with patch.object(session, "session_path", return_value=path):
                self.assertEqual(session.load().cookies, [cookie()])
                session.save(session.Session(cookies=cookies))
                self.assertEqual(json.loads(path.read_text())["cookies"], [cookie()])
            self.assertTrue(session.from_token("synthetic-manual-token").signed_in)


class HttpsTests(unittest.IsolatedAsyncioTestCase):
    def test_host_boundary_and_https(self):
        self.assertTrue(allowed_host(app.SESSION_COOKIE_URL))
        self.assertFalse(allowed_host("http://ship.pirateship.com/api/graphql"))
        self.assertFalse(allowed_host("https://notpirateship.com/api/graphql"))

    async def test_never_follows_http_downgrade(self):
        req = AsyncMock(return_value=SimpleNamespace(
            headers={"location": "http://ship.pirateship.com/api/graphql"},
            status_code=302,
            url=app.SESSION_COOKIE_URL,
        ))
        context = ToolContext(session.Session(cookies=[cookie()]), _http=SimpleNamespace(request=req))
        with self.assertRaises(ToolError) as raised:
            await context.call("GET", app.SESSION_COOKIE_URL)
        self.assertEqual(raised.exception.code, ErrorCode.TARGET_ERROR)
        req.assert_awaited_once()

    async def test_cookie_jar_requires_https(self):
        context = ToolContext(session.Session(cookies=[cookie()]))
        try:
            self.assertTrue(next(iter(context._client().cookies.jar)).secure)
        finally:
            await context.close()


if __name__ == "__main__":
    unittest.main()
