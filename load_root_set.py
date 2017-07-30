from elasticsearch import Elasticsearch
import sys, os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

def getQueryURL(es, index, doc_type, size = 1000):
    # use the topic as the query
    results =  es.search(
        index = index, doc_type = doc_type, size = size,
        body = { "query":{
                    "match":{ "text":
                            "Authoritarianism Autocracy Capitalism Collaborationism Colonialism Cronyism Despotism Dictatorship Discrimination Economic depression Economic inequality Electoral fraud Famine Fascism Feudalism Imperialism Military occupation Monarchy Natural disaster Nepotism Persecution Political corruption Political repression Poverty Totalitarianism Unemployment"}
                        }
                })
    return results

if __name__ == '__main__':
    args = sys.argv
    if len(args) == 2:
        index = args[1:]
    else:
        index = 'crawler_beauty1'
        print 'use default index', index

    es = Elasticsearch()
    doc_type = 'document'

    print 'get urls for root set'
    # Obtain the root set of about 1000 documents by ranking all pages using an
    #   IR function (e.g. BM25, ES Search)
    root_set_info = getQueryURL(es, index, doc_type, 1000)
    # get the url for root set
    root_set = map(lambda d: d['_id'], root_set_info['hits']['hits'])

    print 'export root set'
    f = open('../results/root_set.txt', 'w')
    for url in root_set:
        f.write(url + '\n')
    f.close()
