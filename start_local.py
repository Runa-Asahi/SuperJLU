"""Start this source checkout without redirecting to a separately installed EXE."""
import threading
import webbrowser
from pathlib import Path

from jlu_toolkit import __version__, desktop, ui


def main():
    # A running server keeps its imported Python modules in memory. Always
    # start this checkout so reopening the launcher picks up local edits.
    server, base = desktop.start_server()
    url = ui.launch_url(base, server.RequestHandlerClass.auth_token)
    print(f"SuperJLU {__version__}: {url}", flush=True)
    print(f"Source: {Path(__file__).resolve().parent}", flush=True)
    if server.server_address[1] != desktop.DEFAULT_PORT:
        print("Port 8765 is in use. Use the URL above for this local version.", flush=True)
    print("Keep this window open. Press Ctrl+C to stop.", flush=True)
    try:
        webbrowser.open(url)
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
