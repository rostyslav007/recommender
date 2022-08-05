import mysql.connector
import numpy as np
import random
import pandas as pd
import matplotlib.pyplot as plt
from builder_utils import cosine_similarity, normalize_matrix, get_similar_values, \
get_most_similar_vectors, mean_neighbour_recommendations, ratings_df, mode
np.seterr(all="ignore")

SEED = 15

THRESHOLD = 0.6
NEIGHBOURS = 3

connector = mysql.connector.connect(
    user='root',
    password='7xt73k9x&xxa',
    host='localhost',
    database='recommendation'
)

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

ratings_matrix = np.copy(user_film_matrix)

means, user_film_matrix = normalize_matrix(user_film_matrix, rated, axis=1)

train_part = 0.7

train_size = int(rows * train_part)

user_film_train = user_film_matrix[:train_size]
means_train = means[:train_size]
rated_train = rated[:train_size]

user_film_test = user_film_matrix[train_size:]
means_test = means[train_size:]
rated_test = rated[train_size:]

test_ratings = ratings_matrix[train_size:]
hidden_percent = 0.4

MAE_list = []
true_positive = 0
false_positive = 0
true_negative = 0


for test_user_idx in range(user_film_test.shape[0]):

    test_user_vector = user_film_test[test_user_idx]
    indices = np.where(rated_test[test_user_idx])[0]
    positive_count = indices.shape[0]
    hidden_indices = np.array(random.sample(list(indices), int(hidden_percent * positive_count)))
    ground_truth_indices = np.array(list(set(list(indices)) - set(list(hidden_indices))))
    
    test_user_vector[hidden_indices] = 0
    similar = get_similar_values(test_user_vector, user_film_train)
    
    most_similar_vectors, similarity_list = get_most_similar_vectors(similar, test_user_vector, -1, user_film_train, THRESHOLD, NEIGHBOURS)
    if similarity_list:
        mean_recommend = mean_neighbour_recommendations(most_similar_vectors, similarity_list)


        user_bias = means_test[test_user_idx]
        user_prediction = (user_bias + mean_recommend)[hidden_indices]
        user_prediction = np.clip(user_prediction, 1, 10)

        true_user_ratings = test_ratings[test_user_idx][hidden_indices]

        user_mode = mode(list(test_ratings[test_user_idx]))

        # calculating MAE precision value
        MAE = np.nanmean(np.absolute(user_prediction - true_user_ratings))

        MAE_list.append(MAE)
        # MAE class precision
        mask = ~np.isnan(user_prediction)
        all_preds = mask.sum()
        # counting true positives and false positives
        like = user_prediction[mask] >= user_mode
        actual = true_user_ratings[mask] >= user_mode
        correct = (like & actual).sum()
        wrong = all_preds - correct

        true_positive += correct
        false_positive += wrong

        #true negatives
        mask = ground_truth_indices
        predicted = (user_bias + mean_recommend)[mask]
        truth = test_ratings[test_user_idx][mask]

        true_negative += ((truth >= user_mode) & (predicted < user_mode)).sum()
        
print('MAE: ', sum(MAE_list) / len(MAE_list))
print('precision: ', true_positive / (true_positive + false_positive))
print('recall: ', true_positive / (true_positive + true_negative))
