import numpy as np
import mysql.connector
import faiss

connector = mysql.connector.connect(
	user='root',
	password='7xt73k9x&xxa',
	host='localhost',
	database='recommendation'
)

cursor = connector.cursor()

query = 'DELETE FROM similar_films'

cursor.execute(query)

ids = np.load('./data/ids.npy')
film_topic_matrix = np.load('./data/film_topic_matrix.npy').astype(np.float32)

films_count, dim = film_topic_matrix.shape

index = faiss.IndexFlatL2(dim)   # build the index
print('trained knn search ', index.is_trained)
index.add(film_topic_matrix)      # add vectors to the index
print('number of films ', index.ntotal)

nn = 6

D, I = index.search(film_topic_matrix, nn + 1) # sanity check

try:
	for i, similar in enumerate(I):
		film_id = int(ids[i])
		for j in similar[1:]:
			similar_film_id = int(ids[j])
			query = 'INSERT INTO similar_films (film_id, similar_film_id) VALUES(%s, %s)'
			values = (film_id, similar_film_id)

			cursor.execute(query, values)
			connector.commit()
except Exception as e:
	print('some problem happened ', e)
finally:
	connector.close()

