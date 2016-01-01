from bs4 import BeautifulSoup
from urllib2 import urlopen
from pymongo import MongoClient
import re
import logging

# Every product seems to have a product ASIN id, when substituted in the following link, we get reviews for that product
# product_asin = "B011RG8SOU"
amazon_link = "http://www.amazon.in/product-reviews/%s/ref=cm_cr_pr_viewopt_srt?ie=UTF8&showViewpoints=1&sortBy=helpful&pageNumber=%d"

logging.basicConfig(filename='revmine.log', level=logging.DEBUG)

client = MongoClient('mongodb://localhost:27017/')

db = client.revmine
reviews = db.reviews
done = db.done
queue = db.queue
recom = db.recom


def main():
    """
    While we have Product asin codes in the mongo queue, scrape their product review pages
    and add 'also seen' products to the queue
    """
    while queue.find({}).count > 0:
        doit()

    client.close()


def extract_text(li, recom_flag):

    # Page 1 soup!
    url_ = amazon_link % (li["_id"], 1)
    print "Trying " + url_ + " now!"
    soup = BeautifulSoup(urlopen(url_).read())
    li['title'] = soup('span', {'class': 'a-text-ellipsis'})[0].a.text

    # will scrape reviews' text
    for j, row in enumerate(soup('span', {'class': 'review-text'})):
        li[str(j + 1)] = row.text

    if (recom_flag == 0):
        logging.info("adding entries to queue")
        for div in soup('div', {'class': 'description'}):
            link = div.a['href']
            logging.info("adding " + link + " to queue")
            # extracts product asin
            id = re.search(r'.*?//.*?/.*?/dp/(.*?)/.*', link)
            if (done.find({'_id': id.group(1)}).count() == 1):
                continue
            queue.insert_one({'link': link, '_id': id.group(1)})

    for i in xrange(2, 6):
        url_ = amazon_link % (li["_id"], i)
        print "Trying " + url_ + " now!"
        soup = BeautifulSoup(urlopen(url_).read())

        for j, row in enumerate(soup('span', {'class': 'review-text'})):
            li[str(j + 10*(i-1))] = row.text

    return li


def doit():

    # picking an object from the queue
    product_asin = queue.find_one()['_id']
    logging.info("Read next value from queue")

    logging.info("Start loading reviews")

    li = {}
    li["_id"] = product_asin
    li = extract_text(li, 0)

    # inserted_review = reviews.insert_one(li).inserted_id
    logging.info("reviews loaded into db for " + li['title'])

    logging.info("removing entry from queue")
    queue.remove({"_id": product_asin}, 1)

    for i in queue.find():
        li = {}
        li["_id"] = i["_id"]
        li["recom_by"] = product_asin
        li = extract_text(li, 1)

        logging.info("reviews loaded into recom for " + li['title'])
        logging.info("removing entry from queue")
        queue.remove({"_id": product_asin}, 1)
   #assert(inserted_review == product_asin)

if __name__ == '__main__':
    main()
