# database/db.py
import os
import psycopg2

# Render inyectará esta variable automáticamente
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Error conectando a NeonDB: {e}")
        return None

def init_db():
    """Inicializa las tablas si no existen"""
    conn = get_connection()
    if not conn: return
    
    with conn.cursor() as cur:
        # Tabla Catálogos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS catalogos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) UNIQUE NOT NULL,
                activo BOOLEAN DEFAULT TRUE
            );
        """)
        
        # Tabla Productos (Relación 1 a muchos con catálogos)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                catalogo_id INTEGER REFERENCES catalogos(id) ON DELETE CASCADE,
                nombre VARCHAR(150) NOT NULL,
                precio DECIMAL(10,2) NOT NULL,
                imagen_url TEXT
            );
        """)

        # Tabla Inventario/Stock (Tallas)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER REFERENCES productos(id) ON DELETE CASCADE,
                talla VARCHAR(10) NOT NULL, -- S, M, L, XL
                stock INTEGER DEFAULT 0
            );
        """)
        
        conn.commit()
    conn.close()
    print("✅ Tablas de base de datos verificadas.")