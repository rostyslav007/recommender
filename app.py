from flask import Flask, render_template, url_for, request, redirect, session, abort, jsonify
from flask_mysqldb import MySQL
from datetime import datetime
from datetime import date
from PIL import Image
import json
import bcrypt
import os
from utils import hash_password, execute_query, secure_filename, correct_film_name, \
correct_film_year, correct_film_price, correct_login, correct_email, load_data_into_db

UPLOAD_FOLDER = 'static/images/'


app = Flask(__name__)
app.secret_key = "a83ae@3rh4shf3dasasg#(2ogvfd"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '7xt73k9x&xxa'
app.config['MYSQL_DB'] = 'recommendation'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


def correct_filetype(filetype):
	return '.' in filetype and filetype.split('.')[-1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
	if not 'user' in session:
		return redirect('/login')
	
	recommended_films = execute_query(mysql,
		"""
		SELECT film_id, f.name, f.image FROM recommended_films
		INNER JOIN films as f
		ON film_id = f.id
		WHERE user_id = %s;
		""", (session['id'], ))

	recommended_films_svd = execute_query(mysql,
		"""
		SELECT film_id, f.name, f.image FROM recommended_films_svd
		INNER JOIN films as f
		ON film_id = f.id
		WHERE user_id = %s;
		""", (session['id'], ))

	return render_template('index.html', recommended = recommended_films, recommended_svd=recommended_films_svd)


@app.route('/login', methods=['GET', 'POST'])
def login():
	method = request.method

	if method == 'GET':
		return render_template('login.html')
	else:

		form = request.form

		login, password = form['login'], form['password']

		q_login = execute_query(mysql, "SELECT * FROM user WHERE login=%s", (login, ))
		if not q_login:
			flash('There is no user with such login')
			return redirect('/login')

		data = q_login[0]

		if not bcrypt.checkpw(password.encode('utf-8'), data['password'].encode('utf-8')):
			flash('Wrong password')
			return redirect('/login')

		session['id'] = data['id']
		session['user'] = data['login']
		session['age'] = data['age']

		return redirect('/')

	return redirect('/login')





@app.route('/register', methods=['GET', 'POST'])
def register():
	method = request.method

	if method == 'GET':
		return render_template('register.html')
	else:
		form = request.form

		login, email, birthday, password, password_repear = form['login'], form['email'], form['birthday'], form['password'], form['password_repeat']
		if correct_login(mysql, login) and correct_email(email) and (password == password_repear):
			date_str = birthday 
			format_str = '%Y-%m-%d' 
			birth_date = datetime.strptime(date_str, format_str).date()
			today = date.today()

			age = int((today - birth_date).days / 365.2425)
			hash_pass = hash_password(password)

			execute_query(mysql,
				"""
				INSERT INTO user (login, password, email, birthday, age)
				VALUES (%s, %s, %s, %s, %s)
				""",
				(login, hash_pass, email, birth_date.strftime('%Y-%m-%d'), age))

			return redirect('/login')

		return redirect('/register')



@app.route('/admin_form', methods=['GET', 'POST'])
def admin_form():
	if request.method == 'GET':
		return render_template('admin_form.html')
	else:
		form = request.form
		login, password = form['login'], form['password'].encode('utf-8')
		results = execute_query(mysql, 'SELECT password FROM admin WHERE login=%s', (login, ))

		if not len(results):
			abort(404)
		elif not bcrypt.checkpw(password, results[0]['password'].encode('utf-8')):
			abort(404)
		
		session['admin'] = 'admin'
		return redirect('/admin')




@app.route('/admin', methods=['GET'])
def admin():
	if 'admin' in session:
		films_data = execute_query(mysql, 'SELECT * FROM films')
		return render_template('admin.html', films=films_data)
	else:
		return redirect('/admin_form')


@app.route('/admin/add', methods=['GET', 'POST'])
def add():
	method = request.method

	if 'admin' in session:
		if method == 'GET':
			return render_template('add.html')
		else:
			if 'image' not in request.files:
				return redirect('/admin/add')

			form = request.form

			file = request.files['image']
			
			if not file.filename:
				return redirect('/admin/add')

			name, year, genre, short_desc, main_roles, price = form['name'], form['year'], form['genre'], form['description'], form['roles'], form['price']

			if not (correct_film_name(name) and correct_film_year(year) and correct_film_price(price) and len(short_desc) <= 2000):
				redirect ('/admin/add')

			if file and correct_filetype(file.filename):

				filename = secure_filename(file.filename)
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

				execute_query(mysql, """
							INSERT INTO films (name, image, year, genre, short_desc, main_roles, price) 
							VALUES (%s, %s, %s, %s, %s, %s, %s)
						""", (name, filename, year, genre, short_desc, main_roles, price))

				films_data = execute_query(mysql, 'SELECT * FROM films')

				return redirect('/admin')


			return render_template('add.html')

	return redirect('/admin_form')

@app.route('/admin/delete/<int:id>', methods=['GET'])
def delete(id):
	res = execute_query(mysql, 'SELECT image FROM films WHERE id=%s', (id, ))
	if not len(res):
		return redirect('/admin')

	image_name = res[0]['image']
	path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)

	if os.path.exists(path):
		os.remove(path)

	execute_query(mysql, 'DELETE FROM films WHERE id=%s', (id, ))
	return redirect('/admin')

