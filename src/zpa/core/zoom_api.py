"""
Zoom API communication for Zoom Poll Analyzer.
Handles authentication and data retrieval from Zoom API.
"""

import base64
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional


def _normalize_proxy(proxy_str: Optional[str]) -> Optional[str]:
    """Turn a WinHTTP/PAC proxy list into a single 'http://host:port' URL."""
    if not proxy_str:
        return None
    for token in re.split(r"[;\s]+", proxy_str.strip()):
        if not token:
            continue
        if token.upper() == "DIRECT":
            return None
        if token.upper() == "PROXY":
            continue
        return token if "://" in token else "http://" + token
    return None


def _windows_autoconfig_url() -> Optional[str]:
    """Read the PAC (AutoConfigURL) from the WinINET registry, if any."""
    try:
        import winreg
    except ImportError:
        return None
    path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(root, path) as key:
                url, _ = winreg.QueryValueEx(key, "AutoConfigURL")
                if url:
                    return url
        except OSError:
            continue
    return None


def _windows_detect_proxy(target_url: str) -> Optional[str]:
    """Resolve the effective proxy for *target_url* on Windows using WinHTTP.

    Honors an explicit PAC (AutoConfigURL) and WPAD auto-detection (DHCP/DNS),
    which urllib.getproxies() cannot do. Returns 'http://host:port' or None.
    """
    if sys.platform != "win32":
        return None
    pac_url = _windows_autoconfig_url()
    if not pac_url:
        return None  # no PAC configured; skip slow WPAD auto-detect on startup
    import ctypes
    from ctypes import wintypes

    WINHTTP_AUTOPROXY_CONFIG_URL = 0x00000002
    WINHTTP_ACCESS_TYPE_NO_PROXY = 1

    class AUTOPROXY_OPTIONS(ctypes.Structure):
        _fields_ = [
            ("dwFlags", wintypes.DWORD),
            ("dwAutoDetectFlags", wintypes.DWORD),
            ("lpszAutoConfigUrl", wintypes.LPCWSTR),
            ("lpvReserved", ctypes.c_void_p),
            ("dwReserved", wintypes.DWORD),
            ("fAutoLogonIfChallenged", wintypes.BOOL),
        ]

    class PROXY_INFO(ctypes.Structure):
        _fields_ = [
            ("dwAccessType", wintypes.DWORD),
            ("lpszProxy", ctypes.c_void_p),
            ("lpszProxyBypass", ctypes.c_void_p),
        ]

    try:
        winhttp = ctypes.WinDLL("winhttp")
    except OSError:
        return None

    winhttp.WinHttpOpen.restype = ctypes.c_void_p
    winhttp.WinHttpOpen.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
    ]
    winhttp.WinHttpGetProxyForUrl.argtypes = [
        ctypes.c_void_p,
        wintypes.LPCWSTR,
        ctypes.POINTER(AUTOPROXY_OPTIONS),
        ctypes.POINTER(PROXY_INFO),
    ]
    winhttp.WinHttpGetProxyForUrl.restype = wintypes.BOOL
    winhttp.WinHttpCloseHandle.argtypes = [ctypes.c_void_p]

    kernel32 = ctypes.windll.kernel32
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p

    session = winhttp.WinHttpOpen("ZPA", WINHTTP_ACCESS_TYPE_NO_PROXY, None, None, 0)
    if not session:
        return None
    try:
        options = AUTOPROXY_OPTIONS()
        options.dwFlags = WINHTTP_AUTOPROXY_CONFIG_URL
        options.lpszAutoConfigUrl = pac_url
        options.fAutoLogonIfChallenged = True

        info = PROXY_INFO()
        ok = winhttp.WinHttpGetProxyForUrl(
            session, target_url, ctypes.byref(options), ctypes.byref(info)
        )
        if not ok:
            return None
        proxy_ptr = info.lpszProxy
        bypass_ptr = info.lpszProxyBypass
        try:
            proxy_str = ctypes.wstring_at(proxy_ptr) if proxy_ptr else None
            return _normalize_proxy(proxy_str)
        finally:
            if proxy_ptr:
                kernel32.GlobalFree(proxy_ptr)
            if bypass_ptr:
                kernel32.GlobalFree(bypass_ptr)
    finally:
        winhttp.WinHttpCloseHandle(session)


