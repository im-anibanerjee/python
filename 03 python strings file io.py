#1. Word frequency from a file
def word_count(filepath):
    with open(filepath) as f:
        content = f.read()
    print(content)
    '''
    Python is a popular language for building backend systems, and Python is also
    useful for data pipelines. Many engineers use Python because Python is readable,
    Python integrates well with SQL databases, and Python has a huge ecosystem of
    libraries. Learning Python well takes real practice, not just reading about it -
    practice is what actually builds confidence. A good ETL pipeline in Python usually
    involves reading data, cleaning data, and loading data into a database. Data
    engineers often say: the data is only as good as the pipeline systems that built it.
    '''
    content = content.lower()
    print(content)
    '''
    python is a popular language for building backend systems, and python is also
    useful for data pipelines. many engineers use python because python is readable,
    python integrates well with sql databases, and python has a huge ecosystem of
    libraries. learning python well takes real practice, not just reading about it -
    practice is what actually builds confidence. a good etl pipeline in python usually
    involves reading data, cleaning data, and loading data into a database. data
    engineers often say: the data is only as good as the pipeline systems that built it.
    '''
    content = content.split()
    print(content)
    '''
    [
    'Python', 'is', 'a', 'popular', 'language', 'for', 'building', 'backend', 'systems,', 
    'and', 'Python', 'is', 'also', 'useful', 'for', 'data', 'pipelines.', 'Many', 'engineers', 
    'use', 'Python', 'because', 'Python', 'is', 'readable,', 'Python', 'integrates', 'well', 'with', 
    'SQL', 'databases,', 'and', 'Python', 'has', 'a', 'huge', 'ecosystem', 'of', 'libraries.', 
    'Learning', 'Python', 'well', 'takes', 'real', 'practice,', 'not', 'just', 'reading', 'about', 'it', '-', 
    'practice', 'is', 'what', 'actually', 'builds', 'confidence.', 'A', 'good', 'ETL', 'pipeline', 
    'in', 'Python', 'usually', 'involves', 'reading', 'data,', 'cleaning', 'data,', 'and', 'loading', 
    'data', 'into', 'a', 'database.', 'Data', 'engineers', 'often', 'say:', 'the', 'data', 'is', 
    'only', 'as', 'good', 'as', 'the', 'pipeline', 'systems', 'that', 'built', 'it.'
    ]
    '''
    result = {}
    seen = set()
    for word in content:
        word = word.strip(".,")
        if word not in seen:
            seen.add(word)
            result[word] = 1
        else:
            result[word] = result.get(word) + 1
    print(result)

filepath = 'sample.txt'
word_count(filepath)
'''
{
'python': 8, 'is': 5, 'a': 4, 'popular': 1, 'language': 1, 'for': 2, 'building': 1, 'backend': 1, 'systems': 2, 
'and': 3, 'also': 1, 'useful': 1, 'data': 6, 'pipelines': 1, 'many': 1, 'engineers': 2, 'use': 1, 'because': 1, 
'readable': 1, 'integrates': 1, 'well': 2, 'with': 1, 'sql': 1, 'databases': 1, 'has': 1, 'huge': 1, 'ecosystem': 1, 
'of': 1, 'libraries': 1, 'learning': 1, 'takes': 1, 'real': 1, 'practice': 2, 'not': 1, 'just': 1, 'reading': 2, 'about': 1, 
'it': 2, '-': 1, 'what': 1, 'actually': 1, 'builds': 1, 'confidence': 1, 'good': 2, 'etl': 1, 'pipeline': 2, 'in': 1, 
'usually': 1, 'involves': 1, 'cleaning': 1, 'loading': 1, 'into': 1, 'database': 1, 'often': 1, 'say:': 1, 'the': 2,
'only': 1, 'as': 2, 'that': 1, 'built': 1
}

note the output has: {'-': 1}, because that gets added into the set
    for word in content:
        word.strip(".,")
        if word:
            result[word] = result.get(word, 0) + 1
    print(result)
    {
    'python': 8, 'is': 5, 'a': 4, 'popular': 1, 'language': 1, 'for': 2, 'building': 1, 'backend': 1, 'systems': 2, 
    'and': 3, 'also': 1, 'useful': 1, 'data': 6, 'pipelines': 1, 'many': 1, 'engineers': 2, 'use': 1, 'because': 1, 
    'readable': 1, 'integrates': 1, 'well': 2, 'with': 1, 'sql': 1, 'databases': 1, 'has': 1, 'huge': 1, 'ecosystem': 1, 
    'of': 1, 'libraries': 1, 'learning': 1, 'takes': 1, 'real': 1, 'practice': 2, 'not': 1, 'just': 1, 'reading': 2, 'about': 1, 
    'it': 2, 'what': 1, 'actually': 1, 'builds': 1, 'confidence': 1, 'good': 2, 'etl': 1, 'pipeline': 2, 'in': 1, 
    'usually': 1, 'involves': 1, 'cleaning': 1, 'loading': 1, 'into': 1, 'database': 1, 'often': 1, 'say:': 1, 'the': 2,
    'only': 1, 'as': 2, 'that': 1, 'built': 1
    }

now there is no {'-': 1}
'''

#2. Explain in your own words
'''
because strings are immutable, 
    result += word doesn't extend result in place 
it builds an entirely new string every single iteration copying everything that came before

do that n times and you've copied roughly 1 + 2 + 3 + ... + n characters total, which is O(n²).
"".join(list_of_strings) does it in one pass, O(n), because it knows the total size upfront and allocates once 
'''

#3. CSV without pandas
import csv
def total_by_category(filepath):
    result = {}
    with open(filepath) as f:
        content = csv.DictReader(f)
        print(content)
        # <csv.DictReader object at 0x0000022ABFBF2C70>       
        for row in content:
            '''
            print(row)
            {'category': 'food', 'amount': '200'}
            {'category': 'travel', 'amount': '500'}
            {'category': 'food', 'amount': '150'}
            ....
            {'category': 'entertainment', 'amount': '15'}
            '''
            category = row['category']
            amount = row['amount']
            result[category] = result.get(category, 0) + float(amount)

    print(result)
    '''
    {'food': 517.7, 'travel': 1045.25, 'entertainment': 215.75}
    '''

filepath = 'transactions.csv'
total_by_category(filepath)  
'''
note:
csv dictreader returns an iterator, not a list
printing it directly just shows the object reference
loop through it or wrap in list() to see the actual rows

iterators (content) is a single pass (forward-only, one-row-at-a-time cursor over the file)
it converts each row it passes into a dict as it goes
once you've looped through it once, it's exhausted (cannot re-loop, reopen file again to read)
capture the rows in a list first if you need them more than once

do all the reading inside the with block
the file closes as soon as the with block ends
using the reader after that raises a closed file error
example:
    with open(filepath) as f:
        content = csv.DictReader(f)
    print(content)
    for row in content:
        print(row)
        
    ValueError: I/O operation on closed file
'''

#4. Predict, then verify
'''
with open("no_such_file.txt") as f:
    content = f.read()
print("done")
# FileNotFoundError: [Errno 2] No such file or directory: 'no_such_file.txt'
'''
try:
    with open('no_such_file.txt') as f:
        content = f.read()
except FileNotFoundError:
    content = 'no file, no content'
    print(content)
    # no file, no content
    print('done')
    # done
