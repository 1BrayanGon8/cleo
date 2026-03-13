import sqlite3

def crear_base_datos():
    conexion = sqlite3.connect("cleopatra.db")
    cursor = conexion.cursor()

    # TABLA CATEGORIAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    )
    """)

    # TABLA PRODUCTOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        precio REAL NOT NULL,
        disponible INTEGER DEFAULT 1,
        personalizable INTEGER DEFAULT 0,
        id_categoria INTEGER,
        FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
    )
    """)

    # TABLA IMAGENES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS imagenes_producto (
        id_imagen INTEGER PRIMARY KEY AUTOINCREMENT,
        id_producto INTEGER,
        ruta_imagen TEXT,
        FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
    )
    """)

    # TABLA PEDIDOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
        referencia TEXT UNIQUE,
        fecha TEXT,
        total REAL,
        estado TEXT
    )
    """)

    # TABLA DETALLE PEDIDO
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalle_pedido (
        id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
        id_pedido INTEGER,
        id_producto INTEGER,
        cantidad INTEGER,
        precio_unitario REAL,
        personalizacion TEXT,
        FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido),
        FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
    )
    """)

    # TABLA ADMIN
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS administradores (
        id_admin INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        password TEXT
    )
    """)

    conexion.commit()
    conexion.close()

    print("Base de datos creada correctamente.")

def insertar_datos_prueba():
    conexion = sqlite3.connect("cleopatra.db")
    cursor = conexion.cursor()

    # CATEGORIAS
    cursor.execute("INSERT INTO categorias (nombre) VALUES ('Peluches')")
    cursor.execute("INSERT INTO categorias (nombre) VALUES ('Detalles')")
    cursor.execute("INSERT INTO categorias (nombre) VALUES ('Desayunos')")

    # PRODUCTOS
    cursor.execute("""
    INSERT INTO productos (nombre, descripcion, precio, disponible, personalizable, id_categoria)
    VALUES ('Oso de peluche gigante', 'Peluche grande ideal para regalos', 120000, 1, 1, 1)
    """)

    cursor.execute("""
    INSERT INTO productos (nombre, descripcion, precio, disponible, personalizable, id_categoria)
    VALUES ('Caja sorpresa romántica', 'Caja con chocolates y detalles', 80000, 1, 1, 2)
    """)

    cursor.execute("""
    INSERT INTO productos (nombre, descripcion, precio, disponible, personalizable, id_categoria)
    VALUES ('Desayuno sorpresa', 'Desayuno especial con frutas y café', 95000, 1, 1, 3)
    """)

    # IMAGENES
    cursor.execute("""
    INSERT INTO imagenes_producto (id_producto, ruta_imagen)
    VALUES (1, '/static/img/default.png')
    """)

    cursor.execute("""
    INSERT INTO imagenes_producto (id_producto, ruta_imagen)
    VALUES (2, '/static/img/default.png')
    """)

    cursor.execute("""
    INSERT INTO imagenes_producto (id_producto, ruta_imagen)
    VALUES (3, '/static/img/default.png')
    """)

    # ADMIN
    cursor.execute("""
    INSERT INTO administradores (usuario, password)
    VALUES ('admin', '1234')
    """)

    conexion.commit()
    conexion.close()

    print("Datos de prueba insertados.")

if __name__ == "__main__":
    crear_base_datos()
    insertar_datos_prueba()