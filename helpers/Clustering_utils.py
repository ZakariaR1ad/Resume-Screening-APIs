from sklearn.neighbors import NearestNeighbors
import pandas as pd
from keras.preprocessing.text import Tokenizer
from keras.utils import pad_sequences
from pymongo import MongoClient
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from config import settings
import re
import nltk
from nltk.stem import PorterStemmer


nltk.download('stopwords')
stop_words = nltk.corpus.stopwords.words('english')
stop_words.append("skills")
text_cleaning_re = "@\S+|https?:\S+|http?:\S+|[^A-Za-z0-9]:\S+|subject:\S+|nbsp"


client = MongoClient(f"mongodb+srv://{settings.MongoDB_username}:{settings.MongoDB_password}@{settings.MongoDB_id}/?retryWrites=true&w=majority")
db = client.test


def preprocess(text, stem=False):
    stemmer = PorterStemmer()
    text = re.sub(text_cleaning_re, ' ', str(text).lower()).strip()
    tokens = []
    for token in text.split():
        if token not in stop_words:
            if stem:
                tokens.append(stemmer.stem(token))
            else:
                tokens.append(token)
    return " ".join(tokens)


def knn(x, data, k=5):
    nbrs = NearestNeighbors(n_neighbors=min(k, max(len(data)-1, 1)), algorithm='ball_tree').fit(data)
    distances, indices = nbrs.kneighbors(x.reshape(1, -1))
    return distances, indices


def format_data(data, isString= False):
    try:
        skills = list(db.resumes.find({})) + list(db.formatted_resumes.find({}))
        skills_dic = [skill["cluster"] for skill in skills]
        if not isString:
            skills = [skill["skills"] for skill in skills]+[data.skills]
        else:
            skills = [skill["skills"] for skill in skills]+[data]
        skills = pd.Series([preprocess(skill, True) for skill in skills])
        tokenizer = Tokenizer()
        tokenizer.fit_on_texts(skills)
        skills_set = pad_sequences(tokenizer.texts_to_sequences(skills), maxlen=50)
        x = skills_set[-1]
        print(x)
        return x, skills_set, skills_dic
    except:
        print("Connection to database failed")
        return None, None, None


def find_cluster(data, x, data_dict):
    distances, indices = knn(x, data)
    vote = [data_dict[i-1] for i in indices[0]]
    cluster = max(set(vote), key=vote.count)
    return cluster


def find_cluster_from_resume(resume):
    x, data, data_dict = format_data(resume)
    return find_cluster(data, x, data_dict)


def find_cluster_from_skills(skills):
    x, data, data_dict = format_data(skills, True)
    return find_cluster(data, x, data_dict)

#To add
def gzip_approach():
    pass
