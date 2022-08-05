import numpy as np
import mysql.connector
import pandas as pd
import mysql.connector

def get_connector():
    connector = mysql.connector.connect(
        user='root',
        password='7xt73k9x&xxa',
        host='localhost',
        database='recommendation'
    )

    return connector

def cosine_similarity_items(v1, v2, eps=1e-6):
    cosine = (v1 * v2).sum() / np.sqrt((v1**2).sum() * (v2**2).sum() + eps)
    return cosine

def cosine_similarity(vec1, vec2, mutual=3, eps=1e-6):
    mask = (vec1 != 0) & (vec2 != 0)
    if mask.sum() < mutual:
        return 0

    vec1 = vec1[mask]
    vec2 = vec2[mask]
    cosine = cosine_similarity_items(vec1, vec2)

    return cosine 

def get_similar_values(vector, matrix):
    rows = matrix.shape[0]
    similar = np.full(rows, -1, dtype='float32')

    for j in range(rows):
        another_vector = matrix[j]
        cosine = cosine_similarity(vector, another_vector)
        similar[j] = cosine 

    return similar

def normalize_matrix(matrix, mask, axis):
    rows, cols = matrix.shape
    matrix[matrix == 0] = np.nan
    means = np.nanmean(matrix, axis=axis)
    matrix_mean = np.tile(means, cols).reshape(rows, -1)
    matrix -= mask * matrix_mean
    matrix[np.isnan(matrix)] = 0
    return (means, matrix)

def get_most_similar_vectors(similar, vector_arr, vector_row, matrix, threshold, neighrours):
    if vector_row >= 0:
        neighrours += 1

    most_similar_rows = np.argsort(similar)[::-1]

    j = 0
    list_of_most_sim_vectors = []
    similar_values = []
    while similar[most_similar_rows[j]] > threshold and j < neighrours:
        similar_row = most_similar_rows[j] 
        if similar_row != vector_row:
            list_of_most_sim_vectors.append(matrix[similar_row])
            similar_values.append(similar[similar_row])
        j += 1

    return list_of_most_sim_vectors, similar_values

def mean_neighbour_recommendations(list_of_most_sim_vectors, similar_values_list):
    batch = np.array(list_of_most_sim_vectors)
    mask = ~(batch == 0)
    _, cols = batch.shape
    similar_values = np.array(similar_values_list)
    similar_values = np.tile(similar_values, cols).reshape(-1, cols)

    similar_values *= mask

    #mean_recommend = batch.mean(axis=0)

    mean_recommend = ((batch * similar_values).sum(axis=0) / similar_values.sum(axis=0)).flatten()

    return mean_recommend

def mode(ratings):
    ratings = [r for r in ratings if r!=0]
    rate_count = dict()
    for r in ratings:
        if r in rate_count:
            rate_count[r] += 1
        else:
            rate_count[r] = 1

    max_count = -1
    md = -1
    for rate, count in rate_count.items():
        if count > max_count:
            max_count = count
            md = rate
        elif count == max_count:
            if rate < md:
                md = rate
    return md

def ratings_df(connector):
    
    cursor = connector.cursor()

    query = ("SELECT user_id, film_id, rating FROM user_ratings")

    cursor.execute(query)

    mysql_data = {'user_id':[], 'film_id':[], 'rating':[]}

    for (user_id, film_id, rating) in cursor:
        mysql_data['user_id'].append(user_id)
        mysql_data['film_id'].append(film_id)
        mysql_data['rating'].append(rating)

    mysql_df = pd.DataFrame(mysql_data)

    return mysql_df

def load_content_df(connector):

    cursor = connector.cursor()
    query = ('SELECT id, name, year, short_desc, main_roles FROM films')

    cursor.execute(query)

    content_df = {'id':[], 'name':[], 'year':[], 'short_desc':[], 'main_roles':[]}

    for (film_id, name, year, short_desc, main_roles) in cursor:
        content_df['id'].append(film_id)
        content_df['name'].append(name)
        content_df['year'].append(year)
        content_df['short_desc'].append(short_desc)
        content_df['main_roles'].append(main_roles)

    content_df = pd.DataFrame(content_df)

    return content_df
