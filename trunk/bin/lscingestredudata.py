#!/usr/bin/env python
description = "> Ingest reduced data "
usage = "%prog  -e epoch -T telescope"

import string
import re, sys
from optparse import OptionParser
import datetime
import lsc

if __name__ == "__main__":
    parser = OptionParser(usage=usage, description=description, version="%prog 1.0")
    parser.add_option("-T", "--telescope", dest="telescope", default='all', type="str")
    parser.add_option("-e", "--epoch", dest="epoch", default='20121212', type="str",
                      help='-e epoch \t [%default]')
    # parser.add_option("-f", "--force",dest="force",action="store_true")
    parser.add_option("-f", "--force", dest="force", default='no', type="str",
                      help='force ingestion \t [no/yes/update] \n')
    parser.add_option("-m", "--missing", dest="missing", action="store_true")
    parser.add_option("-t", "--type", dest="type", default='raw', type="str",
                      help='type -t type \t [raw/reduced] \n')
    parser.add_option("--object", dest="object", default='', type="str",
                      help='type --object object \t [name] \n')

    option, args = parser.parse_args()
    if option.type not in ['raw', 'redu']:  sys.argv.append('--help')
    if len(sys.argv) < 2:
        sys.argv.append('--help')
    if option.force not in ['no', 'yes', 'update']:
        sys.argv.append('--help')
    option, args = parser.parse_args()
    _telescope = option.telescope
    _object = option.object
    epoch = option.epoch
    _force = option.force
    _missing = option.missing
    if not _missing:
        _missing = False
    else:
        _force = True
    _type = option.type

    hostname, username, passwd, database = lsc.mysqldef.getconnection('lcogt2')
    conn = lsc.mysqldef.dbConnect(hostname, username, passwd, database)

    if not _missing:
        if '-' not in str(epoch):
            epoch0 = datetime.date(int(epoch[0:4]), int(epoch[4:6]), int(epoch[6:8]))
            pippo = lsc.mysqldef.getlistfromraw(conn, 'photlcoraw', 'dayobs', str(epoch0), '', '*', _telescope)
        else:
            epoch1, epoch2 = string.split(epoch, '-')
            start = re.sub('-', '', str(datetime.date(int(epoch1[0:4]), int(epoch1[4:6]), int(epoch1[6:8]))))
            stop = re.sub('-', '', str(datetime.date(int(epoch2[0:4]), int(epoch2[4:6]), int(epoch2[6:8]))))
            pippo = lsc.mysqldef.getlistfromraw(conn, 'photlcoraw', 'dayobs', str(start), str(stop), '*',
                                                _telescope)
        listingested = [i['filepath']+i['filename'] for i in pippo if (i['objname'] == _object or not _object)]
    else:
        if '-' not in str(epoch):
            epoch0 = re.sub('-', '', str(datetime.date(int(epoch[0:4]), int(epoch[4:6]), int(epoch[6:8]))))
            pippo = lsc.mysqldef.getmissing(conn, epoch0, '', _telescope, 'photlco')
        else:
            epoch1, epoch2 = string.split(epoch, '-')
            pippo = lsc.mysqldef.getmissing(conn, epoch1, epoch2, _telescope, 'photlco')
            print pippo
            print 'here'
        print pippo
        listingested = [i['filepath']+i['filename'] for i in pippo if (i['objname'] == _object or not _object)]

    lsc.mysqldef.ingestredu(listingested, _force, 'photlco')
