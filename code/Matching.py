
import ordered_set
import numpy as np
import itertools
from collections import defaultdict
import copy
from fuzzywuzzy import process
import cPickle as pickle

class fuzzCompany(object):
    """
    Class to match the company name.
    """

    def __init__(self, values, synonymes, common=None):
        '''

        Args:
            values: list with all the company name of interest
            synonymes: list of pair of word that link a word of a sequance from the
                        company name to the reference name.
            common: list with additional value to be added to the list of the most common name
                    to be rejected for the primary vocabulary.
        '''
        self.ponctuation = '().,:!?\'%*-_&@$;[]{}'
        self._common = {'th', 'a', 'the', 'be', 'to', 'of', 'and', 'in',}
        #'bank','issuer','group',
        #                'international','guarantor','ag','sa','inc','llc','plc','securities'}

        if common is not None:
            self._common.update(common)
        self.values = ordered_set.OrderedSet(values)
        self.primary_voc = ordered_set.OrderedSet()

        # create the primary_voc
        for item in values:
            for voc in item.split(' '):
                tmp = voc.lower()  # remove punctuation
                for c in self.ponctuation:
                    tmp = tmp.replace(c,'')

                if len(tmp) > 1:
                    if tmp not in self._common: # do not take into account very common words which are misleading.
                        self.primary_voc.add(tmp)

        self.pvocLookup = {} # for fast retrieval of the index
        for x in xrange(0,len(self.primary_voc)):
            self.pvocLookup[self.primary_voc[x]] = x

        # create the vector matrix, one word per line.
        self.primary_vector = np.zeros((len(self.values),len(self.primary_voc)))
        x = 0
        for item in values:
            for voc in item.split(' '):
                tmp = voc.strip(self.ponctuation).lower()  # remove punctuation
                if tmp in self.pvocLookup:
                    self.primary_vector[x,self.pvocLookup[tmp]] = 1
            x += 1

        # normalize column, more a word is common, lesser should its weight be, therefore by normalizing the
        # column we reduce the weight of the word that are repeated.
        n=np.linalg.norm(self.primary_vector,axis=0)
        self.primary_vector /= n
        # now we normalize the lines.
        n=np.linalg.norm(self.primary_vector,axis=1)
        self.primary_vector = self.primary_vector.transpose() / n
        self.primary_vector = self.primary_vector.transpose()

        # now create the secondary voc based on the fist one.
        #'GREAT WINCHE' >== 'london'
        # BISHOPSGATE <== london
        # JPMORGAN ==> J.P. MORGAN

        # construct the list of new words and order the tuples

        self.secondary_voc = ordered_set.OrderedSet()
        self.secondary_vector = []
        for item in synonymes:
            vec=self.get_prim_vector(item[0])
            sec = item[1]
            if vec is None:
                vec = self.get_prim_vector(item[1])
                sec = item[0]
                if vec is None:
                    print 'The folloing synonymes has no ref to the primary vocabulary: ',item
                    continue
            if sec not in self.secondary_voc:
                self.secondary_voc.add(sec)
            else:
                vec += self.secondary_vector[self.secondary_voc.index(sec)]
                n = np.linalg.norm(vec)
                vec /= n
            self.secondary_vector.append(vec)

        self.secondary_vector = np.array(self.secondary_vector)
        self.svocLookup = {} # for fast retrieval of the index
        for x in xrange(0,len(self.secondary_voc)):
            self.svocLookup[self.secondary_voc[x]] = x


    def get_prim_vector(self,words):
        """
        Provide a primary vector representation of the words provided,

        The vector is normalized.

        This vector is primary ! it means it is only based on the primary
        vecabulary, all the the word that are not in there are skipped and
        if the vector is nul, None is returned.
        """
        vec = np.zeros(self.primary_vector.shape[1])
        for word in words.split(' '):
            tmp = word.lower()  # remove punctuation
            for c in self.ponctuation:
                tmp = tmp.replace(c, '')
            if tmp in self.pvocLookup:
                vec[self.pvocLookup[tmp]] = 1
        n = np.linalg.norm(vec)
        if n == 0:
            return None
        else:
            return vec / n

    def get_vector(self,words):
        '''
        Get a vector representation based on the full vocabulary.
        the provided vector is normed.

        Return None if no word in words is known from the vocabulary.
            else, it returned a vecotrial representation if this words.
        '''
        vec = np.zeros(self.primary_vector.shape[1])

        for word in words.split(' '):
            tmp = word.strip(self.ponctuation).lower()  # remove punctuation
            if tmp in self.pvocLookup: # if in the primary voc, only put a one on the right position
                vec[self.pvocLookup[tmp]] = 1
            if tmp in self.svocLookup: # if on the secondary, need to add the vector that represent
                                       # this word in the primary voc
                vec += self.secondary_vector[self.svocLookup[tmp],:]

        n = np.linalg.norm(vec)
        if n == 0:
            return None
        else:
            return vec / n


    def closerMatch(self,words, tol=0.8):
        '''
        Return the company that match the closest to words and the value of the matching (beteen O and 1)
        Return None is not company match.
        '''
        length = len(set(words.split()))
        vec = self.get_vector(words)
        if vec is None:
            return None
        else:
            val = np.dot(self.primary_vector,vec)
            maxidx = np.argmax(val)
            val = val[maxidx]
            # modulate the value in function of the number of words
            # matching.
            mod = float(len(set(self.values[maxidx].split()))) / length
            if mod > 1:
                mod = 1 / mod
            #print mod, length, float(len(self.values[maxidx].split()))
            return self.values[maxidx], val * mod


