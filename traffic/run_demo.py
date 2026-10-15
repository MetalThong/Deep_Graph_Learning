"""Serve the bundled demo offline. Uses only the Python standard library."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import webbrowser


def main():
    dist = Path(__file__).resolve().parent / 'dist'
    if not (dist / 'index.html').is_file():
        raise SystemExit('Missing dist/index.html. Extract the entire ZIP first.')
    handler = partial(SimpleHTTPRequestHandler, directory=str(dist))
    server = None
    for port in range(8766, 8776):
        try:
            server = ThreadingHTTPServer(('127.0.0.1', port), handler)
            break
        except OSError:
            continue
    if server is None:
        raise SystemExit('Ports 8766-8775 are busy. Close a previous demo and retry.')
    url = f'http://127.0.0.1:{server.server_port}/'
    print(f'Traffic Graph Lab v2: {url}\nKeep this window open. Press Ctrl+C to stop.', flush=True)
    opener = threading.Timer(0.5, webbrowser.open, args=(url,))
    opener.daemon = True
    opener.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