@app.route('/admin/update/<int:id>', methods=['GET', 'POST'])
def update(id):
	method = request.method

	if method == 'GET':
		film_info = execute_query(mysql, 'SELECT * FROM films WHERE id=%s', (id, ))
		if not len(film_info):
			return redirect('/admin')

		return render_template('update.html', film=film_info[0])
	else:
		form = request.form
		file = request.files['image']

		name, year, genre, short_desc, main_roles, price = form['name'], form['year'], form['genre'], form['description'], form['roles'], form['price']

		if not (correct_film_name(name) and correct_film_year(year) and correct_film_price(price) and len(short_desc) <= 2000):
			return redirect (f'/admin/update/{id}')
		
		filename = file.filename

		if not file or not filename or not correct_filetype(filename):
			execute_query(mysql, """
				UPDATE films 
				SET name=%s, year=%s, genre=%s, short_desc=%s, main_roles=%s, price=%s
				WHERE id=%s
				""", 
				(name, year, genre, short_desc, main_roles, price, id))
			return redirect('/admin')

		else:
			q = execute_query(mysql, 'SELECT image FROM films WHERE id=%s', (id, ))
			if not q:
				flash('There is no film with such id')
				return redirect('/admin')

			old_image = q[0]['image']

			file.save(os.path.join(app.config['UPLOAD_FOLDER'], old_image))

			execute_query(mysql, """
				UPDATE films 
				SET name=%s, year=%s, genre=%s, short_desc=%s, main_roles=%s, price=%s
				WHERE id=%s
				""", 
				(name, year, genre, short_desc, main_roles, price, id))

		return redirect('/admin')

@app.route('/content/<int:page>', methods=['GET'])
def content(page):
	films_per_page = 30
	if not 'user' in session:
		return redirect('/login')

	q = execute_query(mysql,
		"""
		SELECT COUNT(user.id) as cnt 
		FROM user
		INNER JOIN user_ratings
		ON user.id = user_ratings.user_id
		WHERE user.id = %s
		""", (session['id'], ))
	count = 0
	if q:
		count = q[0]['cnt']

	films_count = execute_query(mysql, 'SELECT COUNT(id) as film_c FROM films')

	if count < 100:
		films = execute_query(mysql,
			"""
			SELECT films.id, films.image, films.name, films.genre, AVG(rating) as average
			FROM user_ratings RIGHT JOIN films
			ON user_ratings.film_id = films.id
			GROUP BY films.id
			ORDER BY average DESC, year DESC
			LIMIT %s, %s
			""", ((page-1)*films_per_page, films_per_page))
		pages_count = films_count[0]['film_c'] // films_per_page + 1
		return render_template('content.html', films=films, pages=pages_count, current_page=page)

