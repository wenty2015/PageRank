import os, sys
import numpy as np
from datetime import datetime

class PageRank(object):
    def __init__(self):
        self.nodes = {} #{url_id: Node}
        self.node_map = {} # {url : url_id}
        self.N = 0

    def addNode(self, l):
        if l not in self.node_map.keys():
            l_id = self.N
            self.nodes[l_id] = Node(l)
            self.node_map[l] = l_id
            self.N += 1
            return l_id
        else:
            return self.node_map[l]

    def addEdge(self, il, ol_id):
        il_id = self.addNode(il)
        #ol_id = self.addNode(ol)
        self.nodes[il_id].addOutLink(ol_id)
        self.nodes[ol_id].addInlink(il_id)

    def printNodes(self):
        for node_id, node in self.nodes.iteritems():
            print node_id, node.url, \
                    node.out_links, node.in_links, node.out_degree

    def initiatePageRank(self):
        for node_id, node in self.nodes.iteritems():
            node.out_degree = len(node.out_links)
        self.delta = [] # delta for each iteration
        # start with each node being equally likely
        self.page_rank = np.array([1] * self.N) * 1. / self.N

    def getError(self, new_page_rank):
        diff = map(lambda x: abs(x), self.page_rank - new_page_rank)
        return np.sum(diff)

    def updatePageRank(self, w):
        # new page rank score for random jump
        new_page_rank = np.array([1] * self.N) * w / self.N

        for node_id, node in self.nodes.iteritems():
            # when there are out links, the probability of the
            #  node to other links is 1/out_degree
            if len(node.out_links) > 0:
                for ol in node.out_links:
                    new_page_rank[ol] += \
                        (1 - w) * self.page_rank[node_id] / node.out_degree
            # when there are no out links, the probability of the
            #  node to all links is 1/N
            else:
                new_page_rank += (1 - w) * self.page_rank[node_id] / self.N
        return new_page_rank

    def calculatePageRank(self, eps = 1e-6, w = .15, max_iteration = 100):
        # the default setting of w is gotten from wikipedia page for PageRank
        #   w = 1 - damping factor, where damping factor d is selected at 0.85
        self.initiatePageRank()
        new_error = 1.
        iteration = 0
        # calculate PageRank until converge
        while True:
            old_error = new_error
            # self.printNodes()
            new_page_rank = self.updatePageRank(w)
            new_error = self.getError(new_page_rank)
            delta = abs(old_error - new_error)
            print iteration, 'iterations, delta = ', delta
            iteration += 1
            self.delta.append(delta)
            # udpate the current PageRank estimate
            self.page_rank = new_page_rank
            if delta < eps or iteration > max_iteration:
                break

    def exportTopPages(self, f, topK = 500):
        # get topK nodes with top page rank scores
        top_nodes = (-self.page_rank).argsort()[:topK]
        for node_id in np.nditer(top_nodes):
            node_id = int(node_id)
            node_url = self.nodes[node_id].url
            node_page_rank = self.page_rank[node_id]
            f.write(' '.join([node_url, str(node_page_rank), '\n']))

    def exportNodes(self, f):
        for node_id, node in self.nodes.iteritems():
            in_links = list(node.in_links)
            in_links_text = '[' + ','.join(map(lambda il: str(il), in_links)) +\
                                ']'
            out_links = list(node.out_links)
            out_links_text = '[' + ','.join(map(lambda ol: str(ol), out_links)) +\
                                ']'
            f.write(' '.join([str(node_id), node.url,
                            in_links_text, out_links_text, '\n']))
    def exportDelta(self, f):
        for i, delta in enumerate(self.delta):
            f.write(' '.join([str(i), str(delta), '\n']))

class Node(object):
    def __init__(self, url):
        self.url = url
        self.in_links = set()
        self.out_links = set()
        self.out_degree = 0

    def addInlink(self, il):
        self.in_links.add(il)

    def addOutLink(self, ol):
        self.out_links.add(ol)

if __name__ == '__main__':
    args = sys.argv
    if len(args) == 4:
        eps, w, max_iteration = args[1:]
    else:
        eps, w, max_iteration = 1e-6, .15, 50
        print 'check number of input, use default setup'

    now = datetime.now()

    page_rank = PageRank()
    print 'load link graph'
    #file_name = 'wt2g_inlinks.txt'
    file_name = 'merged_index_in_links.txt'
    f = open('../data/' + file_name, 'r')
    node_cnt = 0
    for line in f.readlines():
        edges = line.rstrip(' \n').split(' ')
        if len(edges) == 1:
            node = edges[0]
            page_rank.addNode(node)
        else:
            node = edges[0]
            in_links = edges[1:]
            ol_id = page_rank.addNode(node)
            for il in in_links:
                page_rank.addEdge(il, ol_id)
        node_cnt += 1
        if node_cnt % 1000 == 0:
            print 'load', node_cnt, 'lines'
    f.close()

    print 'calculate page rank'
    page_rank.calculatePageRank(eps, w, max_iteration)

    #page_rank.printNodes()
    print 'export results'
    file_pref = file_name.split('.')[0]
    f = open('../results/' + file_pref + '_top_pages.txt', 'w')
    page_rank.exportTopPages(f, 500)
    f.close()

    f = open('../results/' + file_pref + '_node_info.txt', 'w')
    page_rank.exportNodes(f)
    f.close()

    f = open('../results/' + file_pref + '_delta.txt', 'w')
    page_rank.exportDelta(f)
    f.close()

    print 'running time', datetime.now() - now
