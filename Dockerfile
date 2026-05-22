FROM python:3.13-slim

# No generar .pyc y salida sin buffer (mejores logs en contenedor).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalamos dependencias primero para aprovechar la caché de capas.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiamos el código de la aplicación.
COPY app ./app

# Usuario sin privilegios.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# /Users/yeison/tablo/backend/Dockerfile

# ... (código existente) ...

# Modifica el CMD final
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]