def resolve_proxy(autodetect: bool, manual_proxy: str = "") -> Optional[str]:
    """Return the effective proxy URL to use, or None for a direct connection.

    When *autodetect* is True the system proxy is discovered cross-platform:
      1. Environment variables / OS static settings via urllib.getproxies()
         (Windows registry, macOS system configuration, Linux env vars).
      2. On Windows, a PAC file (AutoConfigURL) or WPAD auto-detection is then
         resolved via WinHTTP - which urllib cannot do on its own.
    Otherwise *manual_proxy* is used (or None when empty).
    """
    if not autodetect:
        return manual_proxy or None
    proxies = urllib.request.getproxies()
    detected = proxies.get("https") or proxies.get("http")
    if detected:
        return _normalize_proxy(detected)
    return _windows_detect_proxy("https://api.zoom.us")


def test_internet(proxy: Optional[str] = None, timeout: float = 8.0) -> bool:
    """Return True if the Zoom API is reachable (optionally through *proxy*).

    Any HTTP response - including 401 Unauthorized - proves connectivity works;
    only network-level failures (refused, timeout, DNS) return False.
    """
    if proxy:
        handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    else:
        handler = urllib.request.ProxyHandler()
    opener = urllib.request.build_opener(handler)
    request = urllib.request.Request(
        "https://api.zoom.us/v2/users/me", headers={"Accept": "application/json"}
    )
    try:
        opener.open(request, timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False


class ZoomAPI:
    """Handle Zoom API communications"""

    def __init__(
        self, account_id: str, client_id: str, client_secret: str, proxy: str = None
    ):
        self.account_id = account_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        # Build a URL opener. When an explicit proxy is provided (e.g. a corporate
        # proxy) it is always used; otherwise urllib's default system/environment
        # proxies apply. Using our own opener keeps the app working even when it is
        # launched without HTTP(S)_PROXY variables in its environment (e.g. the
        # packaged .exe started from Explorer).
        if proxy:
            proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        else:
            proxy_handler = urllib.request.ProxyHandler()
        self.opener = urllib.request.build_opener(proxy_handler)

    def get_access_token(self) -> str:
        """Get OAuth access token from Zoom"""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Authorization": f"Basic {encoded_credentials}",
        }

        data = urllib.parse.urlencode(
            {"grant_type": "account_credentials", "account_id": self.account_id}
        )

        request = urllib.request.Request(
            "https://zoom.us/oauth/token",
            data=data.encode(),
            headers=headers,
            method="POST",
        )

        with self.opener.open(request) as response:
            oauth_data = json.loads(response.read().decode())
            self.access_token = oauth_data["access_token"]
            return self.access_token

    def make_api_request(self, url: str) -> Dict:
        """Make authenticated API request to Zoom"""
        if not self.access_token:
            self.get_access_token()

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        # All callers pass https://api.zoom.us/... URLs.
        request = urllib.request.Request(url, headers=headers)  # noqa: S310
        with self.opener.open(request) as response:
            return json.loads(response.read().decode())

    def get_meeting_info(self, meeting_id: str, debug: bool = False) -> Dict:
        """Get meeting information"""
        url = f"https://api.zoom.us/v2/meetings/{meeting_id}"

        if debug:
            print(f"Debug: Getting meeting info from: {url}")

        try:
            result = self.make_api_request(url)
            if debug:
                print(
                    f"Debug: Meeting info keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
                )
                # Check if meeting info contains poll-related data
                if isinstance(result, dict):
                    poll_related = [k for k in result.keys() if "poll" in k.lower()]
                    if poll_related:
                        print(
                            f"Debug: Found poll-related keys in meeting info: {poll_related}"
                        )
            # If start_time is missing, try past meetings endpoint
            if isinstance(result, dict) and not result.get("start_time"):
                raise Exception(
                    "No start_time in meeting info, trying past meetings endpoint"
                )
            return result
        except Exception as e:
            if debug:
                print(
                    f"Debug: Meeting endpoint failed: {e}, trying past_meetings endpoint"
                )
            # Fallback: try past meetings endpoint
            try:
                past_url = f"https://api.zoom.us/v2/past_meetings/{meeting_id}"
                result = self.make_api_request(past_url)
                if debug:
                    print(
                        f"Debug: Past meeting info keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
                    )
                return result
            except Exception as e2:
                if debug:
                    print(f"Debug: Past meeting endpoint also failed: {e2}")
                return {}

    def get_participants(self, meeting_id: str) -> List[Dict]:
        """Get all meeting participants with pagination"""
        participants = []
        url = f"https://api.zoom.us/v2/past_meetings/{meeting_id}/participants?page_size=30"

        while url:
            data = self.make_api_request(url)
            meeting_participants = data.get("participants", [])
            # Filter for participants who were actually in the meeting
            participants.extend(
                [p for p in meeting_participants if p.get("status") == "in_meeting"]
            )

            # Check for next page
            next_page_token = data.get("next_page_token")
            if next_page_token:
                url = f"https://api.zoom.us/v2/past_meetings/{meeting_id}/participants?next_page_token={next_page_token}"
            else:
                url = None

        return participants

    def get_poll_results(self, meeting_id: str, debug: bool = False) -> Dict:
        """Get poll results for the meeting"""
        if debug:
            print(f"Debug: Attempting to get poll results for meeting {meeting_id}")

        # Try different poll endpoints
        endpoints = [
            f"https://api.zoom.us/v2/past_meetings/{meeting_id}/polls",
            f"https://api.zoom.us/v2/meetings/{meeting_id}/polls",
            f"https://api.zoom.us/v2/report/meetings/{meeting_id}/polls",
        ]

        for i, url in enumerate(endpoints):
            if debug:
                print(f"Debug: Trying poll endpoint {i + 1}/3: {url}")

            try:
                result = self.make_api_request(url)
                if debug:
                    print(
                        f"Debug: Endpoint {i + 1} success - Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
                    )
                    if isinstance(result, dict) and result:
                        print(f"Debug: Poll response content: {result}")

                # Check if we got poll data
                if isinstance(result, dict) and (
                    "polls" in result or "questions" in result or len(result) > 0
                ):
                    if debug:
                        print(f"Debug: Found poll data using endpoint {i + 1}")
                    return result

            except Exception as e:
                if debug:
                    print(f"Debug: Endpoint {i + 1} failed: {e}")
                continue

        if debug:
            print("Debug: No poll data found from any endpoint")
        return {}

    @staticmethod
    def encode_uuid(uuid: str) -> str:
        """URL-encode a meeting UUID for use in a request path.

        Per Zoom's rules the UUID is double-encoded when it begins with '/' or
        contains '//', otherwise single-encoded.
        """
        once = urllib.parse.quote(uuid, safe="")
        if uuid.startswith("/") or "//" in uuid:
            return urllib.parse.quote(once, safe="")
        return once

    def get_past_meeting_instances(self, meeting_id: str) -> List[Dict]:
        """Return past instances of a meeting, newest first.

        Each item has a 'uuid' and 'start_time'. Requires the
        'meeting:read:list_past_instances:admin' scope; instances are available
        for meetings that ended within the last 15 months.
        """
        url = f"https://api.zoom.us/v2/past_meetings/{meeting_id}/instances"
        data = self.make_api_request(url)
        instances = data.get("meetings", []) if isinstance(data, dict) else []
        instances.sort(key=lambda m: m.get("start_time", "") or "", reverse=True)
        return instances