class fuzzCompany2(object):
    """
    Class to match the company name.
    """

    def __init__(self, values, synonymes):
        '''

        Args:
            values: list with all the company name of interest
            synonymes: list of pair of word that link a word or a sequence from the
                        name to match to the reference name.
        '''
        self.values = ordered_set.OrderedSet(values)
        self.synonymes = ordered_set.OrderedSet(synonymes)
        self.ponctuation = '().,:!?\'%*-_&@$;[]{}'

        self.vocab = ordered_set.OrderedSet()
        for item in values:
            # remove punctuation and lower case
            tmp = item.lower()
            for c in self.ponctuation:
                tmp = tmp.replace(c, '')

            for voc in tmp.split(' '):
                if len(voc) > 0:
                    self.vocab.add(voc)

        # for item in synonymes:
        #     for words in item:
        #         for voc in words.split(' '):
        #             tmp = voc.strip(self.ponctuation).lower() # remove punctuation
        #             if len(tmp) > 0:
        #                 self.vocab.add(tmp)


        self.Lookup = dict() # for fast retrieval of the index
        for x in xrange(0,len(self.vocab)):
            self.Lookup[self.vocab[x]] = x

        self.vector = []
        self.l = []
        for item in values:
            v, l = self.to_numberset(item)
            self.vector.append(v)
            self.l.append(l)

        self.sumkVal=[]
        for item in self.vector:
            self.sumkVal.append(self._sumk(item))

    def get_subsets(self,l):
        result = defaultdict(ordered_set.OrderedSet)
        ll = len(l)
        for y in xrange(0,ll):
            for x in xrange(y,ll):
                if x == y:
                    result[x - y + 1].add((l[x],))
                else:
                    tmp = list(result[x - y][-1])
                    tmp.append(l[x])
                    result[x - y + 1].add(tuple(tmp))
        return result


    def to_numberset(self, word):
        '''
        return a number set version of the string. Each word is replace by a number
        which is the position of this word in vocab. if the word is not in the vocab,
        -1 is put. Then return a set of combination of these number.
        '''
        result = []
        l = 0.0
        tmp = word.lower()  # remove punctuation
        for c in self.ponctuation:
            tmp = tmp.replace(c, '')
        for w in tmp.split(' '):
            if len(tmp) > 0:
                l += 1
                if tmp in self.Lookup:
                    result.append(self.Lookup[tmp])
                else:
                    result.append(-1)
                #ans, val = process.extractOne(tmp, self.Lookup.keys())
                #if val >= 0.95:
                #    result.append(self.Lookup[ans])
                #else:
                #    result.append(-1)

        x=0
        while len(result) > x+1:
           if result[x] == result[x+1] == -1:
               result.pop(x)
           else:
               x += 1

        return self.get_subsets(result), l

        # # split the substring into substring.
        # x = 0
        # y = 0
        # ans = []
        # while len(result) > x + 1:
        #     if result[x] == result[x + 1] == -1:
        #         ans.append(np.array(result[y:x]))
        #         y = x+2
        #         x+=1
        #     x += 1
        #
        # result = []
        # for item in ans:
        #     r = item[item != -1]
        #     if r.shape[0] != 0:
        #         result.append(self.get_subsets(r))
        #
        # return result, float(l)


    def _sumk(self,sets):
        r = 0
        for k in sets:
          r += k**2 * len(sets[k])
        return float(r)

    def get_Ps_vect(self,toTest):
        '''
        Get the probability that the provide word match witch each word of the self.values.
        '''
        result = []
        l = float(max(toTest.keys()))

        #for item in toTest:
            #result.append([])
        for x in xrange(0,len(self.vector)):
            newset = dict()
            for k in self.vector[x]:
                newset[k] = set(self.vector[x][k]).intersection(toTest[k])
            ksum = self._sumk(newset)
            if l > 0.0:
                ll = self.l[x] / l
                if ll > 1.0:
                    ll = 1.0 / ll
                result.append(ksum / self.sumkVal[x] * ll)
            else:
                result.append(0.0)

        return result

    def get_Ps(self,word):
        '''
        Get the probability that the provide word match witch each word of the self.values.
        '''
        result = []
        toTest, l = self.to_numberset(word)

        #for item in toTest:
            #result.append([])
        for x in xrange(0,len(self.vector)):
            newset = dict()
            for k in self.vector[x]:
                newset[k] = set(self.vector[x][k]).intersection(toTest[k])
            ksum = self._sumk(newset)
            if l > 0.0:
                ll = self.l[x] / l
                if ll > 1.0:
                    ll = 1.0 / ll
                result.append(ksum / self.sumkVal[x] * ll)
            else:
                result.append(0.0)

        return result
        # # return a 0 vector if several company name are found in the words provided,
        # # if this is the case the string provide is a bad one and it is safer to return
        # # no match.
        # if len(result) == 1:
        #     return result[0]
        # else:
        #     ans = []
        #     for item in result:
        #         if np.sum(item) > 0:
        #             ans.append(item)
        #     if len(ans) == 1:
        #         return ans[0]
        #     else:
        #         return np.zeros(len(self.vector))

    def get_alt(self, words):
        '''
        Provide all the alternative string to the provided one obtaine by substitution of
        word in self.synonymes
        '''

        s=[]
        for w in words.split(' '):
            tmp = w.lower()  # remove punctuation
            for c in self.ponctuation:
                tmp = tmp.replace(c, '')
            if len(tmp) > 0:
                s.append(tmp)

        result = set((' '.join(s),))
        for sym in self.synonymes:
            old = copy.deepcopy(result)
            for s in old:
                if sym[0] in s:
                    result.add(s.replace(sym[0], sym[1]))
        return result

    def closerMatch(self, words):
        '''
        Provide the entry that match the closest
        '''
        res = []
        for w in self.get_alt(words):
            r = self.get_Ps(w)
            idx = np.argmax(r)
            res.append((r[idx],self.values[idx]))
        res = sorted(res, reverse=True)
        #print res
        return res[0]

    def save(self,filename):
        '''
        Save the object into the file
        '''
        with open(filename, 'wb') as output:
            pickle.dump(self, output)

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as pkl_file:
            return pickle.load(pkl_file)
