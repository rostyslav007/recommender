# Recommended System

Web-site for films recommendation, based on machine and deep learning models

## Project structure
***static folder***

Includes css, javascript scripts, data for project

***templates***
Consists of html project templates

***utils.py***
Helper scripts for db connection, user information check

***app.py***
Flask app implementing web-site logic

***builder folder***: Recommendation logic part of project
- **build_content_based_film_recommender.py**: builds films recommendation based on films description using LDAModel
- **build_film_recommender.py**: fills database with similar films sets through fast facebook **KNN algorithm** implementation from module **faiss**
- **build_funk_svd_factorization.py**: ***FunkSVD*** model for users and films vector encoding based on Netflix 1000 000$ kaggle competition top list winner
- **build_similar_films_for_description.py**: item-item recommendation using **cosine similarity** and user-film rate matrix 
- **build_user_user_recommended.py**: user-user recommendation based on user similarities
- **builder_utils.py**: helper functions for matrix normalization, cosine similarity calculation...
- **funk_svd_model.py**: ***PyTorch*** implementation of ***FunkSVD model***
- **prediction_error.py**: film recommendation ***precision*** and ***recall*** metrics calculation

## Book with code examples and all the algorithms explained in details:

Practical Recommender Systems 1st Edition https://www.amazon.com/Practical-Recommender-Systems-Kim-Falk/dp/1617292702