@app.route('/description/<int:id>', methods=['GET'])
def description(id):
	if not 'user' in session:
		return redirect('/login')

	film_info = execute_query(mysql, """
		SELECT id, name, image, year, genre, short_desc, main_roles 
		FROM films
		WHERE id=%s
		""", (id, ))

	if not film_info:
		return redirect('/')

	status = -1

	q = execute_query(mysql, 
		"""
		SELECT watched FROM user_list
		WHERE user_id=%s AND film_id=%s
		""", (session['id'], id))

	if q:
		status = bool(int(q[0]['watched']))

	r = execute_query(mysql, 
		"""
		SELECT rating FROM user_ratings
		WHERE user_id=%s AND film_id=%s 
		""", (session['id'], id))
	rating = 0
	if r:
		rating = r[0]['rating'] 

	similar = execute_query(mysql, 
		"""
		SELECT similar_film_id, f.name, f.image, f.genre FROM similar_films
		INNER JOIN films as f
		ON f.id = similar_film_id
		WHERE film_id=%s LIMIT 8;
		""", (id, ))

	return render_template('description.html', film=film_info[0], status=status, film_id=id, rating=rating, similar=similar)

@app.route('/add_list/<int:id>')
def add_list(id):
	if not 'user' in session:
		return redirect('/login')

	q = execute_query(mysql, 'SELECT * FROM films WHERE id=%s', (id, ))
	if not q:
		return redirect('/my_list')

	execute_query(mysql, 
		"""
		INSERT INTO user_list (user_id, film_id)
		VALUES (%s, %s)
		""", (session['id'], id))

	return redirect('/my_list')

@app.route('/my_list')
def my_list():
	if not 'user' in session:
		return redirect('/login')

	my_list = execute_query(mysql,
		"""
		SELECT films.id, user_list.watched, user_list.date_time, films.name, films.image, films.year, films.genre  
		FROM user_list
		INNER JOIN films
		ON user_list.film_id = films.id
		WHERE user_list.user_id = %s AND user_list.watched = FALSE;
		""", (session['id'], ))

	return render_template('my_list.html', my_list=my_list)

@app.route('/watch/<int:id>')
def watch(id):
	if not 'user' in session:
		return redirect('/my_list')

	q = execute_query(mysql, 'SELECT * FROM films WHERE id=%s', (id, ))
	if not q:
		return redirect('/my_list')

	execute_query(mysql,
		"""
		UPDATE user_list
		SET watched = TRUE
		WHERE user_id=%s AND film_id=%s
		""", (session['id'], id))

	return redirect('/my_list')

@app.route('/remove_from_list/<int:id>')
def remove_from_list(id):
	if 'user' not in session:
		return redirect('/my_list')

	execute_query(mysql, 'DELETE FROM user_list WHERE user_id=%s AND film_id=%s', (session['id'], id))

	return redirect('/my_list')

@app.route('/watched')
def watched_list():
	if not 'user' in session:
		return redirect('/login')

	watched = execute_query(mysql,
		"""
		SELECT films.id, user_list.watched, user_list.date_time, films.name, films.image, films.year, films.genre  
		FROM user_list
		INNER JOIN films
		ON user_list.film_id = films.id
		WHERE user_list.user_id = %s AND user_list.watched = True;
		""", (session['id'], ))

	return render_template('watched.html', watched_list=watched)


@app.route('/rate', methods=['POST'])
def rate_film():
	method = request.method
	if method == 'POST':
		data = request.get_json()
		print(data)

		if data['current_rating'] == 0:
			execute_query(mysql, """
				INSERT INTO user_ratings (user_id, film_id, rating) 
				VALUES(%s, %s, %s)
				""", (data['user_id'], data['film_id'], data['rating']))
		else:
			execute_query(mysql, """
				UPDATE user_ratings
				SET rating=%s
				WHERE user_id=%s AND film_id=%s
				""", (data['rating'], data['user_id'], data['film_id']))
		results = {'processed':'true', 'new_rating': data['rating']}
		ret = jsonify(results)
		return ret

if __name__ == "__main__":
	app.run(debug=True)



