# Personal Trainer Web | Gestión y seguimiento para gimnasios

Demostración de una plataforma web para entrenadores personales y gimnasios que reúne clientes, membresías, rutinas y seguimiento de medidas en una misma aplicación.

## El problema que aborda

La información de los clientes suele repartirse entre hojas de cálculo, mensajes y registros manuales. Esta aplicación muestra cómo centralizar la operación y ofrecer a cada cliente un espacio para consultar su entrenamiento y evolución.

## Funcionalidades

- Página de presentación, registro e inicio de sesión.
- Usuarios con roles de administración y cliente.
- Panel con indicadores de clientes, membresías y rutinas.
- Administración de clientes, tipos de membresía y fechas de vigencia.
- Constructor de rutinas con días, ejercicios, series y cargas.
- Registro y consulta de medidas corporales.
- Vistas para que el cliente consulte y ejecute su rutina.
- Borrado lógico en modelos de negocio y generación de datos de ejemplo.

Las pantallas son parte de una demo: los roles modelados no implican que todos los puntos de acceso hayan sido endurecidos para una instalación pública.

## Tecnologías

| Área | Implementación |
|---|---|
| Backend | Python y Django 6 |
| Datos locales | SQLite y migraciones Django |
| Interfaz | Plantillas Django, Tailwind CSS y Alpine.js |
| Servidor de aplicación | Gunicorn |
| Empaquetado | Docker con Python 3.12 |

## Estructura

| Ruta | Contenido |
|---|---|
| [administracion/](administracion/) | Usuario personalizado, formularios, paneles y vistas de la aplicación |
| [clientes/](clientes/) | Perfiles, membresías y medidas |
| [rutinas/](rutinas/) | Rutinas, días y ejercicios |
| [templates/](templates/) | Interfaz de administración y cliente |
| [gym_project/](gym_project/) | Configuración, rutas y WSGI |
| [Dockerfile](Dockerfile) | Imagen con Gunicorn |

El modelo de usuario utiliza correo como identificador. La base comparte un mecanismo de borrado lógico; las rutinas se componen de días y ejercicios asociados.

## Instalación local

Requisitos: Python 3.12 y las dependencias de [requirements.txt](requirements.txt). Utilizar una copia de desarrollo con datos ficticios.

```bash
git clone https://github.com/AmehdFM/PersonalTrainerWeb.git
cd PersonalTrainerWeb
python -m venv .venv
```

Activar el entorno según el sistema:

```bash
# Linux / macOS
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Después, desde la raíz:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/`. El comando `createsuperuser` permite crear una cuenta propia; no es necesario depender de las credenciales de una instancia de demostración.

### Datos de demostración

El repositorio incluye una base SQLite y un comando para añadir datos de ejemplo:

```bash
python manage.py populate_demo
```

Ejecutarlo únicamente sobre una copia de desarrollo: incorpora clientes, membresías y medidas a la base configurada. Algunas cuentas generadas usan contraseñas de demo, por lo que esos datos no corresponden a una instalación de producción.

### Rutas principales

| Ruta | Uso |
|---|---|
| `/` | Presentación |
| `/login/` | Acceso |
| `/dashboard/` | Panel de operación |
| `/dashboard/clientes/` | Clientes |
| `/dashboard/rutinas/` | Rutinas |
| `/clientes/` | Área del cliente |
| `/clientes/medidas/` | Medidas |
| `/admin/` | Administración Django |

## Docker

```bash
docker build -t personal-trainer-web .
docker run --rm -p 8000:8000 personal-trainer-web
```

El Dockerfile recopila estáticos y arranca Gunicorn, pero no ejecuta migraciones ni crea cuentas automáticamente. Para preparar una base nueva o conservar cambios entre contenedores se debe configurar la persistencia y ejecutar las migraciones correspondientes. Revisar los hosts permitidos en [settings.py](gym_project/settings.py) según el dominio utilizado.

## Recorrido sugerido

1. Crear una cuenta administrativa y cargar datos ficticios.
2. Consultar el panel y abrir la ficha de un cliente.
3. Revisar su membresía y registros de medidas.
4. Crear o modificar una rutina.
5. Acceder con un cliente de prueba y recorrer sus pantallas.

## Estado y próximos pasos

Demo funcional de producto, orientada a presentar flujos y capacidades de personalización. Los archivos `tests.py` de las aplicaciones todavía contienen las plantillas iniciales, sin pruebas implementadas.

Antes de operar con clientes reales: completar controles de acceso por vista, pruebas de los flujos principales y configuración de producción. La clave Django está en el código y `DEBUG` es verdadero por defecto; esa configuración debe sustituirse para un despliegue real. No se han medido ahorros de tiempo ni garantías de capacidad o disponibilidad.

## Autor

[Amehd Mendez](https://github.com/AmehdFM) · Aplicaciones de negocio e integración de sistemas.
