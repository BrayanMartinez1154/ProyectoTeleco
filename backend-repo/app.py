import os
from flask import Flask, request, jsonify
from datetime import datetime
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError
import json
from flask_cors import CORS

# --- Configuración ---
app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas y orígenes

# Contraseña hardcodeada para el endpoint /logins (como requiere el examen)
ADMIN_PASSWORD = "micontrasenaSuperSegura123"

# Configuración de Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "datos-login"
BLOB_NAME = "logins.json"

# --- Funciones Auxiliares para Blob Storage ---

def get_blob_service_client():
    if not AZURE_STORAGE_CONNECTION_STRING:
        raise ValueError("La cadena de conexión AZURE_STORAGE_CONNECTION_STRING no está configurada.")
    return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

def read_logins_from_blob():
    """Lee los datos de login del blob. Devuelve una lista vacía si el blob no existe o está vacío."""
    try:
        blob_service_client = get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
        
        if not blob_client.exists():
            # Crear el contenedor si no existe
            try:
                container_client = blob_service_client.get_container_client(CONTAINER_NAME)
                if not container_client.exists():
                    container_client.create_container()
                    app.logger.info(f"Contenedor '{CONTAINER_NAME}' creado.")
            except Exception as e:
                app.logger.error(f"Error al crear el contenedor '{CONTAINER_NAME}': {e}")
            return []

        downloader = blob_client.download_blob(max_concurrency=1, encoding='UTF-8')
        blob_data = downloader.readall()
        if blob_data:
            return json.loads(blob_data)
        return []
    except ResourceNotFoundError:
        app.logger.info(f"El blob '{BLOB_NAME}' no fue encontrado. Se creará uno nuevo al primer login.")
        return []
    except json.JSONDecodeError:
        app.logger.error(f"Error al decodificar JSON del blob '{BLOB_NAME}'. Se devolverá una lista vacía.")
        return []
    except Exception as e:
        app.logger.error(f"Error al leer del blob: {e}")
        return []

def write_logins_to_blob(data):
    """Escribe los datos de login al blob."""
    try:
        blob_service_client = get_blob_service_client()
        
        # Crear el contenedor si no existe
        try:
            container_client = blob_service_client.get_container_client(CONTAINER_NAME)
            if not container_client.exists():
                container_client.create_container()
                app.logger.info(f"Contenedor '{CONTAINER_NAME}' creado.")
        except Exception as e:
            app.logger.error(f"Error crítico: No se pudo crear o acceder al contenedor '{CONTAINER_NAME}': {e}")
            raise

        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
        blob_client.upload_blob(json.dumps(data, indent=4), overwrite=True, encoding='UTF-8')
        app.logger.info(f"Datos escritos correctamente en el blob '{BLOB_NAME}'.")
    except Exception as e:
        app.logger.error(f"Error al escribir en el blob: {e}")
        raise

# --- Endpoints de la API (según requerimientos del examen) ---

@app.route('/')
def home():
    return "API de Autenticación funcionando correctamente."

@app.route('/login', methods=['POST'])
def login():
    """
    POST /login: Recibe y guarda los datos enviados (usuario, contraseña, fecha y hora del login)
    """
    try:
        data = request.get_json()
        if not data or 'usuario' not in data or 'contrasena' not in data:
            return jsonify({"mensaje": "Faltan los campos 'usuario' o 'contrasena'"}), 400

        usuario = data['usuario']
        contrasena = data['contrasena']
        fecha_hora = datetime.now().isoformat()

        nuevo_login = {
            "usuario": usuario,
            "contrasena": contrasena,
            "fecha_hora": fecha_hora
        }

        logins = read_logins_from_blob()
        logins.append(nuevo_login)
        write_logins_to_blob(logins)

        return jsonify({"mensaje": "Login registrado con éxito", "datos": nuevo_login}), 201

    except ValueError as ve:
        app.logger.error(f"Error de configuración: {ve}")
        return jsonify({"mensaje": f"Error de configuración del servidor: {ve}"}), 500
    except Exception as e:
        app.logger.error(f"Error en el endpoint /login: {e}")
        return jsonify({"mensaje": f"Error interno del servidor: {e}"}), 500

@app.route('/logins', methods=['GET'])
def get_logins():
    """
    GET /logins: Devuelve todos los registros almacenados.
    Este endpoint está protegido con una contraseña fija hardcodeada.
    """
    # Protección del endpoint con contraseña hardcodeada (como requiere el examen)
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f"Bearer {ADMIN_PASSWORD}":
        return jsonify({"mensaje": "No autorizado. Se requiere token de administrador."}), 401
    
    try:
        logins = read_logins_from_blob()
        return jsonify(logins), 200
    except ValueError as ve:
        app.logger.error(f"Error de configuración: {ve}")
        return jsonify({"mensaje": f"Error de configuración del servidor: {ve}"}), 500
    except Exception as e:
        app.logger.error(f"Error en el endpoint /logins: {e}")
        return jsonify({"mensaje": f"Error interno del servidor al leer los logs: {e}"}), 500

if __name__ == '__main__':
    # Configuración para Azure App Service
    port = int(os.environ.get("PORT", 8000))
    # debug=False para producción en Azure
    app.run(host='0.0.0.0', port=port, debug=False)