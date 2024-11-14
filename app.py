from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Conexión a la base de datos MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/solucionador'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Definición del modelo Usuario
class Usuario(db.Model):
    __tablename__ = 'usuarios'  # Asegúrate de que coincida con el nombre de tu tabla
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)  # Encriptación de contraseña
    rol_id = db.Column(db.Integer, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)  # Nuevo campo para el nombre completo

# Clave secreta para las sesiones
app.secret_key = 'your_secret_key'

# Ruta para el panel de usuario
@app.route('/')
def user_panel():
    if 'loggedin' not in session or session['role'] != 'usuario':
        return redirect(url_for('login'))
    return render_template('usuarios/user.html')

# Ruta para el panel de administrador
@app.route('/admin')
def admin_panel():
    if 'loggedin' not in session or session['role'] != 'administrador':
        return redirect(url_for('login'))
    return render_template('admin/admin.html')

# Ver usuarios y funcionamiento  
@app.route('/admin/ver_usuarios')
def ver_usuarios():
    if 'loggedin' not in session or session['role'] != 'administrador':
        return redirect(url_for('login'))
    
    # Obtener parámetro de búsqueda
    query = request.args.get('q', '')
    
    # Filtrar usuarios si hay un término de búsqueda
    if query:
        usuarios = Usuario.query.filter(Usuario.nombre_usuario.like(f"%{query}%")).all()
    else:
        usuarios = Usuario.query.all()
    
    return render_template('admin/ver_usuarios.html', usuarios=usuarios)



# EDITAR USUARIO SELECCIONADO DE VER USUARIOS
@app.route('/admin/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if 'loggedin' not in session or session['role'] != 'administrador':
        return redirect(url_for('login'))

    # Obtener el usuario por ID
    usuario = Usuario.query.get_or_404(id)

    if request.method == 'POST':
        # Actualizar los datos del usuario desde el formulario
        usuario.nombre = request.form['nombre']
        usuario.nombre_usuario = request.form['nombre_usuario']
        rol_id = request.form['rol_id']
        if rol_id.isdigit():
            usuario.rol_id = int(rol_id)
        
        # Si se proporciona una nueva contraseña, actualizarla
        nueva_contraseña = request.form['contraseña']
        if nueva_contraseña:
            usuario.contraseña = generate_password_hash(nueva_contraseña)

        # Guardar los cambios
        db.session.commit()
        flash('Usuario actualizado exitosamente')
        return redirect(url_for('ver_usuarios'))

    # Renderizar el formulario de edición con los datos del usuario
    return render_template('admin/editar_usuarios.html', usuario=usuario)


# ELIMINAR USUARIO DE MODULO VER USUAIROS
@app.route('/admin/eliminar_usuario/<int:id>', methods=['GET'])
def eliminar_usuario(id):
    if 'loggedin' not in session or session['role'] != 'administrador':
        return redirect(url_for('login'))

    # Obtener el usuario por ID y eliminarlo
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    
    flash('Usuario eliminado exitosamente')
    return redirect(url_for('ver_usuarios'))







# Ruta para crear usuarios
@app.route('/admin/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if 'loggedin' not in session or session['role'] != 'administrador':
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Recibir datos del formulario
        nombre_usuario = request.form['nombre_usuario']
        contraseña = request.form['contraseña']
        rol_id = request.form['rol_id']
        nombre = request.form['nombre']  # Campo para el nombre completo

        # Encriptar la contraseña antes de guardarla en la base de datos
        hashed_password = generate_password_hash(contraseña)

        # Crear una instancia de Usuario con los datos del formulario
        nuevo_usuario = Usuario(
            nombre_usuario=nombre_usuario, 
            contraseña=hashed_password, 
            rol_id=rol_id,
            nombre=nombre  # Asignar nombre completo
        )
        
        # Guardar el nuevo usuario en la base de datos
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        # Agregar mensaje flash de éxito y redireccionar a la lista de usuarios
        flash('Usuario creado exitosamente')
        return redirect(url_for('ver_usuarios'))

    return render_template('admin/crear_usuario.html')


# Ruta para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        if session['role'] == 'administrador':
            return redirect(url_for('admin_panel'))
        elif session['role'] == 'usuario':
            return redirect(url_for('user_panel'))
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        # Buscar al usuario por nombre de usuario
        user = Usuario.query.filter_by(nombre_usuario=username).first()
        
        # Verificar si el usuario existe y si la contraseña coincide
        if user and check_password_hash(user.contraseña, password):
            session['loggedin'] = True
            session['id'] = user.id
            session['username'] = user.nombre_usuario
            if user.rol_id == 1:
                session['role'] = 'administrador'
                return redirect(url_for('admin_panel'))
            else:
                session['role'] = 'usuario'
                return redirect(url_for('user_panel'))
        else:
            msg = 'Credenciales incorrectas'
    
    return render_template('login.html', msg=msg) 


# Ruta para logout
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))





# Definición del modelo Categoría -------------------------------------------------------------------
class Categoria(db.Model):
    __tablename__ = 'categorias'  # Nombre de la tabla en la base de datos
    id = db.Column(db.Integer, primary_key=True)
    nombre_categoria = db.Column(db.String(100), nullable=False)
    descripcion_categoria = db.Column(db.Text, nullable=False)
    estado_categoria = db.Column(db.String(10), nullable=False)  # 'activo' o 'inactivo'

# Ruta para ver categorías
@app.route('/admin/ver_categorias')
def ver_categorias():
    if 'loggedin' not in session or session['role'] != 'administrador':
        return redirect(url_for('login'))
    categorias = Categoria.query.all()
    return render_template('admin/ver_categorias.html', categorias=categorias)

# Ruta para crear categorías
@app.route('/admin/crear_categoria', methods=['GET', 'POST'])
def crear_categoria():
    if 'loggedin' not in session or session['role'] != 'administrador':
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre_categoria = request.form['nombre_categoria']
        descripcion_categoria = request.form['descripcion_categoria']
        estado_categoria = request.form['estado_categoria']
        nueva_categoria = Categoria(
            nombre_categoria=nombre_categoria,
            descripcion_categoria=descripcion_categoria,
            estado_categoria=estado_categoria
        )
        db.session.add(nueva_categoria)
        db.session.commit()
        return redirect(url_for('ver_categorias'))

    return render_template('admin/crear_categoria.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
