import socket


def get_lan_ip():
    """Best-effort local network IP (no data is actually sent) so a dashboard can tell
    the user what address a friend on the same WiFi/hotspot should type in their browser."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip
