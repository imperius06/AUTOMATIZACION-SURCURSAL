#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generar respaldos de configuración por telnet (reemplazo de ansible-playbook backup)"""

import socket
import time
import os

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

def connect_and_run(host, port):
    """Conecta por telnet, envía show commands y retorna output."""
    s = socket.create_connection((host, port), timeout=5)
    s.settimeout(3)
    # Leer hasta prompt
    buf = b""
    for _ in range(10):
        try:
            chunk = s.recv(4096)
            if not chunk: break
            buf += chunk
        except: break
    s.close()
    return buf.decode('utf-8', errors='replace')


devices = [
    ("SW-SUC-01-CORE",  "192.168.38.128", 5009,  ["show vlan brief", "show running-config"]),
    ("SW-SUC-01-ACC1",  "192.168.38.128", 5013,  ["show vlan brief", "show running-config"]),
    ("R-SUC-01",        "192.168.38.128", 5003,  ["show running-config"]),
]

for name, host, port, commands in devices:
    print(f"\n=== {name} ===")
    for cmd in commands:
        s = socket.create_connection((host, port), timeout=5)
        s.settimeout(4)
        
        # Drain inicial + wait prompt
        buf = b""
        start = time.time()
        while b"#" not in buf and (time.time() - start) < 5:
            try:
                chunk = s.recv(4096)
                if not chunk: break
                buf += chunk
            except socket.timeout:
                continue
        
        # Enviar comando
        s.sendall(cmd.encode('ascii') + b"\n")
        out_buf = b""
        start = time.time()
        while b"#" not in out_buf and (time.time() - start) < 8:
            try:
                chunk = s.recv(4096)
                if not chunk: break
                out_buf += chunk
            except socket.timeout:
                continue
        
        output = out_buf.decode('utf-8', errors='replace').replace("#", "")
        if cmd == "show vlan brief":
            fname = f"{name}_vlan_brief.txt"
        else:
            fname = f"{name}_full_config.txt"
        
        with open(os.path.join(BACKUP_DIR, fname), "w", encoding="utf-8") as f:
            f.write(output.strip())
        print(f"  ✓ {cmd} → {fname} ({len(output)} chars)")
        s.close()
        time.sleep(0.5)

print("\n✓ Respaldos generados en backups/")
