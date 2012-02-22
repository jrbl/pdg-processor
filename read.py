import csv
import random
import time
import sys

from invenio.search_engine import perform_request_search as search

letters = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

# TODO read file from URL

# read data from file, parsing w/ csv
codesList = csv.reader(open('pdg_codes.csv', 'rb'), delimiter=',', quotechar='"', skipinitialspace=True)
  # TODO de-reference INSPIRE refs as we read them in

def get_ref_hits_codes(line):
    """Return a search, its result set, and the set of PDG codes to attach

    Returns a tuple consisting of
    * reference - the spires-syntax search which will get the desired document
                  may be a STRING or NONE
    * hits - the set of records responsive to the reference search
             may be a LIST or NONE
    * codes - the collection of PDG code designations to be assigned to the 
              unique record specified by hits.  maybe a LIST of STRINGS or NONE
    """
    ref = None
    hits = None
    if line[0].strip().startswith('#'):             # skip comments
        return None,None,None
    if line[1] or line[2]:
        ref = 'find j ' + ','.join(line[:3])
        hits = list(search(p=ref))
        # swap letters position if 0 hits
        if len(hits) == 0 and line[1][-1] in letters:
            letter = line[1][-1]
            line[1] = line[1][:-1]
            line[2] = letter + line[2]
            ref = 'find j ' + ','.join(line[:3])
            hits = list(search(p=ref))
    else:
        ref = 'find irn ' + line[0]
        hits = list(search(p=ref))
    return ref,hits,line[3:]
    

# TODO turn refs in file into marcxml
DEBUGCOUNT = 0
outfile = open('output.txt', 'wb')
errambfile = open('errors_amb.txt', 'wb')
errmissingfile = open('errors_missing.txt', 'wb')
for codes in codesList:
    hits = None
    DEBUGCOUNT += 1
    if DEBUGCOUNT % 100 == 0: 
        sys.exit()
        time.sleep(random.randint(1,9))
        print "100 records processed"

    ref,hits,codes = get_ref_hits_codes(codes)
    if ref == None:
        continue

    output = '' + ref + '|' + str(len(hits)) + '|' + str(codes)
    if len(hits) == 0:
        output += "|#BAD REF MISSING"
        errmissingfile.write(ref + '\n')
    elif len(hits) > 1:
        output += "|#BAD REF AMBIGUOUS"
        errambfile.write(ref + '\n')
    else:
        output += '|' + str(list(hits)[0]) + "#REF OK"

    outfile.write(output + '\n')

# TODO output marcxml for bibupload (update not replace)

outfile.close()
errambfile.close()
errmissingfile.close()
