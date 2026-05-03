# MuniMood — Guía de Instalación
## AlmaLinux + cPanel (VPS)

---

## Requisitos previos

- VPS con AlmaLinux 8 o 9
- cPanel instalado y acceso SSH root
- MySQL 8.x (ya incluido en cPanel)
- Python 3.11+ (instalado según los pasos a continuación)
- Al menos 2 GB de RAM (4 GB recomendados si usás pysentimiento)

---

## 1. Conectarse al VPS por SSH

```bash
ssh root@tu-ip-del-servidor
```

---

## 2. Instalar Python 3.11

AlmaLinux 8/9 trae Python 3.9 por defecto. Necesitamos 3.11+.

```bash
# Instalar repositorio de paquetes adicionales
dnf install -y epel-release
dnf install -y python3.11 python3.11-devel python3.11-pip

# Verificar versión
python3.11 --version
```

---

## 3. Instalar dependencias del sistema

```bash
dnf install -y gcc gcc-c++ make git libffi-devel openssl-devel
dnf install -y chromium chromium-headless     # Para scraping con Selenium (opcional)
```

---

## 4. Subir el código al servidor

**Opción A — Via Git:**
```bash
cd /home/tu_usuario_cpanel
git clone https://github.com/weenovate/munimood.git
cd munimood
```

**Opción B — Via cPanel File Manager:**
Subir el ZIP del proyecto y descomprimirlo en `/home/tu_usuario_cpanel/munimood/`

---

## 5. Crear entorno virtual Python

```bash
cd /home/tu_usuario_cpanel/munimood
python3.11 -m venv venv
source venv/bin/activate
```

---

## 6. Instalar dependencias Python

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Instalar motor de IA opcional (elegir UNO):

```bash
# Si querés usar OpenAI:
pip install openai==1.55.3

# Si querés usar Anthropic Claude:
pip install anthropic==0.39.0

# Si querés usar Google Gemini:
pip install google-generativeai==0.8.3

# Si querés usar pysentimiento (NLP local avanzado — requiere ~2GB RAM extra):
pip install pysentimiento==0.7.2 torch==2.2.0
```

---

## 7. Crear la base de datos MySQL en cPanel

1. Ingresar a cPanel → **Bases de datos MySQL**
2. Crear una nueva base de datos: `munimood`
3. Crear un usuario: `munimood_user` con contraseña segura
4. Otorgar **todos los privilegios** al usuario sobre la base `munimood`

---

## 8. Configurar variables de entorno

```bash
cd /home/tu_usuario_cpanel/munimood
cp .env.example .env
nano .env
```

### ⚠️ CAMPOS OBLIGATORIOS A MODIFICAR EN `.env`:

```
# Base de datos
DB_USER=munimood_user
DB_PASSWORD=la-contraseña-que-creaste
DB_NAME=cpanel_usuario_munimood   # cPanel prefija el nombre de DB con el usuario de cPanel

# Clave secreta JWT (generá una aleatoria)
SECRET_KEY=clave-muy-larga-y-aleatoria-aqui

# URL pública de la app
APP_URL=https://tu-dominio.com.ar

# ──────────────────────────────────────────────
# CREDENCIALES SMTP — MODIFICAR EN: /home/tu_usuario/munimood/.env
# ──────────────────────────────────────────────
SMTP_HOST=mail.tu-dominio.com.ar
SMTP_PORT=587
SMTP_USER=noreply@tu-dominio.com.ar
SMTP_PASSWORD=contraseña-del-correo
SMTP_FROM=noreply@tu-dominio.com.ar
SMTP_USE_TLS=true
```

> **Nota cPanel**: En cPanel, el nombre real de la base de datos tiene el prefijo del usuario de cPanel.
> Por ejemplo, si tu usuario es `municipio` y creaste la base `munimood`,
> el nombre real en MySQL será `municipio_munimood`.

---

## 9. Inicializar la base de datos

```bash
cd /home/tu_usuario_cpanel/munimood
source venv/bin/activate
python -m backend.init_db
```

