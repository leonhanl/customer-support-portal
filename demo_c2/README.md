# demo_c2 — Lab Demo C2 Listener

> **Lab use only.** This is a controlled receiver for the demo reverse shell.
> It does not relay commands, does not forward sessions, and accepts no
> remote input. Deploy only in an isolated lab network.

## Quick Start (VM-2)

```bash
# Copy listener to VM-2
scp demo_c2/listener.py user@demo-c2-vm:/opt/demo-c2/listener.py

# On VM-2: run directly
python3 /opt/demo-c2/listener.py

# Or install as systemd service
sudo cp demo_c2/systemd/demo-c2.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now demo-c2
sudo journalctl -fu demo-c2
```

## /etc/hosts entry on VM-1 (support-portal)

Add to `/etc/hosts` so the reverse shell payload can resolve the C2 hostname:

```
<VM-2-IP>  demo-c2.local
```

## What XDR observes

- `python` process on VM-1 spawns `bash -i` subprocess
- `bash` process opens outbound TCP to `demo-c2.local:4444`
- Network telemetry: VM-1 → VM-2 on port 4444
