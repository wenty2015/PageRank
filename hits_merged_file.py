from datetime import datetime
from numpy import random, sum, sqrt
import sys, os

class HITS(object):
    def __init__(self, link_graph):
        self.nodes = link_graph #{url_id: Node}
        self.root_set, self.base_set = set(), set()
        # max number of urls added to root set for each url
        self.D, self.TARGET_SIZE = 200, 10000

    def addRootSet(self, root_set):
        for node_id in root_set:
            self.root_set.add(node_id)
            self.base_set.add(node_id)
            if len(self.base_set) > self.TARGET_SIZE:
                return True
        return False

    def addBaseSet(self, base_set):
        for node_id in base_set:
            self.base_set.add(node_id)
            if len(self.base_set) > self.TARGET_SIZE:
                return True
        return False

    def expandBaseSet(self):
        # Repeat few two or three time this expansion to get a base set of about
        #   10,000 pages
        base_set = self.base_set.copy()
        new_nodes = base_set
        iteration = 0
        while len(self.base_set) <= self.TARGET_SIZE:
            print 'iteration',iteration,\
                    'size of base set is', len(self.base_set)
            for node_id in new_nodes:
                in_links = self.nodes[node_id].in_links
                out_links = self.nodes[node_id].out_links
                # For each page in the set, add all pages that the page points to
                finish_flag = self.addBaseSet(out_links)
                if finish_flag:
                    break
                # For each page in the set, obtain a set of pages that pointing
                #   to the page.
                # If the size of the set is less than or equal to D, add all
                #   pages in the set to the root set
                if len(in_links) > self.D:
                    # if the size of the set is greater than d, add an RANDOM
                    #   (must be random) set of d pages from the set to the root
                    #   set
                    random.shuffle(in_links)
                finish_flag = self.addBaseSet(in_links[:self.D])
                if finish_flag:
                    break
            # continue to process new added nodes
            new_nodes =  self.base_set - base_set
            base_set = self.base_set.copy()
            if len(new_nodes) == 0:
                print 'size of base set', len(self.base_set)
                print 'no more linked nodes'
                break
            iteration += 1

    def initializeHITS(self):
        # For each web page, initialize its authority and hub scores to 1.
        self.authority_score = {}
        self.hub_score = {}
        for node_id in self.base_set:
            self.authority_score[node_id] = 1
            self.hub_score[node_id] = 1
        self.delta = [] # [authority_score, hub_score]

    def calculateHITS(self, eps = 1e-6, max_iteration = 50):
        self.initializeHITS()
        iteration = 0
        new_authority_error, new_hub_error = 1., 1.
        while True:
            # Update hub and authority scores for each page in the base set
            #   until convergence
            old_authority_error, old_hub_error = new_authority_error, new_hub_error
            new_authority, new_hub = self.updateHITS()
            new_authority_error = self.getError(new_authority, 'authority')
            new_hub_error = self.getError(new_hub, 'hub')
            delta_authority = abs(new_authority_error - old_authority_error)
            delta_hub = abs(new_hub_error - old_hub_error)
            print iteration, 'iterations, delta_authority = ', delta_authority,\
                    ',delta_hub = ', delta_hub
            iteration += 1
            self.delta.append([delta_authority, delta_hub])
            # update authority and hub score
            self.authority_score = new_authority
            self.hub_score = new_hub
            if (delta_authority < eps and delta_hub < eps) or \
                    iteration > max_iteration:
                break

    def updateHITS(self):
        new_authority, new_hub = {}, {}
        # Authority Score Update:
        # Set each web page's authority score in the root set to the sum of the
        #   hub score of each web page that points to it
        for node_id in self.base_set:
            in_links = set(self.nodes[node_id].in_links) & self.base_set
            new_authority[node_id] = 0.
            for il in in_links:
                new_authority[node_id] += self.hub_score[il]
        # add the authority score for the rest nodes in base set
        '''for node_id in self.base_set - self.root_set:
            new_authority[node_id] = self.authority_score[node_id]'''
        # Hub Score Update:
        # Set each web pages's hub score in the base set to the sum of the
        #   authority score of each web page that it is pointing to
        for node_id in self.base_set:
            out_links = set(self.nodes[node_id].out_links) & self.base_set
            new_hub[node_id] = 0.
            for ol in out_links:
                new_hub[node_id] += self.authority_score[ol]
        # After every iteration, it is necessary to normalize the hub and
        #   authority scores.
        self.normalize(new_authority)
        self.normalize(new_hub)
        return new_authority, new_hub

    def normalize(self, d):
        # In the paper, it is said: "We maintain the invariant that the weights
        #   of each type are normalized so their squares sum to 1."
        squares_sum = sum(map(lambda x: x[1] ** 2, d.items()))
        l2 = sqrt(squares_sum)
        for node_id in d:
            d[node_id] /= l2

    def getError(self, new_dict, t):
        if t == 'authority':
            old_dict = self.authority_score
        elif t == 'hub':
            old_dict = self.hub_score
        error = 0.
        for node_id, old_score in old_dict.items():
            error += abs(old_score - new_dict[node_id])
        return error

    def exportResults(self, f, t, topK = 500):
        # Create one file for top 500 hub webpages, and one file for top
        #   500 authority webpages.
        # The format for both files should be:
        #   [webpageurl][tab][hub/authority score]\n
        if t == 'authority':
            score_dict = self.authority_score
        elif t == 'hub':
            score_dict = self.hub_score
        top_nodes = sorted(score_dict.items(), key = lambda x: - x[1])
        for node_id, score in top_nodes[:topK]:
            node_url = self.nodes[node_id].url
            f.write(node_url + '\t' + str(score) + '\n')

    def exportDelta(self, f):
        for i, delta in enumerate(self.delta):
            f.write(' '.join([str(i), ','.join(map(lambda d: str(d), delta)), '\n']))

    def exportSet(self, f, t):
        if t == 'root':
            nodes = self.root_set
        elif t == 'base':
            nodes = self.base_set

        for node_id in nodes:
            in_links = set(self.nodes[node_id].in_links) & self.base_set
            in_links_text = '[' + ','.join(map(lambda il: str(il), in_links)) +\
                                ']'
            out_links = set(self.nodes[node_id].out_links) & self.base_set
            out_links_text = '[' + ','.join(map(lambda ol: str(ol), out_links)) +\
                                ']'
            f.write(' '.join([str(node_id), self.nodes[node_id].url,
                            str(len(in_links)), str(len(out_links)),
                            in_links_text, out_links_text, '\n']))

