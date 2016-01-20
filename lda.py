from pymongo import MongoClient
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
import numpy as np
from gensim import corpora,similarities,models


client = MongoClient('mongodb://localhost:27017/')
db = client.revmine
reviews = db.reviews
done = db.done
queue = db.queue
recom = db.recom

arr = []
titles = []

tokenizer = RegexpTokenizer(r'\w+')
stop = stopwords.words('english')

for i in reviews.find():
    titles.append(tokenizer.tokenize(i['title'].lower()))
    for j in range(1,50,1):
        arr.append(tokenizer.tokenize(i[str(j)].lower()))

for i in titles:
    for j in i:
        stop.append(j)

for i in range(1,len(arr),1):
    arr[i] = [w for w in arr[i] if (not w in stop and not w.isdigit())]

dictionary = corpora.Dictionary(arr)
dictionary.filter_extremes(no_below=2, no_above=0.7)
corpus = [dictionary.doc2bow(text) for text in arr]

num_topics = 5

try:
    m = models.LdaModel(corpus,id2word=dictionary,num_topics=num_topics,update_every=5,chunksize=10000,passes=10)
    topics_matrix = m.show_topics(formatted=False, num_words=10)
    topics_matrix = np.array(topics_matrix)
    keywordArray = topics_matrix[:,:,1]
    keywordArrayProb = topics_matrix[:,:,0]

except:
    pass

print topics_matrix
