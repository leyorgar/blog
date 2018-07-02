# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from models import db, Articulos, User, Categorias, Tag, tags
from os import getenv
from werkzeug.security import check_password_hash
from werkzeug import  secure_filename
from time import time
from math import ceil


# Iniciar
app = Flask(__name__)

# Config
app.config['DEBUG'] = True

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('SQLALCHEMY_DATABASE_URI')
app.config['SECRET_KEY'] = getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = set(['jpg', 'png'])
db.init_app(app)

@app.route("/")
def blog_all():
    mis_articulos = Articulos.query.order_by(Articulos.id.desc()).all()
    # Calculamos el numero maximo de paginas del paginador
    max_pags = ceil(len(mis_articulos) / 5)
    return render_template(
        'web/blog/all.html',
        articulos=mis_articulos,
        max_pags=max_pags
        ) 

@app.route("/articulo/<int:id>/")
def blog_articulo(id):
    # Para coger el articulo por su id
    mi_articulo = Articulos.query.get(id)
    # Select from User where id = mi_articulo.user_id
    mi_autor = User.query.get(mi_articulo.user_id)
    mi_categoria = Categorias.query.get(mi_articulo.categoria_id)
    return render_template(
        'web/blog/articulo.html',
        articulo=mi_articulo,
        autor=mi_autor.username,
        categoria=mi_categoria.name
        )

@app.route("/admin/login/", methods=['GET', 'POST'])
def admin_login():
    if request.method=='POST':
        my_user = User.query.filter_by(email=request.form['email']).first()
        if my_user and check_password_hash(my_user.password, request.form['password']):
            flash('Bienvenido', 'info')
            session['id'] = my_user.id
            return redirect(url_for('admin_articulos'))
        else:
            flash('Tu email o la contraseña no es correcto', 'danger')
    return render_template('web/admin/login.html')

@app.route("/admin/articulos/")
def admin_articulos():
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    # Obtenems todos los articulos
    articulos = Articulos.query.order_by(Articulos.id.desc()).all()
    return render_template('web/admin/articulos.html', articulos=articulos)

@app.route("/admin/articulos/nuevo", methods=['GET', 'POST'])
def admin_nuevo_articulo():
    # Comprobamos si tiene sesion
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    # Guardamos datos del formulario
    if request.method == 'POST':
        titulo = request.form['titulo']
        contenido = request.form['contenido']
        categoria = request.form['categoria']
        mis_tags = request.form.getlist('tags')
        usuario= session['id']
        # Guaardar en la base de datos
        nuevo_articulo = Articulos()
        nuevo_articulo.title = titulo
        nuevo_articulo.text = contenido
        nuevo_articulo.categoria_id = categoria
        nuevo_articulo.user_id = usuario
        for tag in mis_tags:
           mi_temp_tag = Tag.query.get(tag)
           nuevo_articulo.tags.append(mi_temp_tag)
        # Guardamos imagen
        try:
            f = request.files['portada']
            nombre = str(int(time())) + f.filename
            f.save('static/uploads/' + secure_filename(nombre))
            nuevo_articulo.portada = nombre
        except:
            flash('No se ha subido la imagen de portada', 'danger')
        db.session.add(nuevo_articulo)
        db.session.commit()
        # Mostramos informacion al usuario
        flash('Articulo creado', 'primary')
    # Obtenems todos las categorias
    categorias = Categorias.query.all()
    # Obtenemos los tags
    tags=Tag.query.all()
    return render_template('web/admin/nuevo_articulo.html', 
        categorias=categorias,
        tags=tags
        )

@app.route("/admin/categorias/")
def admin_categorias():
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    # Obtenems todos los articulos
    categorias = Categorias.query.all()
    return render_template('web/admin/categorias.html', categorias=categorias)

@app.route("/admin/categorias/nueva", methods=['GET', 'POST'])
def admin_nueva_categoria():
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    if request.method == 'POST':
        categoria = request.form['nombre']
        # Guardamos la categoria en la base de datos
        nueva_categoria = Categorias()
        nueva_categoria.name = categoria
        db.session.add(nueva_categoria)
        db.session.commit()
        # Mostramos informacion al usuario
        flash('Categoria creada', 'primary')
        return redirect(url_for("admin_categorias"))
    # Obtenems todos los articulos
    categorias = Categorias.query.all()
    return render_template('web/admin/nueva_categoria.html', categorias=categorias)

@app.route('/articulo/borrar', methods=['POST'])
def borrar_articulo():
    if request.method == 'POST':
        articulo_id_borrar = request.form['articulo-borrar']
        # Borramos de la base de datos
        Articulos.query.filter_by(id=articulo_id_borrar).delete()
        db.session.commit()
        flash('Articulo borrado correctamente', 'success')
    return redirect(url_for('admin_articulos'))