Esto creará todas las tablas y el usuario inicial:
- **Usuario**: `muniadmin`
- **Contraseña**: `Ramallo2026`

> **Cambiá la contraseña después del primer login** en Configuración → Usuarios.

---

## 10. Probar el servidor localmente

```bash
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Abrí en el navegador: `http://tu-ip:8000`

---

## 11. Configurar el servicio como demonio (systemd)

Crear el archivo de servicio:

```bash
nano /etc/systemd/system/munimood.service
```

Contenido del archivo:

```ini
[Unit]
Description=MuniMood — Termómetro Político Municipal
After=network.target mysqld.service

[Service]
Type=simple
User=tu_usuario_cpanel
WorkingDirectory=/home/tu_usuario_cpanel/munimood
Environment=PATH=/home/tu_usuario_cpanel/munimood/venv/bin
ExecStart=/home/tu_usuario_cpanel/munimood/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Activar e iniciar el servicio:

```bash
systemctl daemon-reload
systemctl enable munimood
systemctl start munimood
systemctl status munimood
```

---

## 12. Configurar proxy inverso con cPanel (Apache)

Para acceder a la app desde tu dominio sin `:8000`, configurá un proxy en cPanel.

### Opción A — cPanel → Apache Handlers / .htaccess

Creá o editá el archivo `/home/tu_usuario_cpanel/public_html/.htaccess`:

```apache
RewriteEngine On
RewriteRule ^(.*)$ http://127.0.0.1:8000/$1 [P,L]

# Headers para proxy inverso
RequestHeader set X-Forwarded-Proto "https"
ProxyPreserveHost On
```

### Opción B — cPanel → Configuración del proxy inverso (cPanel 86+)

1. cPanel → **Dominios** → **Proxy Inverso**
2. Agregar: `URL = /` → `Destino = http://127.0.0.1:8000/`

---

## 13. SSL (HTTPS)

En cPanel → **SSL/TLS** → **Certificados SSL gratuitos (Let's Encrypt)**
Instalar el certificado para tu dominio.

Luego actualizar en `.env`:
```
APP_URL=https://tu-dominio.com.ar
CORS_ORIGINS=https://tu-dominio.com.ar
```

Reiniciar el servicio:
```bash
systemctl restart munimood
```

---

## Comandos útiles de administración

```bash
# Ver logs en tiempo real
journalctl -u munimood -f

# Reiniciar la app
systemctl restart munimood

# Ver estado
systemctl status munimood

# Detener
systemctl stop munimood

# Actualizar el código
cd /home/tu_usuario_cpanel/munimood
git pull
source venv/bin/activate
pip install -r backend/requirements.txt
systemctl restart munimood
```

---

## Archivo de credenciales SMTP

> **Las credenciales SMTP se configuran exclusivamente en:**
> ```
> /home/tu_usuario_cpanel/munimood/.env
> ```
> Variables a modificar: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_TLS`

---

## Credenciales iniciales

| Campo      | Valor           |
|------------|-----------------|
| Usuario    | `muniadmin`     |
| Contraseña | `Ramallo2026`   |
| URL        | `http://tu-ip:8000` o `https://tu-dominio.com.ar` |

> ⚠️ **Cambiar la contraseña después del primer acceso.**

---

## Troubleshooting frecuente

### La app no inicia
```bash
journalctl -u munimood -n 50
```

### Error de conexión a MySQL
Verificar credenciales en `.env` y que el usuario MySQL tenga permisos.

### El scraping falla
- Verificar que las librerías estén instaladas: `pip list | grep instaloader`
- Instagram requiere login para scraping masivo. Configurar `INSTAGRAM_USERNAME` en `.env`
- Los proxies de red social pueden bloquear el servidor VPS. En ese caso considerar usar las APIs oficiales.

### El mail no se envía
Verificar SMTP en `.env`. Probar con:
```python
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.tu-host.com', 587)
server.starttls()
server.login('usuario', 'contraseña')
print('OK')
"
```
