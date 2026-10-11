#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configurar dispositivos Sucursal 01 vía Telnet
===============================================
Conecta por telnet a cada dispositivo y aplica la configuración de VLANs,
troncales y subinterfaces según el diseño del PDF.

Uso: python configurar_dispositivos.py
"""

import socket
import time
import os

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

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
                if not chunk:
                    break
                self.buffer += chunk
            except socket.timeout:
                continue
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
        try:
            self.sock.close()
        except:
            pass


def configurar_switch_core():
    """Configura SW-SUC-01-CORE (puerto 5009)"""
    print("\n" + "="*60)
    print("CONFIGURANDO SW-SUC-01-CORE...")
    print("="*60)
    
    client = TelnetClient("192.168.38.128", 5009)
    
    # Leer prompt inicial
    client.read_until(b"#", timeout=3)
    
    commands = [
        "enable",
        "configure terminal",
        # VLANs
        "vlan 10",
        " name USUARIOS_VLAN10",
        "exit",
        "vlan 20",
        " name USUARIOS_VLAN20",
        "exit",
        "vlan 99",
        " name GESTION",
        "exit",
        # Troncal hacia R-SUC-01
        "interface GigabitEthernet0/0",
        " description Troncal hacia R-SUC-01",
        " switchport trunk native vlan 99",
        " switchport trunk allowed vlan 10,20,99",
        " switchport mode trunk",
        " no shutdown",
        "exit",
        # Troncal hacia SW-SUC-01-ACC1
        "interface GigabitEthernet1/2",
        " description Troncal hacia SW-SUC-01-ACC1",
        " switchport trunk native vlan 99",
        " switchport trunk allowed vlan 10,20,99",
        " switchport mode trunk",
        " no shutdown",
        "exit",
        # Puertos acceso VLAN 10
        "interface GigabitEthernet0/1",
        " description PC1 - VLAN 10",
        " switchport mode access",
        " switchport access vlan 10",
        " no shutdown",
        "exit",
        "interface GigabitEthernet0/2",
        " description PC2 - VLAN 10",
        " switchport mode access",
        " switchport access vlan 10",
        " no shutdown",
        "exit",
        # Puertos acceso VLAN 20
        "interface GigabitEthernet1/0",
        " description PC3 - VLAN 20",
        " switchport mode access",
        " switchport access vlan 20",
        " no shutdown",
        "exit",
        "interface GigabitEthernet1/1",
        " description PC4 - VLAN 20",
        " switchport mode access",
        " switchport access vlan 20",
        " no shutdown",
        "exit",
        # Puerto gestión VLAN 99
        "interface GigabitEthernet0/3",
        " description Gestion - VLAN 99",
        " switchport mode access",
        " switchport access vlan 99",
        " no shutdown",
        "exit",
        # IP gestión
        "interface Vlan99",
        " ip address 192.168.99.2 255.255.255.0",
        " no shutdown",
        "exit",
        "ip default-gateway 192.168.99.1",
        "end",
        "write memory",
    ]
    
    for cmd in commands:
        output = client.send_and_read(cmd)
        if "%" in output.lower() and "invalid" in output.lower():
            print(f"  ERROR en comando: {cmd}")
            print(f"  Respuesta: {output.strip()}")
    
    # Obtener show vlan brief
    vlan_output = client.send_and_read("show vlan brief", timeout=3)
    with open(os.path.join(BACKUP_DIR, "SW-SUC-01-CORE_vlan_brief.txt"), "w") as f:
        f.write(vlan_output)
    print("  ✓ VLANs configuradas y respaldo guardado")
    
    # Obtener running-config
    config_output = client.send_and_read("show running-config", timeout=5)
    with open(os.path.join(BACKUP_DIR, "SW-SUC-01-CORE_full_config.txt"), "w") as f:
        f.write(config_output)
    print("  ✓ Running-config respaldado")
    
    client.close()


def configurar_switch_acc1():
    """Configura SW-SUC-01-ACC1 (puerto 5013)"""
    print("\n" + "="*60)
    print("CONFIGURANDO SW-SUC-01-ACC1...")
    print("="*60)
    
    client = TelnetClient("192.168.38.128", 5013)
    client.read_until(b"#", timeout=3)
    
    commands = [
        "enable",
        "configure terminal",
        # VLANs
        "vlan 10",
        " name USUARIOS_VLAN10",
        "exit",
        "vlan 20",
        " name USUARIOS_VLAN20",
        "exit",
        "vlan 99",
        " name GESTION",
        "exit",
        # Troncal hacia CORE
        "interface GigabitEthernet0/0",
        " description Troncal hacia SW-SUC-01-CORE",
        " switchport trunk native vlan 99",
        " switchport trunk allowed vlan 10,20,99",
        " switchport mode trunk",
        " no shutdown",
        "exit",
        # Puertos acceso
        "interface GigabitEthernet0/1",
        " description PC5 - VLAN 10",
        " switchport mode access",
        " switchport access vlan 10",
        " no shutdown",
        "exit",
        "interface GigabitEthernet0/2",
        " description PC6 - VLAN 20",
        " switchport mode access",
        " switchport access vlan 20",
        " no shutdown",
        "exit",
        "interface GigabitEthernet0/3",
        " description PC8 - VLAN 99",
        " switchport mode access",
        " switchport access vlan 99",
        " no shutdown",
        "exit",
        # IP gestión
        "interface Vlan99",
        " ip address 192.168.99.3 255.255.255.0",
        " no shutdown",
        "exit",
        "ip default-gateway 192.168.99.1",
        "end",
        "write memory",
    ]
    
    for cmd in commands:
        output = client.send_and_read(cmd)
        if "%" in output.lower() and "invalid" in output.lower():
            print(f"  ERROR en comando: {cmd}")
    
    vlan_output = client.send_and_read("show vlan brief", timeout=3)
    with open(os.path.join(BACKUP_DIR, "SW-SUC-01-ACC1_vlan_brief.txt"), "w") as f:
        f.write(vlan_output)
    print("  ✓ VLANs configuradas y respaldo guardado")
    
    config_output = client.send_and_read("show running-config", timeout=5)
    with open(os.path.join(BACKUP_DIR, "SW-SUC-01-ACC1_full_config.txt"), "w") as f:
        f.write(config_output)
    print("  ✓ Running-config respaldado")
    
    client.close()


def configurar_router():
    """Configura R-SUC-01 (puerto 5003)"""
    print("\n" + "="*60)
    print("CONFIGURANDO R-SUC-01...")
    print("="*60)
    
    client = TelnetClient("192.168.38.128", 5003)
    client.read_until(b"#", timeout=3)
    
    commands = [
        "enable",
        "configure terminal",
        # Interfaz física
        "interface GigabitEthernet0/0",
        " description Enlace troncal hacia SW-SUC-01-CORE",
        " no shutdown",
        "exit",
        # Subinterface VLAN 10
        "interface GigabitEthernet0/0.10",
        " description Subinterface VLAN 10 - USUARIOS",
        " encapsulation dot1Q 10",
        " ip address 192.168.10.1 255.255.255.0",
        "exit",
        # Subinterface VLAN 20
        "interface GigabitEthernet0/0.20",
        " description Subinterface VLAN 20 - USUARIOS",
        " encapsulation dot1Q 20",
        " ip address 192.168.20.1 255.255.255.0",
        "exit",
        # Subinterface VLAN 99 nativa
        "interface GigabitEthernet0/0.99",
        " description Subinterface VLAN 99 - GESTION",
        " encapsulation dot1Q 99 native",
        " ip address 192.168.99.1 255.255.255.0",
        "exit",
        "end",
        "write memory",
    ]
    
    for cmd in commands:
        output = client.send_and_read(cmd)
        if "%" in output.lower() and "invalid" in output.lower():
            print(f"  ERROR en comando: {cmd}")
    
    config_output = client.send_and_read("show running-config", timeout=5)
    with open(os.path.join(BACKUP_DIR, "R-SUC-01_full_config.txt"), "w") as f:
        f.write(config_output)
    print("  ✓ Subinterfaces configuradas y respaldo guardado")
    
    client.close()


if __name__ == "__main__":
    print("="*60)
    print("CONFIGURACIÓN AUTOMÁTICA - SUCURSAL 01")
    print("="*60)
    
    try:
        configurar_switch_core()
    except Exception as e:
        print(f"  ✗ Error en SW-SUC-01-CORE: {e}")
    
    try:
        configurar_switch_acc1()
    except Exception as e:
        print(f"  ✗ Error en SW-SUC-01-ACC1: {e}")
    
    try:
        configurar_router()
    except Exception as e:
        print(f"  ✗ Error en R-SUC-01: {e}")
    
    print("\n" + "="*60)
    print("CONFIGURACIÓN COMPLETADA")
    print(f"Respaldos guardados en: {os.path.abspath(BACKUP_DIR)}")
    print("="*60)
