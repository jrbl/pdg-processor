import csv
import random
import time
import sys

from invenio.search_engine import perform_request_search as search

letters = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

# TODO read file from URL

# read data from file, parsing w/ csv
#codesList = csv.reader(open('pdg_codes.csv', 'rb'), delimiter=',', quotechar='"', skipinitialspace=True)
codesList = csv.reader(open('broken_input.txt', 'rb'), delimiter=',', quotechar='"', skipinitialspace=True)
  # TODO de-reference INSPIRE refs as we read them in

def move_around_letters(journal,volume,pages):
    """Move around the letter attached of a volume or page ref seeking unique

    Sometimes volume letters for a coden reference get put in the wrong place:
    they're on the page when they should be on the volume, or they're at the
    front of the volume when they should be at the back (or vice versa).  
    Here we try moving the letters around until we've gotten exactly 0 hits for
    various permutations or we find a unique result.

    If we find no unique result, throw the volume letter away altogether.
    """

    def permutations(journal,volume,pages,letter):
        yield journal,letter+volume,pages
        yield journal,volume+letter,pages
        yield journal,volume,letter+pages
        yield journal,volume,pages+letter

    letter = ''
    if volume[0] in letters:
        letter = volume[0]
        volume = volume[1:]
    elif volume[-1] in letters:
        letter = volume[-1]
        volume = volume[:-1]
    elif pages[0] in letters:
        letter = pages[0]
        pages = pages[1:]
    elif pages[-1] in letters:
        letter = pages[-1]
        pages = pages[:-1]

    for j,v,p in permutations(journal,volume,pages,letter):
        hits = list(search(p='find j ' + ','.join([j,v,p])))
        if len(hits) == 1:
            return j,v,p,hits
    return journal,volume,pages,None
    

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
    search_str   = None
    hits         = None
    journal      = line[0].strip().upper()
    if journal.startswith('#'):             # skip comments
        return None,None,None
    volume,pages = [x.strip().upper() for x in line[1:3]]
    codes        = [x.strip().lower() for x in line[3:]]
    if volume or pages:
        search_str = 'find j ' + ','.join([journal,volume,pages])
        hits = list(search(p=search_str))
        # swap letters position if 0 hits
        if len(hits) == 0:
            journal,volume,pages,new_hits = move_around_letters(journal,volume,pages)
            if new_hits:
                hits = new_hits
            search_str = 'find j ' + ','.join([journal,volume,pages])
    else:
        search_str = 'find irn ' + journal
        hits = list(search(p=search_str))
    return search_str,hits,codes
    

# TODO turn refs in file into marcxml
DEBUGCOUNT = 0
outfile = open('output.txt', 'wb')
errambfile = open('errors_amb.txt', 'wb')
errmissingfile = open('errors_missing.txt', 'wb')
for codes in codesList:
    hits = None
    DEBUGCOUNT += 1
    if DEBUGCOUNT % 100 == 0: 
        #sys.exit()
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
