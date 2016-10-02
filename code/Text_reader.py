

# function to read text from the files.

import os
import tempfile
import Image
import StringIO
import re
from bs4 import BeautifulSoup

try:
    import PythonMagick
except:
    print 'The PythonMagick package is missing, get_text_adv function can not be used '

try:
    from pytesseract import image_to_string
except:
    print 'The pytesseract package is missing, get_text_adv function can not be used'
    print 'You will also need to install tesseract itself ...'

try:
    import PyPDF2
except:
    print 'The PyPDF2 package is missing, get_text_adv function can not be used '

try:
    import html2text
except:
    print 'The html2text package is missing, get_text_adv and get_text functions can not be used.'
    print 'Please consider the instalation of this package !'

def parse_rows(rows):
    """ Get data from rows """
    results = []
    for row in rows:
        table_headers = row.find_all('th')
        if table_headers:
            results.append([headers.get_text() for headers in table_headers])

        table_data = row.find_all('td')
        if table_data:
            results.append([data.get_text() for data in table_data])
    return results

# https://codereview.stackexchange.com/questions/60769/scrape-an-html-table-with-python
def get_table(soup):

    # Get table
    try:
        tables = soup.findAll('table')
    except AttributeError as e:
        print 'No tables found, exiting'
        return 1

    # Get rows
    lines = []
    for table in tables:
        try:
            rows = table.find_all('tr')
        except AttributeError as e:
            print 'No table rows found, exiting'
            return 1

        # Get data
        lines.extend(parse_rows(rows))
    return lines


class htmlDoc(object):

    def __init__(self,filename):

        with open(filename,'r') as f:
            txt = f.read().decode('ascii', errors='ignore')

        self.filename = filename
        # if in the file name ...
        self.fileId = os.path.basename(filename).split('_')
        if len(self.fileId) > 0:
            self.fileId = self.fileId[0]
        else:
            self.fileId = None

        self.isin = re.findall('[a-zA-Z][a-zA-Z][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]', filename)
        if len(self.isin) > 0:
            self.isin = self.isin[0]
        else:
            self.isin = None

        soup = BeautifulSoup(txt, 'html.parser')
        self.table = get_table(soup)
        self.raw = txt
        self.list = []
        self.title = soup.title.string

        flags = []
        for x in xrange(0, 10):
            flags.append('h' + str(x))
        for x in xrange(0, 10):
            flags.append('s' + str(x))

        self.titles = []
        for flag in flags:
            a = soup.findAll(flag)
            for item in a:
                self.titles.append(item.string)

        li = soup.findAll('li')
        for item in li:
            t = []
            for i in item:
                s = i.getText(separator=' ', strip='True')
                if len(s) > 0:
                    t.append(s)
            self.list.append(t)

        [s.extract() for s in soup('table')]
        [s.extract() for s in soup('li')]
        tmp = soup.find('body')
        t = tmp.getText(separator='\n')

        # normalize the punctuation.
        t = re.sub('[\t\n\s]\([\t\n\s]*', ' (', t)
        t = re.sub('[\t\n\s]\)[\t\n\s]*', ') ', t)
        t = re.sub('[\t\n\s]*:[\t\n\s]*', ': ', t)
        t = re.sub('[\t\n\s]*\.', r'.', t)
        t = re.sub('[\t\n\s]*\,[\t\n\s]*([a-zA-z])', r', \1', t)
        t = re.sub('[\t\n\s]*\.[\t\n\s]*([0-9])', r'.\1', t)
        t = re.sub('[\t\n\s]*\,[\t\n\s]*([0-9])', r',\1', t)
        t = re.sub('[\t\n\s]*\;[\t\n\s]*', '; ', t)
        t = re.sub('[\t\n\s]*\"[\t\n\s]*', '"', t)
        self.txt = t


def get_files(folder):
    """
    Provide a dict with the files.
    the key of the dict are the fileid, the values are the
    path to the file.
    :return:
    """
    filelist = os.listdir(folder)
    files = {}
    for f in filelist:
        tmp=f.split('_')[0]
        if '.txt' in tmp:
            tmp=tmp.replace('.txt','')
        files[tmp] = os.path.realpath(os.path.join(folder,f))

    return files


