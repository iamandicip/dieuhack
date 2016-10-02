
import csv
import os
import copy
import collections
import re
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

class label(dict):
    # holder class based on a dict with key == isin
    # diffined function to manipulate the data.

    def __init__(self):
        '''
        create an empty dict for holding the label info.
        '''
        self.header = []

    def divide(self,pc=0.75):
        '''
        Divide the set into to set, The first one contain pc*(the number of isin in this set) and
        the second one 1-pc of this set. Return both sets.
        '''
        assert 0 < pc < 1, 'pc need to be between 0 and 1 !!!!'
        lset1 = int(pc*len(self))
        set1  ={}
        set2 = {}
        x = 0
        for item in self:
            if x >= lset1:
                set2[item] = self[item]
            else:
                set1[item] = self[item]
            x += 1
        return set1, set2


    @classmethod
    def from_cvs(cls, datafolder):
        '''
        Create a new dictionary with the all the label loaded for the labels and cities cvs
        file from the folder datafolder.

        args:
            datafolder: the folder where the labels.csv and cities.csv files are.
        '''
        assert os.path.isdir(datafolder)
        self = cls()
        l = 0
        with open(os.path.join(datafolder, 'labels.csv'), 'r') as csvfile:
            reader = csv.reader(csvfile)
            header = reader.next()
            l = len(header)
            for data in reader:
                fileid_t = data[0]
                isin_t = data[1]
                # safty check:
                if isin_t not in self:
                    if len(data) != l:
                        print 'icoherent data lengths'
                    self[isin_t] = data[2:]
                    if self[isin_t][7] != '':
                        self[isin_t][7] = self[isin_t][7].split(',')[0]
                    if self[isin_t][10] != '':
                        self[isin_t][10] = self[isin_t][10].split(',')[0]
                    self[isin_t].insert(0, [fileid_t])
                else:
                    self[isin_t][0].append(fileid_t)
                    #if self[isin_t][1:] != data[2:]:
                    #    print self[isin_t][1:]
                    #    print data[2:]
                    #    raise ValueError('inconsistancy !')
        l -= 1
        with open(os.path.join(datafolder, 'cities.csv'), 'r') as csvfile:
            reader = csv.reader(csvfile)
            header2 = reader.next()
            header = header[2:]
            header.extend(header2[2:])
            self.header = header
            self.header.insert(0, header2[0])
            print self.header
            for data in reader:
                fileid_t = data[0]
                isin_t = data[1]
                data = data[2:]

                # safty check:
                if fileid_t not in self[isin_t][0]:
                    raise ValueError('file id do not match between cities and lables !')

                if len(self[isin_t]) == l:  # still no cites
                    self[isin_t].extend([[data[0]], [data[1]]])
                else:
                    self[isin_t][-2].append(data[0])
                    self[isin_t][-1].append(data[1])

        for item in self:
            if len(self[item]) < len(self.header):
                self[item].extend([None, None])

        return self

    @classmethod
    def from_folder(cls, datafolder, header):
        '''
        Initialize the dictionary with all the files in the given folder. The files are not read,
        this method only import all the files names and extract the isin from the name of
        the file is possible for each of them, and the array
        of data is initialized for each of the isin, all the data are initialized to None (apart for the
        filepath... ).

        if the isin is unknow, the files are append to the list self.unknown

        The files are expected to be formatted as (fileid)_i(isin)_(stuff...)

        args:
            datafolder: folder where the data are.
            header: header for the data, this is the label for each of the element stored for each isin.
                    the first data is always the 'fileId', so you should always have the label as a fist
                    element of your header.
                    e.g: header= ['fileId', 'NOMINAL.CURR', 'MIN.TRAD.AMT', 'MULT.TRAD.AMT', 'ZERO.COUPN.FLAG',
                    'SEC.SUB.ID', 'FUNG.FL', 'OpCurrency', 'issuerName', 'issuerCity', 'issuerCountry',
                    'guarantorName', 'guarantorCity', 'guarantorCountry', 'City.Id', 'City.Name']

        '''
        assert os.path.isdir(datafolder)
        self = cls()
        self.header = header
        self.unknown = []
        for filename in os.listdir(datafolder):
            isin = re.findall('[a-zA-Z][a-zA-Z][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]', filename)
            if len(isin) > 1:
                raise ValueError('multpiple isin !')
            elif len(isin) == 1:
                if isin[0] in self:
                    self[isin[0]][0].append(filename)
                else:
                    self[isin[0]] = [[filename]]
                    self[isin[0]].extend([None] * (len(self.header) - 1))
            # isin=filename.split('_')[1]
            # if 'I' == isin[0].upper():
            #    if isin[1:] in self:
            #        self[isin[1:]][0].append(filename)
            #    else:
            #        self[isin[1:]]=[[filename]]
            #        self[isin[1:]].extend([None]*(len(self.header)-1))
            # elif re.match('[a-zA-Z][a-zA-Z][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]', isin):
            #    if isin in self:
            #        self[isin][0].append(filename)
            #    else:
            #        self[isin]=[[filename]]
            #        self[isin].extend([None]*(len(self.header)-1))
            else:
                self.unknown.append(filename)
        return self

    def get_headers(self):
        '''
        Return the header as a list, this is all the possible filed store for each isin.
        '''
        return copy.deepcopy(self.header)

    def get_isin(self, isin, label=None):
        '''
        Provide the data for a given isin and label, all the possible label are given by get_headers().

        args:
            isin: the isin...
            lable: data data you want for this isin, is None, all the data for this isin are returned
        '''
        if label is not None:
            assert label in self.header
            return copy.deepcopy(self[isin][self.header.index(label)])
        else:
            return copy.deepcopy(self[isin])

    def get_from_field(self, field, value):
        '''
        Return a list of isin that have the given value for the give field.

        The research is done by going through the complete list, this is therefore inefficient.

        args:
            field: one of the label in the header where to look for the value
            value: value to look for.
        '''
        result = []
        for item in self:
            tmp = self[item][self.header.index(field)]
            if tmp is not None and (tmp == value or value in tmp):
                result.append(item)
        return result

    def empty(self):
        '''
        Empty the all the data (set them to None), only keep the isin and the fileId associated.
        '''
        l = len(self.header)
        for item in self:
            for x in xrange(1, l):
                self[item][x] = None

    def get_set(self, field):
        '''
        return a set with all the possible value of this field provided.

        args:
            field: the id or label of the field
        '''
        if isinstance(field,str):
            idx=self.header.index(field)
        else:
            idx=field
        result = set()
        for item in self:
            result.add(self[item][idx])
        return result

    def evaluate(self, what, ref, printerr=True, match_ok=90):
        '''
        Compare the values from this set to a reference set with fuzzy matching.

        Only work to non list data.
        Args:
            what: index of the data to compare (see header label)
            ref: another label object to compare with.
            printerr: print not matching entity
            match_ok: threshold to accept the result.
        '''
        total = 0
        notcomp = 0
        err = np.zeros(len(what))
        lookup = dict()
        for i in xrange(0, len(what)):
            lookup[what[i]] = i

        for item in ref:
            if item not in self:
                print item + ' is not in the set !'
                notcomp += 1
            else:
                total += 1
                for idx in what:
                        if (self[item][idx] is None and (ref[item][idx] is not None or ref[item][idx] != '') ) or\
                                        fuzz.token_set_ratio(self[item][idx],ref[item][idx]) < match_ok:

                            if self[item][idx] is None or ref[item][idx] not in self[item][idx]:
                                if printerr:
                                    print item,', ', self[item][idx],', ', ref[item][idx]
                                err[lookup[idx]] += 1
        print
        print 'total number of set compared: ' + str(total)
        print 'total number of missing set: ' + str(notcomp)
        print 'total number of errors for each index: ' + str(err)
        print 'error %: ' + str(err / total * 100)