@app.route('/articulo/actualizar/<int:id>', methods=['GET', 'POST'])
def editar_articulo(id):
    # PRotegemos nuestra pagina
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    # Consultamos la base de datos
    mi_articulo = Articulos.query.get(id)
    if request.method == 'POST':
        titulo = request.form['titulo']
        contenido = request.form['contenido']
        categoria = request.form['categoria']
        mis_tags = request.form.getlist('tags')
        usuario= session['id']
        # Guaardar en la base de datos
        mi_articulo.title = titulo
        mi_articulo.text = contenido
        mi_articulo.categoria_id = categoria
        mi_articulo.user_id = usuario
        for tag in mis_tags:
           mi_temp_tag = Tag.query.get(tag)
           nuevo_articulo.tags.append(mi_temp_tag)
        # Guardamos imagen
        try:
            f = request.files['portada']
            if f.filename:
                nombre = str(int(time())) + f.filename
                f.save('static/uploads/' + secure_filename(nombre))
                mi_articulo.portada = nombre
        except:
            flash('No se ha subido la imagen de portada', 'danger')
        db.session.add(mi_articulo)
        db.session.commit()
        # Mostramos informacion al usuario
        flash('Articulo creado', 'primary')
    # Obtenems todos las categorias
    categorias = Categorias.query.all()
    # Obtenemos los tags
    tags=Tag.query.all()
    return render_template('web/admin/editar_articulo.html', 
        categorias=categorias,
        tags=tags,
        articulo=mi_articulo
        )

@app.route('/categoria/borrar', methods=['POST'])
def borrar_categoria():
    if request.method == 'POST':
        # Obtenemos la id
        categoria_id_borrar = request.form['categoria-borrar']
        # Borramos de la base de datos
        Categorias.query.filter_by(id=categoria_id_borrar).delete()
        db.session.commit()
        # Marcamos la categoria por defecto para los articulos
        articulos = Articulos.query.filter_by(categoria_id=categoria_id_borrar).all()
        for articulo in articulos:
            articulo.categoria = Categorias.query.first()
            db.session.add(articulo)
        # Informamos al usuario
        flash('Categoría borrada correctamente', 'success')
    return redirect(url_for('admin_categorias'))

@app.route('/categoria/editar/<int:id>', methods=['GET', 'POST'])
def editar_categoria(id):
    # Consultamos la base de datos
    mi_categoria = Categorias.query.get(id)
    # Actualizar
    if request.method == 'POST':
        nombre = request.form['nombre']
        mi_categoria.name = nombre
        db.session.add(mi_categoria)
        db.session.commit()
        flash('Categoria actualizada', 'success')
        return redirect(url_for('admin_categorias'))
    # Renderizamos
    return render_template(
        'web/admin/editar_categoria.html',
        categoria = mi_categoria
    )

@app.route("/admin/tags/")
def admin_tags():
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    # Obtenems todos los articulos
    tags = Tag.query.all()
    return render_template('web/admin/tags.html', tags=tags)

@app.route("/admin/tags/nueva", methods=['GET', 'POST'])
def admin_nuevo_tag():
    if 'id' not in session:
        flash('No tienes acceso', 'danger')
        return redirect(url_for('blog_all'))
    if request.method == 'POST':
        tag = request.form['nombre']
        # Guardamos la categoria en la base de datos
        nuevo_tag = Tag()
        nuevo_tag.name = tag
        db.session.add(nuevo_tag)
        db.session.commit()
        # Mostramos informacion al usuario
        flash('Tag creado', 'primary')
        return redirect(url_for("admin_tags"))
    # Obtenems todos los articulos
    tags = Tag.query.all()
    return render_template('web/admin/nuevo_tag.html', tags=tags)

@app.route('/tags/borrar', methods=['POST'])
def borrar_tag():
    if request.method == 'POST':
        tag_id_borrar = request.form['tag-borrar']
        # Borramos de la base de datos
        Tag.query.filter_by(id=tag_id_borrar).delete()
        db.session.commit()
        flash('Tag borrada correctamente', 'success')
    return redirect(url_for('admin_categorias'))

@app.route('/tags/editar/<int:id>', methods=['GET', 'POST'])
def editar_tag(id):
    # Consultamos la base de datos
    mi_tag = Tag.query.get(id)
    # Actualizar
    if request.method == 'POST':
        nombre = request.form['nombre']
        mi_tag.name = nombre
        db.session.add(mi_tag)
        db.session.commit()
        flash('Tag actualizado', 'success')
        return redirect(url_for('admin_tags'))
    return render_template(
        'web/admin/editar_tag.html',
        tag=mi_tag
    )

@app.route('/logout')
def logout():
    session.pop('id', None)
    flash('Has cerrado tu sesión correctamente', 'success')
    return redirect(url_for('blog_all'))

@app.route('/buscar')
def buscar():
    if request.args.get('q'):
        q = request.args.get('q')
        mis_resultados = Articulos.query.filter(Articulos.title.ilike(f'%{q}%')).all()
        return render_template(
            'web/blog/busqueda.html',
            resultados=mis_resultados,
            num_resultados=len(mis_resultados),
            busqueda=q
        )
    else:
        return redirect(url_for('blog_all'))

@app.route('/api/articulos/<int:pag>')
def api_articulos(pag):
    num_articulos_max = 5
    mis_articulos = Articulos.query.offset((pag-1)*num_articulos_max).limit(num_articulos_max).all()    
    # Convertimos un resultado de models a un Json
    dict_resultados = dict()
    for articulo in mis_articulos:
        portada = ''
        if articulo.portada:
            portada = url_for('static', filename='uploads/' + articulo.portada)
        dict_resultados[articulo.id]= {
            'id': articulo.id,
            'portada': portada,
            'title': articulo.title,
            'text': articulo.text[1:100]
        }
    return jsonify(dict_resultados)


if __name__ == "__main__":
    app.run()