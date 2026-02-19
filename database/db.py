import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Render inyecta esto automáticamente
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Error DB: {e}")
        return None

def init_db():
    conn = get_connection()
    if not conn: return
    
    try:
        with conn.cursor() as cur:
            # 1. Usuarios
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    user_id BIGINT PRIMARY KEY,
                    nombre TEXT,
                    username TEXT,
                    rol TEXT DEFAULT 'admin',
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Eventos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS eventos (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) UNIQUE NOT NULL,
                    activo BOOLEAN DEFAULT TRUE
                );
            """)

            # 3. Catálogos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS catalogos (
                    id SERIAL PRIMARY KEY,
                    evento_id INTEGER REFERENCES eventos(id) ON DELETE CASCADE,
                    nombre VARCHAR(100) NOT NULL,
                    activo BOOLEAN DEFAULT TRUE
                );
            """)
            
            # 4. Productos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id SERIAL PRIMARY KEY,
                    catalogo_id INTEGER REFERENCES catalogos(id) ON DELETE CASCADE,
                    nombre VARCHAR(150) NOT NULL,
                    precio DECIMAL(10,2) NOT NULL,
                    activo BOOLEAN DEFAULT TRUE
                );
            """)

            # 5. Inventario
            cur.execute("""
                CREATE TABLE IF NOT EXISTS inventario (
                    id SERIAL PRIMARY KEY,
                    producto_id INTEGER REFERENCES productos(id) ON DELETE CASCADE,
                    talla VARCHAR(10) NOT NULL,
                    stock INTEGER DEFAULT 0,
                    UNIQUE(producto_id, talla)
                );
            """)
            
            # 6. VENTAS
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id SERIAL PRIMARY KEY,
                    producto_id INTEGER REFERENCES productos(id),
                    nombre_producto VARCHAR(150),
                    talla VARCHAR(10),
                    precio_venta DECIMAL(10,2),
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_id BIGINT
                );
            """)
            
            # 7. ENVÍOS (CREACIÓN)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS envios (
                    tracking_id VARCHAR(20) PRIMARY KEY,
                    venta_id INTEGER REFERENCES ventas(id),
                    cliente_nombre VARCHAR(100),
                    cc VARCHAR(50),
                    telefono VARCHAR(50),
                    ciudad VARCHAR(100),
                    depto VARCHAR(100),
                    direccion TEXT,
                    barrio VARCHAR(100),  -- Se agrega aquí para instalaciones nuevas
                    producto_info TEXT,
                    estado VARCHAR(50) DEFAULT 'Pendiente',
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # --- EL FIX MÁGICO ---
            # Esto asegura que la columna se agregue si la tabla ya existía sin ella
            cur.execute("""
                ALTER TABLE envios ADD COLUMN IF NOT EXISTS barrio VARCHAR(100);
            """)
            
            conn.commit()
            print("✅ Base de datos verificada y actualizada (Columna 'barrio' asegurada).")
            
    except Exception as e:
        print(f"❌ Error inicializando DB: {e}")
    finally:
        conn.close()