import pandas as pd
import numpy as np
import mysql.connector
from builder_utils import cosine_similarity, normalize_matrix, get_similar_values, \
get_most_similar_vectors, mean_neighbour_recommendations, ratings_df
np.seterr(all="ignore")

THRESHOLD = 0.6
NEIGHBOURS = 3

connector = mysql.connector.connect(
    user='root',
    password='7xt73k9x&xxa',
    host='localhost',
    database='recommendation'
)

cursor = connector.cursor()

mysql_df = ratings_df(connector)

unique_user_ids = list(mysql_df['user_id'].unique())
unique_film_ids = list(mysql_df['film_id'].unique())

rows, cols = len(unique_user_ids), len(unique_film_ids)

id2row = {unique_user_ids[i]: i for i in range(len(unique_user_ids))} 
id2col = {unique_film_ids[i]: i for i in range(len(unique_film_ids))}

row2id = {value: key for key, value in id2row.items()}
col2id = {value: key for key, value in id2col.items()}

user_film_matrix = np.zeros(shape=(rows, cols))
rated = np.zeros(shape=(rows, cols), dtype=bool)

for i in range(mysql_df.shape[0]):
    row = mysql_df.iloc[i, :]
    row, col, rating = id2row[row.user_id], id2col[row.film_id], row.rating
    rated[row, col] = True
    user_film_matrix[row, col] = rating

row_means, user_film_matrix = normalize_matrix(user_film_matrix, rated, axis=1)

print('building db')
try:
    for user_row in range(rows):
        user = user_film_matrix[user_row]

        user_vector = user_film_matrix[user_row]

        similar = get_similar_values(user_vector, user_film_matrix)

        user_watch = rated[user_row]


        list_of_most_sim_users, similar_values = get_most_similar_vectors(similar, user_vector, user_row, user_film_matrix, \
                                                                      THRESHOLD, NEIGHBOURS)

        if list_of_most_sim_users:
            mean_recommend = mean_neighbour_recommendations(list_of_most_sim_users, similar_values)

            rec = (mean_recommend > 0) & (user_watch == False)
            rec_indices = np.where(rec > 0)[0]
            sorted_indices = np.argsort(mean_recommend[rec_indices])[::-1]
            most_relevant_film_cols = rec_indices[sorted_indices]
        
            for film_id in [col2id[f] for f in most_relevant_film_cols]:
                query = 'INSERT INTO recommended_films (user_id, film_id) VALUES(%s, %s)'
                values = (int(row2id[user_row]), int(film_id))
                cursor.execute(query, values)
                connector.commit()
                
    print('successfully built')
except Exception as e:
    print('something went wrong ', e)
finally:
    connector.close()