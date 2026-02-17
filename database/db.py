import os
import psycopg2
from psycopg2.extras import RealDictCursor

# En Render, DATABASE_URL se inyecta automáticamente
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Establece conexión con NeonDB."""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Error conectando a DB: {e}")
        return None

def init_db():
    """Crea las tablas necesarias si no existen."""
    conn = get_connection()
    if not conn: return
    
    with conn.cursor() as cur:
        # 1. Tabla Usuarios (Admin/Clientes)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                user_id BIGINT PRIMARY KEY,
                nombre TEXT,
                username TEXT,
                rol TEXT DEFAULT 'cliente', -- 'admin' o 'cliente'
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Tabla Catálogos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS catalogos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) UNIQUE NOT NULL,
                activo BOOLEAN DEFAULT TRUE
            );
        """)
        
        # 3. Tabla Productos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                catalogo_id INTEGER REFERENCES catalogos(id) ON DELETE CASCADE,
                nombre VARCHAR(150) NOT NULL,
                precio DECIMAL(10,2) NOT NULL,
                activo BOOLEAN DEFAULT TRUE
            );
        """)

        # 4. Tabla Inventario (Tallas)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER REFERENCES productos(id) ON DELETE CASCADE,
                talla VARCHAR(10) NOT NULL, -- S, M, L, XL
                stock INTEGER DEFAULT 0,
                UNIQUE(producto_id, talla)
            );
        """)
        
        # 5. Tabla Envíos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS envios (
                tracking_id VARCHAR(20) PRIMARY KEY,
                cliente_nombre VARCHAR(100),
                direccion TEXT,
                producto_info TEXT,
                estado VARCHAR(50) DEFAULT 'Pendiente', -- Pendiente, En Camino, Entregado
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente.")