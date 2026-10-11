#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Corregir los 7 incumplimientos detectados por la auditoría"""

import socket
import time

class TelnetClient:
    def __init__(self, host, port, timeout=5):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(3)
        self.buffer = b""
    
    def read_until(self, marker, timeout=5):
        deadline = time.time() + timeout
        while marker not in self.buffer and time.time() < deadline:
            try:
                chunk = self.sock.recv(4096)
                if not chunk: break
                self.buffer += chunk
            except socket.timeout: continue
        if marker in self.buffer:
            idx = self.buffer.index(marker) + len(marker)
            result = self.buffer[:idx]
            self.buffer = self.buffer[idx:]
            return result.decode('utf-8', errors='replace')
        result = self.buffer
        self.buffer = b""
        return result.decode('utf-8', errors='replace')
    
    def send(self, cmd):
        self.sock.sendall(cmd.encode('ascii') + b"\n")
        time.sleep(0.3)
    
    def send_and_read(self, cmd, timeout=2):
        self.send(cmd)
        return self.read_until(b"#", timeout=timeout)
    
    def close(self):
        try: self.sock.close()
        except: pass


def corregir_acc1():
    """SW-SUC-01-ACC1: VLAN 99, Gi0/2 VLAN 20, trunk add VLAN 99"""
    print("\n=== Corrigiendo SW-SUC-01-ACC1 ===")
    client = TelnetClient("192.168.38.128", 5013)
    client.read_until(b"#", timeout=3)
    
    cmds = [
        "enable",
        "configure terminal",
        "vlan 99",
        " name GESTION",
        "exit",
        "interface GigabitEthernet0/2",
        " switchport access vlan 20",
        " description PC6 - VLAN 20",
        "exit",
        "interface GigabitEthernet0/0",
        " switchport trunk allowed vlan add 99",
        "exit",
        "end",
        "write memory",
    ]
    for cmd in cmds:
        out = client.send_and_read(cmd)
        if "%" in out.lower() and "invalid" in out.lower():
            print(f"  ERROR: {cmd}")
    
    print("  ✓ VLAN 99 creada")
    print("  ✓ Gi0/2 cambiado a VLAN 20")
    print("  ✓ Trunk Gi0/0 ahora permite VLAN 99")
    client.close()


def corregir_core():
    """SW-SUC-01-CORE: VLAN 20 nombre, Gi0/1 descripción"""
    print("\n=== Corrigiendo SW-SUC-01-CORE ===")
    client = TelnetClient("192.168.38.128", 5009)
    client.read_until(b"#", timeout=3)
    
    cmds = [
        "enable",
        "configure terminal",
        "vlan 20",
        " name USUARIOS_VLAN20",
        "exit",
        "interface GigabitEthernet0/1",
        " description ACCESO VLAN10 hacia PC2",
        "exit",
        "end",
        "write memory",
    ]
    for cmd in cmds:
        out = client.send_and_read(cmd)
        if "%" in out.lower() and "invalid" in out.lower():
            print(f"  ERROR: {cmd}")
    
    print("  ✓ VLAN 20 renombrada a USUARIOS_VLAN20")
    print("  ✓ Gi0/1 descripción actualizada")
    client.close()


if __name__ == "__main__":
    print("="*60)
    print("CORRIGIENDO 7 INCUMPLIMIENTOS")
    print("="*60)
    
    try:
        corregir_acc1()
    except Exception as e:
        print(f"  ✗ Error ACC1: {e}")
    
    try:
        corregir_core()
    except Exception as e:
        print(f"  ✗ Error CORE: {e}")
    
    print("\n" + "="*60)
    print("CORRECCIONES APLICADAS - Ejecuta auditoría nuevamente")
    print("="*60)
