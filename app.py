from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = "cleopatra_secret"

DATABASE = "cleopatra.db"


# -------------------------
# CONEXIÓN BASE DE DATOS
# -------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------
# PÁGINAS PÚBLICAS
# -------------------------

@app.route("/")
def home():
    return render_template("publico/home.html")


@app.route("/catalogo")
def catalogo():
    conn = get_db()
    categoria = request.args.get("categoria")

    if categoria:
        productos = conn.execute(
            "SELECT * FROM productos WHERE id_categoria=?",
            (categoria,)
        ).fetchall()
    else:
        productos = conn.execute(
            "SELECT * FROM productos"
        ).fetchall()

    categorias = conn.execute("SELECT * FROM categorias").fetchall()

    conn.close()

    return render_template(
        "publico/catalogo.html",
        productos=productos,
        categorias=categorias
    )


@app.route("/producto/<int:id>")
def producto(id):
    conn = get_db()

    producto = conn.execute(
        "SELECT * FROM productos WHERE id_producto=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template("publico/producto.html", producto=producto)


# -------------------------
# AUTENTICACIÓN
# -------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        correo = request.form["correo"]
        password = request.form["password"]

        conn = get_db()

        usuario = conn.execute(
            "SELECT * FROM usuarios WHERE correo=? AND password=?",
            (correo, password)
        ).fetchone()

        conn.close()

        if usuario:

            session["usuario_id"] = usuario["id_usuario"]
            session["rol"] = usuario["rol"]
            session["nombre"] = usuario["nombre"]

            if usuario["rol"] == "admin":
                return redirect(url_for("admin_panel"))
            else:
                return redirect(url_for("catalogo"))

        else:
            return "Correo o contraseña incorrectos"

    return render_template("cliente/login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form["nombre"]
        correo = request.form["correo"]
        password = request.form["password"]

        conn = get_db()

        conn.execute(
            "INSERT INTO usuarios (nombre, correo, password, rol) VALUES (?,?,?,?)",
            (nombre, correo, password, "cliente")
        )

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("cliente/registro.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# -------------------------
# CARRITO
# -------------------------

@app.route("/agregar_carrito/<int:id>", methods=["POST"])
def agregar_carrito(id):

    cantidad = int(request.form["cantidad"])
    personalizacion = request.form.get("personalizacion", "")

    conn = get_db()

    producto = conn.execute(
        "SELECT * FROM productos WHERE id_producto=?",
        (id,)
    ).fetchone()

    conn.close()

    if "carrito" not in session:
        session["carrito"] = []

    carrito = session["carrito"]

    carrito.append({
        "id_producto": id,
        "nombre": producto["nombre"],
        "precio": producto["precio"],
        "cantidad": cantidad,
        "personalizacion": personalizacion
    })

    session["carrito"] = carrito

    return redirect(url_for("carrito"))


@app.route("/carrito")
def carrito():

    carrito = session.get("carrito", [])

    total = 0
    for item in carrito:
        total += item["precio"] * item["cantidad"]

    return render_template(
        "cliente/carrito.html",
        carrito=carrito,
        total=total
    )


@app.route("/eliminar_carrito/<int:index>")
def eliminar_carrito(index):

    carrito = session.get("carrito", [])

    if 0 <= index < len(carrito):
        carrito.pop(index)

    session["carrito"] = carrito

    return redirect(url_for("carrito"))


# -------------------------
# GENERAR PEDIDO
# -------------------------

@app.route("/generar_pedido")
def generar_pedido():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    carrito = session.get("carrito", [])

    if not carrito:
        return redirect(url_for("carrito"))

    conn = get_db()

    referencia = "PED-" + str(random.randint(1000, 9999))
    fecha = datetime.now().strftime("%Y-%m-%d")

    total = 0
    for item in carrito:
        total += item["precio"] * item["cantidad"]

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO pedidos (referencia, fecha, total, estado, id_usuario)
        VALUES (?,?,?,?,?)
        """,
        (referencia, fecha, total, "Pendiente", session["usuario_id"])
    )

    id_pedido = cursor.lastrowid

    for item in carrito:

        cursor.execute(
            """
            INSERT INTO detalle_pedido
            (id_pedido, id_producto, cantidad, precio_unitario, personalizacion)
            VALUES (?,?,?,?,?)
            """,
            (
                id_pedido,
                item["id_producto"],
                item["cantidad"],
                item["precio"],
                item["personalizacion"]
            )
        )

    conn.commit()
    conn.close()

    session["carrito"] = []

    return render_template(
        "cliente/pedido_confirmado.html",
        referencia=referencia
    )




@app.route("/mis_pedidos")
def mis_pedidos():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = sqlite3.connect("cleopatra.db")
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_pedido, referencia, fecha, total, estado
        FROM pedidos
        WHERE id_usuario = ?
        ORDER BY fecha DESC
    """, (session["usuario_id"],))

    pedidos = cursor.fetchall()

    conexion.close()

    return render_template(
        "cliente/mis_pedidos.html",
        pedidos=pedidos
    )

# -------------------------
# ADMIN PANEL
# -------------------------

@app.route("/admin")
def admin_panel():

    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    return render_template("admin/admin_panel.html")


# -------------------------
# ADMIN PRODUCTOS
# -------------------------

@app.route("/admin/productos")
def admin_productos():

    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    conn = get_db()

    productos = conn.execute(
        """
        SELECT productos.*, categorias.nombre as categoria
        FROM productos
        LEFT JOIN categorias
        ON productos.id_categoria = categorias.id_categoria
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin/admin_productos.html",
        productos=productos
    )


@app.route("/admin/productos/crear", methods=["GET", "POST"])
def admin_crear_producto():

    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":

        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        precio = request.form["precio"]
        imagen = request.form["imagen"]
        id_categoria = request.form["id_categoria"]

        conn.execute(
            """
            INSERT INTO productos
            (nombre, descripcion, precio, imagen, id_categoria)
            VALUES (?,?,?,?,?)
            """,
            (nombre, descripcion, precio, imagen, id_categoria)
        )

        conn.commit()

        return redirect(url_for("admin_productos"))

    categorias = conn.execute("SELECT * FROM categorias").fetchall()

    conn.close()

    return render_template(
        "admin/admin_producto_form.html",
        categorias=categorias
    )


@app.route("/admin/productos/editar/<int:id>", methods=["GET", "POST"])
def admin_editar_producto(id):

    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":

        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        precio = request.form["precio"]
        imagen = request.form["imagen"]
        id_categoria = request.form["id_categoria"]

        conn.execute(
            """
            UPDATE productos
            SET nombre=?, descripcion=?, precio=?, imagen=?, id_categoria=?
            WHERE id_producto=?
            """,
            (nombre, descripcion, precio, imagen, id_categoria, id)
        )

        conn.commit()

        return redirect(url_for("admin_productos"))

    producto = conn.execute(
        "SELECT * FROM productos WHERE id_producto=?",
        (id,)
    ).fetchone()

    categorias = conn.execute("SELECT * FROM categorias").fetchall()

    conn.close()

    return render_template(
        "admin/admin_producto_form.html",
        producto=producto,
        categorias=categorias
    )


@app.route("/admin/productos/eliminar/<int:id>")
def admin_eliminar_producto(id):

    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        "DELETE FROM productos WHERE id_producto=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_productos"))


# -------------------------
# ADMIN PEDIDOS
# -------------------------

@app.route("/admin/pedidos")
def admin_pedidos():

    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    conn = get_db()

    pedidos = conn.execute(
        """
        SELECT pedidos.*, usuarios.nombre
        FROM pedidos
        JOIN usuarios
        ON pedidos.id_usuario = usuarios.id_usuario
        ORDER BY fecha DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin/admin_pedidos.html",
        pedidos=pedidos
    )


@app.route("/admin/pedidos/<int:id>")
def admin_detalle_pedido(id):

    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    conn = get_db()

    detalles = conn.execute(
        """
        SELECT detalle_pedido.*, productos.nombre
        FROM detalle_pedido
        JOIN productos
        ON detalle_pedido.id_producto = productos.id_producto
        WHERE id_pedido=?
        """,
        (id,)
    ).fetchall()

    conn.close()

    return render_template(
        "admin/admin_detalle_pedido.html",
        detalles=detalles,
        id_pedido=id
    )


@app.route("/admin/pedidos/estado/<int:id>", methods=["POST"])
def cambiar_estado_pedido(id):

    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    nuevo_estado = request.form["estado"]

    conn = get_db()

    conn.execute(
        "UPDATE pedidos SET estado=? WHERE id_pedido=?",
        (nuevo_estado, id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_pedidos"))


# -------------------------
# EJECUTAR APP
# -------------------------

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)  # <- agrega debug=True
