#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# 1. Crear superusuario 'admin' si no existe
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin1234')"

# 2. EJECUTAR ROBOT DE IMPORTACIÓN (NUEVO)
python manage.py cargar_ejercicios