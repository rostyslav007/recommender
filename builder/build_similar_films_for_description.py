import pandas as pd
import numpy as np
import mysql.connector
from builder_utils import cosine_similarity

THRESHOLD = 0.6

connector = mysql.connector.connect(
    user='root',
    password='7xt73k9x&xxa',
    host='localhost',
    database='recommendation'
)

cursor = connector.cursor()

query = ("SELECT user_id, film_id, rating FROM user_ratings")

cursor.execute(query)

mysql_data = {'user_id':[], 'film_id':[], 'rating':[]}

for (user_id, film_id, rating) in cursor:
    mysql_data['user_id'].append(user_id)
    mysql_data['film_id'].append(film_id)
    mysql_data['rating'].append(rating)

mysql_df = pd.DataFrame(mysql_data)

unique_user_ids = list(mysql_df['user_id'].unique())
unique_film_ids = list(mysql_df['film_id'].unique())

rows, cols = len(unique_user_ids), len(unique_film_ids)

id2row = {unique_user_ids[i]: i for i in range(len(unique_user_ids))} 
id2col = {unique_film_ids[i]: i for i in range(len(unique_film_ids))}

row2id = {i: unique_user_ids[i] for i in range(len(unique_user_ids))}
col2id = {i: unique_film_ids[i] for i in range(len(unique_film_ids))}

user_film_matrix = np.zeros(shape=(rows, cols))

for i in range(mysql_df.shape[0]):
    row = mysql_df.iloc[i, :]
    user_id, film_id, rating = id2row[row.user_id], id2col[row.film_id], row.rating
    user_film_matrix[user_id, film_id] = rating

user_film_matrix[user_film_matrix == 0] = np.nan
col_means = np.nanmean(user_film_matrix, axis=0)
matrix_mean = np.tile(col_means, rows).reshape(rows, -1)
mask = 1 - np.isnan(user_film_matrix)
user_film_matrix -= mask * matrix_mean
user_film_matrix[np.isnan(user_film_matrix)] = 0
print('building db')
try:
    for film_col in range(cols):
        film = user_film_matrix[:,film_col]

        similar = np.full(cols, -1, dtype='float32')

        for i in range(cols):
            another_film = user_film_matrix[:, i]
            cosine = cosine_similarity(film, another_film)
            similar[i] = cosine

        most_similar_cols = np.argsort(similar)[::-1]

        j = 0

        while similar[most_similar_cols[j]] > THRESHOLD:
            similar_col = most_similar_cols[j] 
            if similar_col != film_col:
                query = 'INSERT INTO similar_films (film_id, similar_film_id) VALUES (%s, %s)'
                values = (int(col2id[film_col]), int(col2id[similar_col]))
                print(values)
                cursor.execute(query, values)
                connector.commit()
            j += 1
    print('successfully built')
except e:
    print('something went wrong')
finally:
    connector.close()