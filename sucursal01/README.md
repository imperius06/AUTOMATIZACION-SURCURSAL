# Automatización y Auditoría de Sucursal 01

## Descripción

Este proyecto automatiza la configuración de la **Sucursal 01** mediante **Ansible** y realiza una auditoría de cumplimiento con **Python**.

### Componentes

- **Ansible**: Configura router y switches con VLANs, troncales y puertos de acceso. Obtiene respaldos de configuración.
- **Python**: Lee el diseño esperado (YAML) y la evidencia obtenida por Ansible. Determina si cada elemento cumple o no cumple.

## Estructura del Proyecto

```
sucursal01/
├── inventario.ini              # Inventario de dispositivos
├── vars/
│   └── config_sucursal.yaml    # Diseño esperado (VLANs, troncales, accesos)
├── playbook_configuracion.yml  # Configura todos los dispositivos
├── playbook_backup.yml         # Obtiene respaldos de configuración
├── auditoria.py                # Script de auditoría Python
├── backups/                    # Respaldos generados por Ansible
├── requirements.txt            # Dependencias Python
└── README.md                   # Este archivo
```

## Requisitos

### Ansible

```bash
pip install ansible netaddr
ansible-galaxy collection install cisco.ios
```

### Python (auditoría)

```bash
pip install pyyaml
```

## Uso

### 1. Configurar dispositivos

```bash
ansible-playbook -i inventario.ini playbook_configuracion.yml
```

### 2. Obtener respaldos

```bash
ansible-playbook -i inventario.ini playbook_backup.yml
```

### 3. Ejecutar auditoría

```bash
python auditoria.py
```

## Diseño de Red

### VLANs

| VLAN | Nombre | Red | Gateway |
|------|--------|-----|---------|
| 10 | USUARIOS_VLAN10 | 192.168.10.0/24 | 192.168.10.1 |
| 20 | USUARIOS_VLAN20 | 192.168.20.0/24 | 192.168.20.1 |
| 99 | GESTION | 192.168.99.0/24 | 192.168.99.1 |

### Direcciones de Gestión

| Dispositivo | IP |
|-------------|-----|
| SW-SUC-01-CORE | 192.168.99.2 |
| SW-SUC-01-ACC1 | 192.168.99.3 |

### Troncales

- **VLAN nativa**: 99
- **VLANs permitidas**: 10, 20, 99

## Evidencias

Los respaldos se guardan en `backups/`:
- `{hostname}_running.cfg` - Configuración running
- `{hostname}_vlan_brief.txt` - Output de `show vlan brief`
- `{hostname}_full_config.txt` - Configuración completa

La auditoría genera `reporte_auditoria.json` con el resumen de cumplimiento.
