# Usar una imagen oficial de Python ligera
FROM python:3.12-slim

# Evitar que Python genere archivos .pyc y permitir que los logs lleguen directamente a la consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para algunas librerías de Python (como Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . /app/

# Recopilar archivos estáticos
RUN python manage.py collectstatic --noinput

# Exponer el puerto que usará Gunicorn
EXPOSE 8000

# Comando para ejecutar la aplicación con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "gym_project.wsgi:application"]