class Node(object):
    def __init__(self, url, in_links, out_links):
        self.url = url
        self.in_links = in_links
        self.out_links = out_links

def loadLinkGraph():
    graph_file = '../results/merged_index_in_links_node_info.txt'
    f = open(graph_file, 'r')
    # link_graph: {node_id: Node}, url_map: {url: node_id}
    link_graph, url_map = {}, {}
    for line in f.readlines():
        # line: node_id url in_links out_links
        #print line.rstrip('\n').split(' ')
        node_id, url, in_links_text, out_links_text = line.rstrip(' \n').split(' ')
        in_links = getLinks(in_links_text)
        out_links = getLinks(out_links_text)
        node_id = int(node_id)
        link_graph[node_id] = Node(url, in_links, out_links)
        url_map[url] = node_id
    return link_graph, url_map

def getLinks(text):
    link_text = text.lstrip('[').rstrip(']')
    if link_text == '':
        return []
    else:
        links = link_text.split(',')
        return map(lambda l: int(l), links)

def loadRootSet():
    root_set_file = '../results/root_set.txt'
    f = open(root_set_file, 'r')
    root_set = []
    for url in f.readlines():
        root_set.append(url.rstrip('\n'))
    return root_set

if __name__ == '__main__':
    now = datetime.now()
    print 'load link graph'
    link_graph, url_map = loadLinkGraph()
    hits = HITS(link_graph)

    # get root set
    print 'add root set'
    root_set_info = loadRootSet()
    # convert to node_id
    root_set = map(lambda url: url_map[url], root_set_info)
    hits.addRootSet(root_set)
    # expand base set
    print 'expand base set'
    hits.expandBaseSet()

    print 'calculate authority and hub score'
    hits.calculateHITS()

    print 'export results'
    f = open('../results/authority_top_pages.txt', 'w')
    hits.exportResults(f, 'authority')
    f.close()
    f = open('../results/hub_top_pages.txt', 'w')
    hits.exportResults(f, 'hub')
    f.close()

    f = open('../results/authority_hub_delta.txt', 'w')
    hits.exportDelta(f)
    f.close()
    f = open('../results/root_set_node_info.txt', 'w')
    hits.exportSet(f, 'root')
    f.close()
    f = open('../results/base_set_node_info.txt', 'w')
    hits.exportSet(f, 'base')
    f.close()

    print 'running time', datetime.now() - now
