#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Auditoría de configuración - Sucursal 01
=========================================
Lee el diseño esperado desde YAML y compara con la evidencia obtenida por Ansible.
Determina si cada elemento cumple o no cumple con el diseño.

Uso: python auditoria_sucursal.py
"""

import yaml
import json
import os
from pathlib import Path
from typing import Any, Dict, List

# Rutas
BACKUP_DIR = Path("./backups")
VARS_FILE = Path("./vars/config_sucursal.yaml")

class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AMARILLO = '\033[93m'
    AZUL = '\033[94m'
    RESET = '\033[0m'
    NEGRITA = '\033[1m'

def cargar_yaml(ruta: Path) -> Dict[str, Any]:
    """Carga archivo YAML con el diseño esperado."""
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró {ruta}")
    with open(ruta, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def leer_evidencia(ruta: Path) -> str:
    """Lee archivo de evidencia (texto plano)."""
    if not ruta.exists():
        return None
    with open(ruta, 'r', encoding='utf-8') as f:
        return f.read()

def parsear_vlan_brief(contenido: str) -> Dict[int, Dict]:
    """
    Parsea output de 'show vlan brief' de Cisco IOS.
    Devuelve dict: {vlan_id: {'name': str, 'status': str, 'ports': list}}
    """
    vlans = {}
    if not contenido:
        return vlans
    
    lines = contenido.strip().split('\n')
    for line in lines:
        # Formato típico: 10   VLAN0010                         active    Gi0/1, Gi0/2
        parts = line.split()
        if len(parts) >= 3 and parts[0].isdigit():
            vlan_id = int(parts[0])
            name = parts[1] if len(parts) > 1 else f"VLAN{vlan_id}"
            status = parts[2] if len(parts) > 2 else "active"
            ports = parts[3].split(',') if len(parts) > 3 else []
            vlans[vlan_id] = {'name': name, 'status': status, 'ports': ports}
    
    return vlans

def parsear_running_config(contenido: str) -> Dict[str, Any]:
    """
    Parsea configuración running para extraer:
    - Interfaces y sus modos (access/trunk)
    - VLANs nativas y permitidas en trunks
    - Descripciones
    """
    config = {'interfaces': {}, 'vlans': [], 'trunks': {}, 'access': {}}
    if not contenido:
        return config

    lines = contenido.split('\n')
    current_interface = None

    for line in lines:
        line = line.strip()

        # Detectar interfaz (solo GigabitEthernet)
        if line.startswith('interface GigabitEthernet'):
            current_interface = line.split()[1]
            config['interfaces'][current_interface] = {
                'description': '', 
                'mode': 'access',  # default
                'vlan': None, 
                'trunk': {'native': None, 'allowed': []}
            }
            continue

        if not current_interface or not current_interface.startswith('GigabitEthernet'):
            continue

        # Descripción
        if line.startswith('description '):
            config['interfaces'][current_interface]['description'] = ' '.join(line.split()[1:])

        # Modo switchport (flexible matching)
        if line.startswith('switchport mode trunk'):
            config['interfaces'][current_interface]['mode'] = 'trunk'
            if current_interface not in config['trunks']:
                config['trunks'][current_interface] = {}
        elif line.startswith('switchport mode access'):
            config['interfaces'][current_interface]['mode'] = 'access'

        # VLAN nativa en trunk (antes o después de 'mode trunk')
        if line.startswith('switchport trunk native vlan'):
            vlan_id = int(line.split()[-1])
            config['interfaces'][current_interface]['trunk']['native'] = vlan_id
            if current_interface in config['trunks']:
                config['trunks'][current_interface]['native'] = vlan_id

        # VLANs permitidas (antes o después de 'mode trunk')
        if line.startswith('switchport trunk allowed vlan'):
            parts = line.split('vlan', 1)
            if len(parts) > 1:
                vlans_str = parts[1].strip()
                # Remover 'add' si está presente
                vlans_str = vlans_str.replace('add ', '').replace('remove ', '')
                vlans_list = [int(v) for v in vlans_str.split(',') if v.isdigit()]
                config['interfaces'][current_interface]['trunk']['allowed'] = vlans_list
                if current_interface in config['trunks']:
                    config['trunks'][current_interface]['allowed'] = vlans_list

        # VLAN de acceso
        if line.startswith('switchport access vlan'):
            vlan_id = int(line.split()[-1])
            config['interfaces'][current_interface]['vlan'] = vlan_id
            config['access'][current_interface] = vlan_id

        # VLANs creadas (fuera de interfaces)
        if line.startswith('vlan ') and not current_interface:
            vlan_id = int(line.split()[-1])
            if vlan_id not in config['vlans']:
                config['vlans'].append(vlan_id)

    return config

def auditar_vlans(diseño: Dict, evidencia: Dict) -> List[Dict]:
    """Audita existencia y nombre de VLANs."""
    resultados = []
    vlans_esperadas = {v['id']: v['name'] for v in diseño.get('vlans', [])}
    vlans_encontradas = evidencia.get('vlans', [])
    
    print(f"\n{Colores.AZUL}{'='*60}{Colores.RESET}")
    print(f"{Colores.NEGRITA}AUDITORÍA DE VLANs{Colores.RESET}")
    print(f"{Colores.AZUL}{'='*60}{Colores.RESET}")
    
    for vlan_id, nombre_esperado in vlans_esperadas.items():
        if vlan_id in vlans_encontradas:
            resultados.append({
                'elemento': f'VLAN {vlan_id}',
                'cumple': True,
                'esperado': nombre_esperado,
                'encontrado': nombre_esperado,
                'nota': 'VLAN existe'
            })
            print(f"{Colores.VERDE}✓{Colores.RESET} VLAN {vlan_id} ({nombre_esperado}) - {Colores.VERDE}CUMPLE{Colores.RESET}")
        else:
            resultados.append({
                'elemento': f'VLAN {vlan_id}',
                'cumple': False,
                'esperado': nombre_esperado,
                'encontrado': 'No encontrada',
                'nota': 'VLAN no existe'
            })
            print(f"{Colores.ROJO}✗{Colores.RESET} VLAN {vlan_id} ({nombre_esperado}) - {Colores.ROJO}NO CUMPLE{Colores.RESET}")
    
    return resultados

def auditar_troncales(diseño: Dict, evidencia: Dict) -> List[Dict]:
    """Audita configuración de enlaces troncales."""
    resultados = []
    trunks_diseño = diseño.get('trunks', {})
    trunks_evidencia = evidencia.get('trunks', {})
    
    print(f"\n{Colores.AZUL}{'='*60}{Colores.RESET}")
    print(f"{Colores.NEGRITA}AUDITORÍA DE ENLACES TRONCALES{Colores.RESET}")
    print(f"{Colores.AZUL}{'='*60}{Colores.RESET}")
    
    for switch, interfaces in trunks_diseño.items():
        for intf, config in interfaces.items():
            key = f"{switch}:{intf}"
            trunk_real = trunks_evidencia.get(intf, {})
            
            # Verificar VLAN nativa
            nativa_esperada = config.get('nativa')
            nativa_real = trunk_real.get('native')
            
            if nativa_real == nativa_esperada:
                print(f"{Colores.VERDE}✓{Colores.RESET} {key} - VLAN nativa {nativa_esperada} - {Colores.VERDE}CUMPLE{Colores.RESET}")
                resultados.append({'elemento': f'{key} native', 'cumple': True})
            else:
                print(f"{Colores.ROJO}✗{Colores.RESET} {key} - VLAN nativa: esperado {nativa_esperada}, encontrado {nativa_real} - {Colores.ROJO}NO CUMPLE{Colores.RESET}")
                resultados.append({'elemento': f'{key} native', 'cumple': False, 'nota': f'Esperado {nativa_esperada}, encontrado {nativa_real}'})
            
            # Verificar VLANs permitidas
            permitidas_esperadas = set(config.get('permitidas', []))
            permitidas_reales = set(trunk_real.get('allowed', []))
            
            if permitidas_reales >= permitidas_esperadas:
                print(f"{Colores.VERDE}✓{Colores.RESET} {key} - VLANs permitidas {permitidas_esperadas} - {Colores.VERDE}CUMPLE{Colores.RESET}")
                resultados.append({'elemento': f'{key} allowed', 'cumple': True})
            else:
                faltantes = permitidas_esperadas - permitidas_reales
                print(f"{Colores.ROJO}✗{Colores.RESET} {key} - Faltan VLANs permitidas: {faltantes} - {Colores.ROJO}NO CUMPLE{Colores.RESET}")
                resultados.append({'elemento': f'{key} allowed', 'cumple': False, 'nota': f'Faltan: {faltantes}'})
    
    return resultados

def auditar_acceso(diseño: Dict, evidencia: Dict) -> List[Dict]:
    """Audita asignación de puertos de acceso a VLANs."""
    resultados = []
    acceso_diseño = diseño.get('acceso', {})
    acceso_evidencia = evidencia.get('access', {})
    
    print(f"\n{Colores.AZUL}{'='*60}{Colores.RESET}")
    print(f"{Colores.NEGRITA}AUDITORÍA DE PUERTOS DE ACCESO{Colores.RESET}")
    print(f"{Colores.AZUL}{'='*60}{Colores.RESET}")
    
    for switch, interfaces in acceso_diseño.items():
        for intf, config in interfaces.items():
            key = f"{switch}:{intf}"
            vlan_esperada = config.get('vlan')
            vlan_real = acceso_evidencia.get(intf)
            
            if vlan_real == vlan_esperada:
                print(f"{Colores.VERDE}✓{Colores.RESET} {key} - VLAN {vlan_esperada} - {Colores.VERDE}CUMPLE{Colores.RESET}")
                resultados.append({'elemento': key, 'cumple': True})
            else:
                print(f"{Colores.ROJO}✗{Colores.RESET} {key} - Esperado VLAN {vlan_esperada}, encontrado {vlan_real} - {Colores.ROJO}NO CUMPLE{Colores.RESET}")
                resultados.append({'elemento': key, 'cumple': False, 'nota': f'Esperado VLAN {vlan_esperada}, encontrado {vlan_real}'})
    
    return resultados

def generar_reporte(resultados: List[Dict], output_file: str = "reporte_auditoria.json"):
    """Genera reporte JSON con todos los resultados."""
    total = len(resultados)
    cumplidos = sum(1 for r in resultados if r.get('cumple', False))
    fallidos = total - cumplidos
    porcentaje = (cumplidos / total * 100) if total > 0 else 0
    
    reporte = {
        'resumen': {
            'total': total,
            'cumplidos': cumplidos,
            'fallidos': fallidos,
            'porcentaje': f"{porcentaje:.1f}%"
        },
        'resultados': resultados
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Colores.AZUL}{'='*60}{Colores.RESET}")
    print(f"{Colores.NEGRITA}RESUMEN{Colores.RESET}")
    print(f"{Colores.AZUL}{'='*60}{Colores.RESET}")
    print(f"Total elementos auditados: {total}")
    print(f"{Colores.VERDE}Cumplidos: {cumplidos}{Colores.RESET}")
    print(f"{Colores.ROJO}Fallidos: {fallidos}{Colores.RESET}")
    print(f"Porcentaje de cumplimiento: {Colores.NEGRITA}{porcentaje:.1f}%{Colores.RESET}")
    print(f"\nReporte guardado en: {output_file}")
    
    return reporte

def main():
    print(f"{Colores.NEGRITA}{'='*60}{Colores.RESET}")
    print(f"{Colores.NEGRITA}AUDITORÍA DE CONFIGURACIÓN - SUCURSAL 01{Colores.RESET}")
    print(f"{Colores.NEGRITA}{'='*60}{Colores.RESET}")
    
    # Cargar diseño esperado
    try:
        diseño = cargar_yaml(VARS_FILE)
        print(f"Diseño cargado desde: {VARS_FILE}")
    except FileNotFoundError as e:
        print(f"{Colores.ROJO}ERROR: {e}{Colores.RESET}")
        return
    
    # Buscar evidencia
    vlans_evidencia = {}
    running_evidencia = {}
    
    for backup_file in BACKUP_DIR.glob("*_vlan_brief.txt"):
        contenido = leer_evidencia(backup_file)
        if contenido:
            switch_name = backup_file.stem.replace('_vlan_brief', '')
            vlans_evidencia[switch_name] = parsear_vlan_brief(contenido)
            print(f"VLANs cargadas de: {backup_file.name}")
    
    for config_file in BACKUP_DIR.glob("*_full_config.txt"):
        contenido = leer_evidencia(config_file)
        if contenido:
            switch_name = config_file.stem.replace('_full_config', '')
            running_evidencia[switch_name] = parsear_running_config(contenido)
            print(f"Configuración cargada de: {config_file.name}")
    
    if not vlans_evidencia and not running_evidencia:
        print(f"{Colores.ROJO}ADVERTENCIA: No se encontraron archivos de evidencia en {BACKUP_DIR}{Colores.RESET}")
        print(f"Ejecuta primero el playbook_backup.yml para generar los respaldos.")
        return
    
    # Ejecutar auditorías
    todos_resultados = []
    
    # Auditar VLANs
    for switch, vlans in vlans_evidencia.items():
        evidencia_plana = {'vlans': list(vlans.keys())}
        todos_resultados.extend(auditar_vlans(diseño, evidencia_plana))
    
    # Auditar troncales
    for switch, config in running_evidencia.items():
        todos_resultados.extend(auditar_troncales(diseño, config))
    
    # Auditar accesos
    for switch, config in running_evidencia.items():
        todos_resultados.extend(auditar_acceso(diseño, config))
    
    # Generar reporte
    generar_reporte(todos_resultados)

if __name__ == "__main__":
    main()
