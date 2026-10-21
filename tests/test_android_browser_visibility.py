"""Browser discovery must be visible without querying a complete app inventory."""
from pathlib import Path
import xml.etree.ElementTree as ET

MANIFEST = Path(__file__).resolve().parents[1] / "android/app/src/main/AndroidManifest.xml"
ANDROID = "{http://schemas.android.com/apk/res/android}"


def test_browser_visibility_only_covers_network_web_requests():
    root = ET.parse(MANIFEST).getroot()
    queries = root.find("queries")
    assert queries is not None
    assert not queries.findall("package")
    assert not queries.findall("provider")
    signatures = set()
    for intent in queries.findall("intent"):
        assert [action.get(ANDROID + "name") for action in intent.findall("action")] == ["android.intent.action.VIEW"]
        assert {category.get(ANDROID + "name") for category in intent.findall("category")} == {"android.intent.category.BROWSABLE"}
        data = intent.find("data")
        assert data is not None
        signatures.add((data.get(ANDROID + "scheme"), data.get(ANDROID + "mimeType")))
    assert signatures == {(scheme, mime) for scheme in ("http", "https")
                          for mime in (None, "text/html", "application/xhtml+xml")}


def test_browser_discovery_does_not_request_installed_app_inventory_or_file_access():
    permissions = {node.get(ANDROID + "name") for node in ET.parse(MANIFEST).getroot().findall("uses-permission")}
    assert permissions == {"android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE"}
