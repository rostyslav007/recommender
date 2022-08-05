import spacy
from gensim.models import LdaModel, LdaMulticore
from gensim.corpora.dictionary import Dictionary
from gensim.test.utils import datapath
import nltk
from nltk.stem import PorterStemmer
from string import punctuation
import matplotlib.pyplot as plt
import mysql.connector
from builder_utils import load_content_df
from pyLDAvis import gensim
import pyLDAvis
import os
import pandas as pd
import numpy as np
import re
from builder_utils import cosine_similarity_items

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

from nltk.stem import WordNetLemmatizer

train = False
N_TOPICS = 10

temp_file = datapath("C:/Users/roxa0/Documents/WorkSpace/Apps/RecommendApp/builder/models/lda_model")
dictionary_file = './models/dictionary.npy'
out_file_ids = './data/ids.npy'
out_file_matrix = './data/film_topic_matrix.npy'

connector = mysql.connector.connect(
	user='root',
	password='7xt73k9x&xxa',
	host='localhost',
	database='recommendation'
)

punctuation = '[\!"#\$%&\'\(\)\*\+\,-\./:;<=>\?@\[\]\^_`\{|\}~]'

stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

nlp = spacy.load("en_core_web_sm")
stop_words = nlp.Defaults.stop_words

content_df = load_content_df(connector)

def tokenize(text):
	text = text.lower()
	text = re.sub(punctuation, ' ', text)
	text = re.sub(' {2,}', ' ', text)
	return [lemmatizer.lemmatize(token.text) for token in nlp(text) if not token.text in stop_words and len(token.text) > 2]


if (train):

	overviews = pd.read_csv('../static/data/overviews.csv')
	film_descriptions = list(overviews.overview)[:43000]
	
	film_descriptions = [tokenize(desc) for desc in film_descriptions]

	dictionary = Dictionary(film_descriptions)

	corpus = [dictionary.doc2bow(desc) for desc in film_descriptions]

	print('model train')
	model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=N_TOPICS, random_state=40)
	print('Training finished')

	# Save model and dictionary to disc
	dictionary.save(dictionary_file)
	model.save(temp_file)

	print('model and dictionary saved')

	vis = gensim.prepare(model, corpus, dictionary)
	pyLDAvis.show(vis)
	
else:

	dictionary = Dictionary.load(dictionary_file)
	model = LdaModel.load(temp_file)
	print('model loaded')

	my_overviews = []
	film_ids = []
	for i in range(content_df.shape[0]):
		row = content_df.iloc[i, :]
		desc = row['short_desc']
		film_ids.append(row['id'])
		my_overviews.append(desc)

	film_count = len(film_ids)

	id2row = {film_ids[i]: i for i in range(film_count)}
	row2id = {value: key for key, value in id2row.items()}

	my_descriptions = [tokenize(desc) for desc in my_overviews]
	my_corpus =  [dictionary.doc2bow(desc) for desc in my_descriptions]

	film_encoding_matrix = np.zeros(shape=(film_count, N_TOPICS))

	for i, d in enumerate(my_corpus):
		topic_proba = model.get_document_topics(d)
		for j, proba in topic_proba:
			film_encoding_matrix[i, j] = proba

	film_ids = np.array(film_ids)

	np.save(out_file_ids, film_ids)
	np.save(out_file_matrix, film_encoding_matrix)
	print('matrix and ids saved')


