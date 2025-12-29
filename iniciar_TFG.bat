@echo off
SET PYTHON_PATH=%~dp0tfg_backend\install_deps.py
SET BACKEND_PATH=%~dp0tfg_backend
SET FRONTEND_PATH=%~dp0tfg_frontend

ECHO --- Verificando e Instalando Dependencias ---
REM Ejecuta el script de Python para instalar dependencias.
REM Se usa CALL para que el script .bat espere a que Python termine.
call python "%PYTHON_PATH%"

IF ERRORLEVEL 1 (
    ECHO ERROR: La instalacion de dependencias Python falló.
    PAUSE
    EXIT /B 1
)
ECHO ----------------------------------------------

ECHO Iniciando el Backend (Servidor Django) en puerto 8000...

REM Inicia el Backend en una nueva ventana
start "Backend TFG (Django)" cmd /k "cd /d "%BACKEND_PATH%" && python manage.py runserver"

ECHO Esperando que el Backend se estabilice...

REM Espera 5 segundos para que el backend empiece a arrancar
timeout /t 5 /nobreak > nul

ECHO Iniciando el Frontend (Servidor React) en puerto 3000...

REM Inicia el Frontend en una nueva ventana (esto abrira el navegador en :3000)
start "Frontend TFG (React)" cmd /k "cd /d "%FRONTEND_PATH%" && npm start"

ECHO Abriendo Panel de Administracion...

REM Abre una nueva pestaña/ventana del navegador directamente en el admin
start http://127.0.0.1:8000/admin/

ECHO ¡Ambos servidores estan arrancando y el Admin ha sido abierto!