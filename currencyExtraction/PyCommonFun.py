"""
PyCommunFun
"""

# python equivalent of matlab find dfunction
def PyFind(a, func):
    return [i for (i, val) in enumerate(a) if func(val)]

# get string in between character "first" and "last"
def find_between( s, first, last ):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""


# save any object / poses problem with notebook
def save_obj(obj, name ):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)



#load any object / poses problem with notebook
def load_obj(name ):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)
