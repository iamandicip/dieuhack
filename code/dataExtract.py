
import os
import ordered_set
import csv


def merge_csv(files=('issuer.csv', 'guarantor.csv', 'roc.csv', 'zcp.csv', 'minTrad.csv', 'mltTrad.csv', 'optCur.csv')):
    newd={}
    for file in files:
        with open(file,'r') as f:
            f = csv.reader(f)
            for item in f:
                if item[0] not in newd:
                    newd[item[0]]=[item[1]]
                else:
                    newd[item[0]].append(item[1])

    with open('final.csv','w') as f:
        writer = csv.writer(f,delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(['ISIN','ISSUER.NAME','GA.NAME','ROC','ZCP.FL','MIN.TRAD.AMT','MLT.TRAD.AMT','OPS.CURR'])
        for item in newd:
            tmp = newd[item]
            tmp.insert(0,item)
            writer.writerow(tmp)

    print('Done')


def to_csv(filename, data):
    '''
    filename = name of the file
    data = a dict with key == isin and string as value.
    '''
    with open(filename,'w') as f:
        writer = csv.writer(f,delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_ALL)
        for item in data:
            writer.writerow([item,data[item]])

class data(object):

    def __init__(self,folder='../Newdata/train/',):

        type = folder.strip('/').split('/')[-1]
        if type == 'train':
            docidf = os.path.join(folder,'docID/docid_train.csv')
            guarantorf = os.path.join(folder,'outcome/guarantor_train.csv')
            isinf = os.path.join(folder,'outcome/ISIN_train.csv')
            rocf = os.path.join(folder,'outcome/ROC_train.csv')
        elif type == 'int_test':
            docidf = os.path.join(folder,'docID/docid_int_test.csv')
            guarantorf = None
            isinf= None
            rocf = None
        else:
            raise ValueError('Only train and int_test folder can be use.')

        self.docid = {}
        self.guarantor = {}
        self.issuer = {}
        self.zcp = {} # zero coupon flag
        self.minTrad = {}
        self.mltTrad = {}
        self.optCur = {}
        self.roc = {}

        with open(docidf) as f:
            f=csv.reader(f)
            #line = f.next()
            next(f)
            for tmp in f:
                if tmp[1] in self.docid:
                    self.docid[tmp[1]].add(tmp[0])
                else:
                    self.docid[tmp[1]]=ordered_set.OrderedSet((tmp[0],))

        if guarantorf is not None:
            with open(guarantorf) as f:
                f = csv.reader(f)
                #line = f.next()
                next(f)
                for tmp in f:
                    if tmp[1] != '':
                        if tmp[0] in self.guarantor:
                            self.guarantor[tmp[0]].add(tmp[1])
                        else:
                            self.guarantor[tmp[0]]=ordered_set.OrderedSet((tmp[1],))
                    else:
                        self.guarantor[tmp[0]] = ordered_set.OrderedSet()

        if rocf is not None:
            with open(rocf) as f:
                f = csv.reader(f)
                #line = f.next()
                next(f)
                for tmp in f:
                    if tmp[1] != '':
                        if tmp[0] in self.roc:
                            self.roc[tmp[0]].add(tmp[1])
                        else:
                            self.roc[tmp[0]]=ordered_set.OrderedSet((tmp[1],))
                    else:
                        self.roc[tmp[0]] = ordered_set.OrderedSet()

        if isinf is not None:
            with open(isinf) as f:
                f = csv.reader(f)
                #line = f.next()
                next(f)
                for tmp in f:
                    if tmp[0] in self.issuer:
                        self.issuer[tmp[0]].add(tmp[1])
                    else:
                        self.issuer[tmp[0]]=ordered_set.OrderedSet((tmp[1],))

                    if tmp[0] in self.zcp:
                        self.zcp[tmp[0]].add(tmp[2])
                    else:
                        self.zcp[tmp[0]] = ordered_set.OrderedSet((tmp[2],))

                    if tmp[0] in self.minTrad:
                        self.minTrad[tmp[0]].add(tmp[3])
                    else:
                        self.minTrad[tmp[0]] = ordered_set.OrderedSet((tmp[3],))

                    if tmp[0] in self.mltTrad:
                        self.mltTrad[tmp[0]].add(tmp[4])
                    else:
                        self.mltTrad[tmp[0]] = ordered_set.OrderedSet((tmp[4],))

                    if tmp[0] in self.optCur:
                        self.optCur[tmp[0]].add(tmp[5])
                    else:
                        self.optCur[tmp[0]] = ordered_set.OrderedSet((tmp[5],))

        self.torm=set()
        if guarantorf is not None:
            for isin in self.docid:
                if isin not in self.guarantor:
                    self.torm.add(isin)

                if isin not in self.issuer:
                    self.torm.add(isin)

                if isin not in self.zcp:
                    self.torm.add(isin)

                if isin not in self.minTrad:
                    self.torm.add(isin)

                if isin not in self.mltTrad:
                    self.torm.add(isin)

                if isin not in self.optCur:
                    self.torm.add(isin)

                if isin not in self.roc:
                    self.torm.add(isin)

        for item in self.torm:
            del self.docid[item]


def test(prediction, answer):
    '''
    Test the prediction.

    prediction, ansewer: dic with isin as key and string as values.
    '''
    total = float(len(answer))
    err = 0.0
    notcomp = 0.0
    for item in answer:
        if item in prediction:
            if prediction[item] != answer[item]:
                err += 1
        else:
            notcomp += 1

    print
    print('total number of set compared: ' + str(total))
    print('total number of missing set: ' + str(notcomp))
    print('error %: ' + str(err / total * 100))