import bcrypt
import string
import random
import json
from datetime import datetime
from datetime import date

symbols = string.ascii_uppercase + string.ascii_lowercase + string.digits
year = list(range(1975, 2006))

def correct_login(mysql, login):

	q = execute_query(mysql,
		"""
		SELECT id FROM user WHERE login=%s
		""",
		(login, ))
	return not len(q) and len(login) >= 6

def correct_email(email):
	spl = email.split('@')
	return len(spl) > 1 and '.' in spl[-1] and all([len(p) for p in spl]) 

def check_name(name):
	return name != '' and name.isalpha()

def correct_film_name(name):
	return name and len(name) <= 100

def correct_film_year(year):
	return year.isnumeric() and len(year) == 4

def correct_film_price(price):
	return price and all([part.isnumeric() for part in price.split('.')])

def check_middle_name(middle_name):
	return middle_name != '' and middle_name.isalpha()

def check_last_name(last_name):
	return last_name != '' and last_name.isalpha()

def check_student_card(card):
	return card[:2].isalpha() and card[2:].isnumeric()

def check_password(passwrd):
	return len(passwrd) >= 8 and sum(l.isdigit() for l in passwrd) >= 2\

def hash_password(password):
	byte = password.encode('utf-8')
	mySalt = bcrypt.gensalt()
	hashed = bcrypt.hashpw(byte, mySalt)

	return hashed 

def secure_filename(filename):
	filename = filename.split('.')
	return filename[0] + ''.join(random.sample(symbols, 6)) + '.' + filename[1]

def execute_query(mysql, query, *args):
	cursor = mysql.connection.cursor()

	if not args:
		cursor.execute(query)
	else:
		cursor.execute(query, args[0])

	mysql.connection.commit()

	return cursor.fetchall()

def generate_password(length):
	return ''.join(random.sample(symbols, length))

def generate_email():
	return ''.join(random.sample(symbols, 10)) + '@gmail.com'

def generate_birthday():
	return str(random.sample(year, 1)[0]) + '-' + str(random.sample(list(range(1, 13)), 1)[0]) + '-' + str(random.sample(list(range(1, 29)), 1)[0])

def load_data_into_db(mysql):
	passwords = dict()
	f = open('static/data/db_data.json')
	data = json.load(f)

	for user_id, user_data in data.items():
		login = 'user' + str(user_id)
		password = generate_password(8)
		h_password = hash_password(password)
		email = generate_email()
		date_str = generate_birthday()
		format_str = "%Y-%m-%d"

		birth_date = datetime.strptime(date_str, format_str).date()
		today = date.today()
		age = int((today - birth_date).days / 365.2425)

			
		execute_query(mysql,
			"""
			INSERT INTO user (login, password, email, birthday, age)
			VALUES (%s, %s, %s, %s, %s)
			""",
			(login, h_password, email, birth_date.strftime('%Y-%m-%d'), age))

		db_user_id = execute_query(mysql, "SELECT id FROM user WHERE login=%s", (login, ))[0]['id']
		passwords[login] = password

		for film_id, rating in user_data.items():
			print(film_id, rating)
			r = int(rating*2+0.01)
			execute_query(mysql, 
				"INSERT INTO user_ratings (user_id, film_id, rating) VALUES (%s, %s, %s)", 
				(db_user_id, film_id, r))

	with open('static/data/passwords.json', 'w') as file:
   		json.dump(passwords, file)
