import numpy as np
from numpy.linalg import svd 
import matplotlib.pyplot as plt
import seaborn as sns
from builder_utils import get_connector, ratings_df, cosine_similarity_items
from funk_svd_model import FunkSVDModel
from random import sample
import torch.nn as nn
import torch
import torch.optim as optim

test = False

def get_k(S):
    all_info = S.sum()
    s = 0
    i = 0
    while s / all_info < 0.9:
        s += S[i]
        i += 1
    
    return i

def get_uv(U, S, Vt, k):
    U_dims, V_dims = U.shape[0], Vt.shape[0]
    S[k:] = 0
    S_sqrt = np.sqrt(S)

    S_u = np.zeros(shape=(U_dims, k))
    np.fill_diagonal(S_u, S_sqrt)

    S_v = np.zeros(shape=(k, V_dims))
    np.fill_diagonal(S_v, S_sqrt)

    np.fill_diagonal(S_v, S_sqrt)
    U = U @ S_u
    V = S_v @ Vt

    return U, V

connector = get_connector()

mysql_df = ratings_df(connector)

unique_user_ids = list(mysql_df['user_id'].unique())
unique_film_ids = list(mysql_df['film_id'].unique())

rows, cols = len(unique_user_ids), len(unique_film_ids)

id2row = {unique_user_ids[i]: i for i in range(len(unique_user_ids))} 
id2col = {unique_film_ids[i]: i for i in range(len(unique_film_ids))}

row2id = {value: key for key, value in id2row.items()}
col2id = {value: key for key, value in id2col.items()}

user_film_matrix = np.zeros(shape=(rows, cols), dtype=np.float64)
rated = np.zeros(shape=(rows, cols), dtype=bool)

for i in range(mysql_df.shape[0]):
    row = mysql_df.iloc[i, :]
    row, col, rating = id2row[row.user_id], id2col[row.film_id], row.rating
    rated[row, col] = True
    user_film_matrix[row, col] = rating

if test:

    rated_indices = np.where(rated)
    list_of_indices = list(range(len(rated_indices[0])))

    test_indices_size = 800

    hidden_indices = np.array(sample(list_of_indices, test_indices_size))

    rated_hidden_indices = (rated_indices[0][hidden_indices], rated_indices[1][hidden_indices])

    hidden_rows, hidden_cols = rated_hidden_indices[0], rated_hidden_indices[1]

    hidden_ratings = user_film_matrix[hidden_rows, hidden_cols]

    user_film_matrix[hidden_rows, hidden_cols] = 0
    rated[hidden_rows, hidden_cols] = False

### SVD factorization

#mean_rating = user_film_matrix[rated].mean()
#user_film_matrix[rated] -= mean_rating

#U_svd, S, Vt = svd(user_film_matrix)

#k_principal = get_k(S)

#U, V = get_uv(U_svd, S, Vt, k_principal)

#predictons = U @ V + mean_rating

#predicted_hidden_ratings = predictons[hidden_rows, hidden_cols]

###

n_dims = 40

model = FunkSVDModel(rows, cols, n_dims)

num_iterations = 300
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
lamb = 0.02

true_ratings =  torch.tensor(user_film_matrix[rated].astype(np.float32))
if test:
    test_ratings = torch.tensor(hidden_ratings.astype(np.float32))

train_error = []

if test:
    test_error = []

#Training user and film matrix representation

for e in range(num_iterations):
    pred_matrix = model()

    loss = torch.sqrt(criterion(pred_matrix[rated], true_ratings)) + lamb * model.regularize()

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    train_error.append(loss.item())

    if test:
        test_loss = torch.sqrt(criterion(pred_matrix[hidden_rows, hidden_cols], test_ratings)) + lamb * model.regularize()
        test_error.append(test_loss.item())

def plot_errors(train_error, test_error):
    fig = plt.figure()

    plt.subplot(1, 2, 1)
    plt.plot(list(range(len(train_error))), test_error)

    plt.subplot(1, 2, 2)
    plt.plot(list(range(len(test_error))), test_error)
    plt.show()

if test:
    plot_errors(train_error, test_error)

prediction = model.final_prediction()

try:
    if not test:
        query = 'DELETE FROM recommended_films_svd'
        cursor = connector.cursor()
        cursor.execute(query)

        for user_row in range(rows):
            user_rate = rated[user_row]
            user_mean = user_film_matrix[user_row][user_rate].mean()

            recomm_list = []
            for film_col in range(cols):
                value = prediction[user_row, film_col]
                if (not user_rate[film_col]):
                    recomm_list.append((value, film_col))

            sorted_recomm = sorted(recomm_list, key=lambda x: x[0], reverse=True)
            
            for value, col in sorted_recomm[:8]:
                query = 'INSERT INTO recommended_films_svd (user_id, film_id) VALUES (%s, %s)'
                values = (int(row2id[user_row]), int(col2id[col]))
                cursor.execute(query, values)
                connector.commit()
except Exception as e:
    print('something go wrong ', e)
finally:
    connector.close()