def get_text(filename, raw=False):
    '''
    Return the text from a html file.
    Args:
        filename: file to read
        raw: True to get row html

    Return: a string with the text.
    '''
    assert os.path.isfile(filename)

    if raw:
        with open(filename, 'r') as f:
            result = f.read().decode('ascii', errors='ignore')
        return result
    else:
        with open(filename, 'r') as f:
            data = f.read().decode('ascii', errors='ignore')
        return html2text.html2text(pre_html(data))


def get_docs(folder, raw=False):
    """
    Itarator to get all the html files from a folder.

    if raw is True, the raw html code is returned.
    """
    assert os.path.isdir(folder)

    for f in os.listdir(folder):
        yield clean_text(get_text(os.path.join(folder, f), raw))


def pre_html(text):
    """
    Play with html tags befor we strip all the html tags.
    """
    text = text.replace('</tr>', '.</tr>')
    text = text.replace('</p>', '.</p>')

    return text


def clean_text(text):
    """
    Clean the text a bit,
    """
    text = text.replace('*', '')
    text = text.replace('#', '')
    text = text.replace('\t', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('&',' and ')
    text = re.sub(r'\.[\.\s]+', r'.\n\n', text)  # take care of multiple points
    text = re.sub(r'(\n)*(\s)*\|+(\s)*(\n)*', r'', text)  # clean any '|' with space en return around
    text = re.sub(r'--+', r'', text)  # remove ----- character
    text = re.sub(r'[\s\.]*:[\s\.]*', r': ', text)  # be sure tho have space around the column (:)
    text = re.sub(r'\n\s*[1-9ivx\)\(]+\s', r'\n\g<0>. ', text)
    text = text.replace('\n', ' ')
    return text


def split_text(text):
    '''
    Split the text into sentences.
    '''
    return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)


def get_text_adv(filename, isin=None):
    '''
    Recover the text from a file.
    More advanced version... does not pre or post processing on the data,
    Just remove the html tags for html files.

    After some test I thing the simple html files are better, but you are free to use this.
    PS: you need PythonMagick and from pytesseract  !

    args:
        filename: name of the file to read. Format: txt, html, pdf, doc, jpeg or png
        isin: is the isin is know and provided, check if the extracted isin match
              if not, rais an error. Also help for evaluating the quality of ocr.


    '''
    assert os.path.isfile(filename)
    if isin is None:
        isin = re.findall('[a-zA-Z][a-zA-Z][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]', filename)
        if len(isin) == 1:
            isin = isin[0]
        else:
            isin = None
    ext = filename.strip().split('.')[-1].lower()

    result = None
    if ext == 'txt':
        with open(filename, 'r') as f:
            result = f.read().decode('ascii', errors='ignore')
        return result
    elif ext == 'html':
        with open(filename, 'r') as f:
            data = f.read().decode('ascii', errors='ignore')
        return html2text.html2text(data)
    else:
        npage = 1
        notok = True
        result = StringIO.StringIO()
        if ext == 'pdf':
            # try to extract the text directly from the pdf
            pdf_im = PyPDF2.PdfFileReader(file(filename, "rb"))
            npage = pdf_im.getNumPages()
            for p in xrange(0, npage):
                pageObj = pdf_im.getPage(p)
                result.write(pageObj.extractText())
            tmp = result.getvalue()
            result.close()
            result = tmp.replace('\n', ' ')
            # test if if make sense and if we can extract the isin number, if not, this is probalby robish
            b = re.findall('[iI][sS][iI][nN].{0,30}[a-zA-Z][a-zA-Z][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]',
                           tmp)
            tmp = ' '.join(b)
            isinfound = re.findall('[a-zA-Z][a-zA-Z][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]', tmp)
            if isin is not None:
                if len(isinfound) > 0 and isin in isinfound:
                    notok = False
            else:
                if len(isinfound) > 0:
                    notok = False

        if notok:  # if it is robish, try to make an ocr...
            result = StringIO.StringIO()
            for p in xrange(0, npage):
                img = PythonMagick.Image()
                img.density("600")
                img.read(filename + '[' + str(p) + ']')
                f = tempfile.NamedTemporaryFile(mode='w+b', suffix='.jpeg')
                img.write(f.name)
                result.write(image_to_string(Image.open(f.name)))
                f.close()
            tmp = result.getvalue()
            result.close()
            result = tmp

        return result