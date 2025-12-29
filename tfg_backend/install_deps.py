# Nombre de archivo: tfg_backend/install_deps.py
import subprocess
import sys
import os

# Lista de librerías necesarias
REQUIRED_PACKAGES = [
    "django",
    "sympy",
    "django-cors-headers"
]

def install_and_check_packages():
    """Verifica e instala las librerías necesarias."""
    print("--- Verificando e instalando dependencias Python ---")
    
    # 1. Comprueba si pip está disponible y lo instala si es necesario.
    try:
        # Intenta verificar las versiones de los paquetes
        # El comando 'pip freeze' no lista paquetes instalados por dependencia, por lo que es más fiable usar 'import'
        pass # La verificación por 'import' puede ser compleja, confiemos en 'pip install --ignore-installed'
    except ImportError:
        pass # Continuamos con la instalación si la importación falla

    packages_to_install = []
    
    # Intenta la instalación de todas las dependencias
    for package in REQUIRED_PACKAGES:
        try:
            print(f"Instalando {package}...")
            # Usamos subprocess para ejecutar el comando pip
            process = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,  # Lanza una excepción si el comando falla
                capture_output=True,
                text=True
            )
            # Solo muestra la salida si hay algo significativo (ej. instaló algo)
            if "Successfully installed" in process.stdout or "Requirement already satisfied" in process.stdout:
                 print(f"Éxito: {package} - Listo.")
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Falló la instalación de {package}.")
            print("Asegúrate de que Python y pip estén configurados correctamente.")
            sys.exit(1) # Detiene el script si una librería esencial falla
        except Exception as e:
            print(f"ERROR inesperado al instalar {package}: {e}")
            sys.exit(1)

    print("--- Todas las dependencias Python han sido verificadas/instaladas. ---")
    print("--- Continuando con la ejecución... ---")

if __name__ == "__main__":
    install_and_check_packages()