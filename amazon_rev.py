from bs4 import BeautifulSoup
from urllib2 import urlopen

product_asin = "B011RG8SOU"
amazon_link = "http://www.amazon.in/product-reviews/B011RG8SOU/ref=cm_cr_pr_viewopt_srt?ie=UTF8&showViewpoints=1&sortBy=helpful&pageNumber=%d"


def main():
    li = []
    for i in xrange(1, 11):
        url_ = amazon_link % i
        print "Trying " + url_ + " now!"
        soup = BeautifulSoup(urlopen(url_).read())

        for row in soup('span', {'class': 'review-text'}):
            li.append(row.text)

if __name__ == '__main__':
    main()
