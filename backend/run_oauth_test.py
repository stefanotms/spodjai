import os
import sys
import time
import webbrowser
import threading
from dotenv import load_dotenv

# Agregar el directorio actual a la ruta para poder importar el módulo app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Cargar variables de entorno
load_dotenv()

from app.config import settings

def generate_ssl_cert(cert_path="cert.pem", key_path="key.pem"):
    try:
        from datetime import datetime, timedelta, timezone
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        print("[ERROR] No se pudo importar la librería 'cryptography'. Por favor, asegúrate de instalar las dependencias con: pip install -r requirements.txt")
        sys.exit(1)

    print("[INFO] Generando certificado SSL autofirmado para desarrollo local (https)...")
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Madrid"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Madrid"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Smart AI DJ Development"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.now(timezone.utc)
    ).not_valid_after(
        datetime.now(timezone.utc) + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost"), x509.DNSName("127.0.0.1")]),
        critical=False,
    ).sign(key, hashes.SHA256())

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print("[INFO] Certificado generado correctamente (cert.pem, key.pem)")

def main():
    if (settings.spotify_client_id == "PON_AQUI_TU_CLIENT_ID" or 
        settings.spotify_client_secret == "PON_AQUI_TU_CLIENT_SECRET"):
        print("=" * 70)
        print(" ¡ATENCIÓN! AÚN NO HAS CONFIGURADO LAS CREDENCIALES DE SPOTIFY ".center(70, "*"))
        print("=" * 70)
        print("Para probar este flujo, necesitas:")
        print("1. Ir a: https://developer.spotify.com/dashboard")
        print("2. Registrar una nueva app y obtener tu Client ID y Client Secret.")
        print("3. Agregar tu redirect URI a los 'Redirect URIs' en la app.")
        print("4. Editar el archivo 'backend/.env' con tus valores reales.")
        print("=" * 70)
        return

    # Comprobar si se requiere HTTPS
    is_https = settings.spotify_redirect_uri.startswith("https://")
    ssl_keyfile = None
    ssl_certfile = None

    if is_https:
        ssl_keyfile = "key.pem"
        ssl_certfile = "cert.pem"
        if not os.path.exists(ssl_keyfile) or not os.path.exists(ssl_certfile):
            generate_ssl_cert(ssl_certfile, ssl_keyfile)

    protocol = "https" if is_https else "http"
    host_for_browser = "127.0.0.1" if settings.host == "0.0.0.0" else settings.host
    login_url = f"{protocol}://{host_for_browser}:{settings.port}/login"

    def auto_open_browser():
        time.sleep(1.5)  # Esperar a que el servidor FastAPI esté listo
        print(f"\n[INFO] Abriendo el navegador automáticamente en: {login_url}\n")
        print("[NOTA] Si tu navegador muestra un aviso de advertencia de seguridad debido a que el certificado es autofirmado, haz clic en 'Avanzado' y luego en 'Continuar a localhost (no seguro)'. Esto es seguro y normal para desarrollo local.\n")
        webbrowser.open(login_url)

    threading.Thread(target=auto_open_browser, daemon=True).start()

    # Ejecutar el servidor uvicorn
    import uvicorn
    print(f"Iniciando el servidor de desarrollo en {protocol}://{settings.host}:{settings.port}")
    print("Presiona Ctrl+C para apagar el servidor.")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        reload=True
    )

if __name__ == "__main__":
    main()
