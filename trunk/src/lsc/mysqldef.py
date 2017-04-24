#######################################################################
def dbConnect(lhost, luser, lpasswd, ldb):
    import sys
    import MySQLdb, os, string
    try:
        conn = MySQLdb.connect(host=lhost,
                               user=luser,
                               passwd=lpasswd,
                               db=ldb)
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    return conn


def getconnection(site):
    import lsc
    connection = {'lcogt2': {}, 'iptf': {}}
    connection['lcogt2']['database'] = lsc.util.readpass['database']
    connection['lcogt2']['hostname'] = lsc.util.readpass['hostname']
    connection['lcogt2']['username'] = lsc.util.readpass['mysqluser']
    connection['lcogt2']['passwd'] = lsc.util.readpass['mysqlpasswd']

    connection['iptf']['database'] = lsc.util.readpass['ptfdatabase']
    connection['iptf']['hostname'] = lsc.util.readpass['ptfhost']
    connection['iptf']['username'] = lsc.util.readpass['ptfuser']
    connection['iptf']['passwd'] = lsc.util.readpass['ptfpasswd']

    return connection[site]['hostname'], connection[site]['username'], connection[site]['passwd'], connection[site][
        'database']


########################################################################
def querylike(query, datatable='', column='filename', likelist=[]):
    # Adds onto query a search for entries in the likelist to be within the filename.
    if datatable != '':
        datatable += "."
    if len(likelist) > 0:
        query += ' AND ( {0}{1} LIKE "%{2}%" '.format(datatable, column, likelist[0])
        for i in range(1, len(likelist)):
            query += ' OR {0}{1} LIKE "%{2}%" '.format(datatable, column, likelist[i])
        query += ")"
    return query


def querytelescope(query, telescope='all', datatable=''):
    import lsc
    if datatable != '':
        datatable += "."
    if telescope in lsc.util.site0 + ['1m0', 'fl', 'kb', '2m0', 'fs', 'spectral', 'sbig', 'sinistro']:
        # ['elp','lsc','cpt','coj','1m0','kb','fl','ogg']:
        query += " AND {0}filename LIKE '%{1}%' ".format(datatable, telescope)
    elif telescope != 'all':
        query += " AND {0}telescope = {1} ".format(datatable, telescope)
    return query


def getmissing(conn, epoch0, epoch1, telescope='all', datatable='photlco', filestr=()):
    import sys
    import lsc
    import MySQLdb, os, string
    print epoch0, epoch1, telescope, filestr
    try:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT raw.filename,raw.objname,raw.filepath FROM photlcoraw AS raw WHERE "
        if not epoch1:
            epoch1 = epoch0
        query += " raw.dayobs <= {0} AND raw.dayobs >= {1} ".format(epoch1, epoch0)
        query = querytelescope(query, telescope, datatable="raw")
        query = querylike(query, likelist=filestr)
        query += " and NOT EXISTS(select * from " + str(datatable) + " as redu where raw.filename = redu.filename)"
        print query
        cursor.execute(query)
        resultSet = cursor.fetchall()
        if cursor.rowcount == 0:
            pass
        cursor.close()
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    return resultSet


def getfromdataraw(conn, table, column, value, column2='*'):
    resultSet = getlistfromraw(conn, table, column, value, value2=None, column2=column2)
    return resultSet


def getlistfromraw(conn, table, column, value1, value2=None, column2='*', telescope='all', filestr=[]):
    import sys
    import lsc
    import MySQLdb, os, string
    try:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        if not value2:
            value2 = value1
        query = "select {0} from {1} where {2} <= '{3}' and {4} >= '{5}'".format(column2, table, column, value2, column,
                                                                                 value1)
        query = querytelescope(query, telescope)
        query = querylike(query, likelist=filestr)
        cursor.execute(query)
        resultSet = cursor.fetchall()
        if cursor.rowcount == 0:
            pass
        cursor.close()
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    return resultSet


###########################################################################

def updatevalue(table, column, value, filename, connection='lcogt2', filename0='filename'):
    import sys
    import MySQLdb, os, string
    import lsc

    hostname, username, passwd, database = lsc.mysqldef.getconnection(connection)
    conn = lsc.mysqldef.dbConnect(hostname, username, passwd, database)
    try:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        if value in [True, False]:
            cursor.execute("UPDATE " + str(table) + " set " + column + "=" + str(value) + " where " + str(
                filename0) + "= " + "'" + str(filename) + "'" + "   ")
        elif value in ['Null', 'null', 'NULL', '']:
            cursor.execute(
                "UPDATE " + str(table) + " set " + column + "=NULL where " + str(filename0) + "= " + "'" + str(
                    filename) + "'" + "   ")
        elif type(value) is float:
            cursor.execute("UPDATE %s set %s=%16.16f where %s= '%s'   " % (table, column, value, filename0, filename))
        else:
            cursor.execute("UPDATE " + str(table) + " set " + column + "=" + "'" + str(value) + "'" + " where " + str(
                filename0) + "= " + "'" + str(filename) + "'" + "   ")
        resultSet = cursor.fetchall()
        if cursor.rowcount == 0:
            pass
        conn.commit()
        cursor.close()
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])


###########################################################################

def insert_values(conn, table, values):
    import sys, string, os, re, MySQLdb, os, string, datetime

    datecreated_tables = ['atels', 'groups', 'iaunames', 'instruments', 'notes',
                          'obsrequests', 'photlco', 'photlcoraw', 'photpairing',
                          'spec', 'speclcoraw', 'targetnames', 'targets',
                          'telescopes', 'useractionlog', 'users']
    if 'datecreated' not in values and table in datecreated_tables:
        values['datecreated'] = str(datetime.datetime.utcnow())

    def dictValuePad(key):
        return '%(' + str(key) + ')s'

    def insertFromDict(table, dicto):
        """Take dictionary object dict and produce sql for
        inserting it into the named table"""
        cleandict = {key: val for key, val in dicto.items() if val not in ['NaN', 'UNKNOWN', 'N/A', None, '']}

        sql = 'INSERT INTO ' + table
        sql += ' ('
        sql += ', '.join(cleandict)
        sql += ') VALUES ('
        sql += ', '.join(map(dictValuePad, cleandict))
        sql += ');'
        return sql

    sql = insertFromDict(table, values)
    try:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sql, values)
        resultSet = cursor.fetchall()
        if cursor.rowcount == 0:
            pass
        conn.commit()
        cursor.close()
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])


########################################################################
#  dataraw
# create table dataraw (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, filename VARCHAR(50) UNIQUE KEY, filepath VARCHAR(100), objname VARCHAR(50), jd FLOAT, dateobs DATE, exptime FLOAT, filter VARCHAR(20), grism VARCHAR(20), telescope VARCHAR(20), instrument VARCHAR(20), type VARCHAR(20), category VARCHAR(20) , tech VARCHAR(20) , airmass FLOAT, ut TIME, slit VARCHAR(20), lamp VARCHAR(20), status VARCHAR(50), input VARCHAR(50), note VARCHAR(100), ra0 FLOAT, dec0 FLOAT, OBID INT, temperature FLOAT, observer VARCHAR(30) );

# dataredu
# create table dataredu (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, filename VARCHAR(50) UNIQUE KEY, filepath VARCHAR(100), objname VARCHAR(50), jd FLOAT, dateobs DATE, exptime FLOAT, filter VARCHAR(20), grism VARCHAR(20), telescope VARCHAR(20), instrument VARCHAR(20), type VARCHAR(20), category VARCHAR(20) , tech VARCHAR(20) , airmass FLOAT, ut TIME, slit VARCHAR(20), lamp VARCHAR(20), status VARCHAR(50), input VARCHAR(50), note VARCHAR(100), ra0 FLOAT, dec0 FLOAT, OBID INT, temperature FLOAT, observer VARCHAR(30) );

# reducomputed
# create table redulog (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, filename VARCHAR(50) UNIQUE KEY, filepath VARCHAR(100), bias  VARCHAR(50), flat VARCHAR(50), dark VARCHAR(50), illcorr VARCHAR(50), crosstalk VARCHAR(50), arc VARCHAR(50), skysub VARCHAR(50), mask  VARCHAR(50), fringing VARCHAR(50), astrometry  BOOL, zeropoint  VARCHAR(30), sensitivity VARCHAR(50), telluric  VARCHAR(50) );

# (val BOOL, true INT DEFAULT 1, false INT DEFAULT 0)
###############################
# create table photlcoraw (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, filename VARCHAR(50) UNIQUE KEY, filepath VARCHAR(100), objname VARCHAR(50), jd DOUBLE, dateobs DATE, exptime FLOAT, filter VARCHAR(20), grism VARCHAR(20), telescope VARCHAR(20), instrument VARCHAR(20), type VARCHAR(20), category VARCHAR(20) , tech VARCHAR(20) , airmass FLOAT, ut TIME, slit VARCHAR(20), lamp VARCHAR(20), status VARCHAR(50), input VARCHAR(50), note VARCHAR(100), ra0 FLOAT, dec0 FLOAT,  fwhm FLOAT DEFAULT 9999, OBID INT, temperature FLOAT, propid VARCHAR(30), rotskypa FLOAT, observer VARCHAR(30), USERID VARCHAR(30), dateobs2  VARCHAR(23)) ;


# create table datarawfloyds (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, filename VARCHAR(50) UNIQUE KEY, filepath VARCHAR(100), objname VARCHAR(50), jd DOUBLE, dateobs DATE, exptime FLOAT, filter VARCHAR(20), grism VARCHAR(20), telescope VARCHAR(20), instrument VARCHAR(20), type VARCHAR(20), category VARCHAR(20) , tech VARCHAR(20) , airmass FLOAT, ut TIME, slit VARCHAR(20), lamp VARCHAR(20), status VARCHAR(50), input VARCHAR(50), note VARCHAR(100), ra0 FLOAT, dec0 FLOAT,  fwhm FLOAT DEFAULT 9999, OBID INT, temperature FLOAT, propid VARCHAR(30), rotskypa FLOAT, observer VARCHAR(30), USERID VARCHAR(30), dateobs2  VARCHAR(23)) ;

# create table photlco (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, filename VARCHAR(50) UNIQUE KEY, filepath VARCHAR(100), objname VARCHAR(50), jd DOUBLE, dateobs DATE, exptime FLOAT, filter VARCHAR(20), telescope VARCHAR(20), instrument VARCHAR(20), airmass FLOAT, ut TIME, wcs FLOAT DEFAULT 9999, psf FLOAT DEFAULT 9999, apmag FLOAT, psfx FLOAT, psfy FLOAT, psfmag FLOAT DEFAULT 9999, psfdmag FLOAT, z1 FLOAT DEFAULT 9999, z2 FLOAT DEFAULT 9999, c1 FLOAT DEFAULT 9999, c2 FLOAT DEFAULT 9999, dz1 FLOAT DEFAULT 9999, dz2 FLOAT DEFAULT 9999, dc1 FLOAT DEFAULT 9999, dc2 FLOAT DEFAULT 9999 , zcol1 VARCHAR(2), zcol2 VARCHAR(2) , mag FLOAT DEFAULT 9999, dmag FLOAT, quality BOOL, zcat varchar(50) DEFAULT 'X', abscat varchar(50) DEFAULT 'X');

# create table photpairing (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, namein VARCHAR(100), tablein VARCHAR(20), nameout VARCHAR(100), tableout VARCHAR(20) );

# create table targets (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), ra0 DOUBLE, dec0 DOUBLE, redshift DOUBLE, psf_string VARCHAR(20), sloan_cat, landolt_cat );

# create table groupstab (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, group  VARCHAR(20) , groupid INT);

# create table changelog  (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, user VARCHAR(20), targetid BIGINT, date DATE, note  VARCHAR(200));

# create table obslog  (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, user VARCHAR(20), targetid BIGINT, triggerjd DOUBLE, windowstart DOUBLE, windowend  DOUBLE, filters  VARCHAR(30), exptime VARCHAR(30), numexp VARCHAR(30), proposal VARCHAR(30), site VARCHAR(10), instrument VARCHAR(30), sky FLOAT DEFAULT 9999, seeing FLOAT DEFAULT 9999, airmass FLOAT DEFAULT 9999, slit FLOAT DEFAULT 9999, acqmode VARCHAR(20), priority FLOAT DEFAULT 9999);

# select raw.filename,raw.filepath from photlcoraw raw where raw.telescope = '1m0a' and raw.dateobs = 20121105 and NOT EXISTS(select * from photlco redu where raw.filename = redu.filename);

# delete from dataraw where filename='test';
#######################################

def ingestdata(telescope, instrument, listepoch, _force, _type='oracproc', _object='', lista=''):
    import glob, string, os, re, sys
    import lsc
    from mysqldef import dbConnect
    from mysqldef import insert_values
    from mysqldef import getfromdataraw
    from mysqldef import updatevalue
    import numpy as np
    if _type not in ['oracproc', 'quicklook', 'pylcogt', 'preproc']:
        _type = 'oracproc/'
        roothdir = '/archive/engineering/'
    elif _type == 'pylcogt':
        _type = ''
        roothdir = '/nethome/supernova/pylcogt/'
    else:
        _type = _type + '/'
        roothdir = '/archive/engineering/'

    if telescope in lsc.telescope0['all'] + lsc.site0 + ['all', 'ftn', 'fts', 'tar']:
        hostname, username, passwd, database = lsc.mysqldef.getconnection('lcogt2')
    else:
        sys.exit('problem with database')

    conn = lsc.mysqldef.dbConnect(hostname, username, passwd, database)
    print instrument
    print telescope

    aaa = lsc.mysqldef.query(['select idcode, groupidcode from programs'], conn)
    _proposal = list(set([i['idcode'] for i in aaa] + lsc.util.proposalingestion))
    _objectstring = lsc.util.extraobject
    _objectskip = lsc.util.skipobjects

    a, b, c, d = lsc.sites.cameraavailable()
    b = np.array(b)
    c = np.array(c)
    d = np.array(d)

    if instrument:
        if instrument in b:
            tellist = {d[list(b).index(instrument)]: [instrument]}
        else:
            tellist = {}
            for jj in lsc.site0:
                tellist[jj] = b[d == jj]
    else:
        if telescope:
            tellist = {}
            if telescope == 'all':
                for jj in lsc.site0:
                    tellist[jj] = lsc.instrument0['all']
            elif telescope in ['elp']:
                tellist['elp'] = b[d == 'elp']
            elif telescope in ['cpt']:
                tellist['cpt'] = b[d == 'cpt']
            elif telescope in ['lsc']:
                tellist['lsc'] = b[d == 'lsc']
            elif telescope in ['ogg', 'ftn']:
                tellist['ogg'] = b[d == 'ogg']
            elif telescope in ['coj', 'fts']:
                tellist['coj'] = b[d == 'coj']
            elif telescope in lsc.telescope0['all']:
                for i in range(0, len(b)):
                    if lsc.dome0[(d[i], c[i])] == telescope:
                        tellist[d[i]] = [b[i]]
            elif telescope in ['tar']:
                tellist['tar'] = ['tar']
            else:
                for jj in lsc.site0:
                    tellist[jj] = b[d == jj]
        else:
            for jj in lsc.site0:
                tellist[jj] = lsc.instrument0['all']

                #####################   collect all fits images to ingest    #############################
    for epoch in listepoch:
        print epoch
        if telescope in ['fts', 'ftn']:
            imglist = ''
            print '\n###  warning ingestion raw data FTN and FTS data should be done from web site and not from /archive/data1/'
        elif telescope in lsc.util.site0 + lsc.util.telescope0['all'] + ['all']:
            import lsc
            from lsc.util import readkey3, readhdr
            imglist = []
            for tel in tellist:
                for instrument in tellist[tel]:
                    directory = roothdir + tel + '/' + instrument + '/' + str(epoch) + '/' + _type
                    print directory
                    imglist = imglist + glob.glob(directory + '*[0-9][0-9].fits')
                    print imglist
        elif telescope in ['tar']:
            if lista:
                imglist0 = lista
            else:
                imglist0 = glob.glob('*fits')

            import lsc
            from lsc.util import readkey3, readhdr
            imglist = []
            instrumentlist = []
            tellist = []
            for img in imglist0:
                img = os.getcwd() + '/' + img
                # answ=raw_input('do you want to ingest this files '+str(img)+' [[y]/n]?')
                answ = 'y'
                if not answ: answ = 'y'
                if answ in ['yes', 'y', 'Y', 'YES', 'Yes']:
                    hdr = readhdr(img)
                    if readkey3(hdr, 'instrume') not in instrumentlist:
                        instrumentlist = instrumentlist + [readkey3(hdr, 'instrume')]
                    if readkey3(hdr, 'TELESCOP') not in tellist:
                        tellist = tellist + [readkey3(hdr, 'TELESCOP')]
                    imglist = imglist + [img]
            print tellist
        else:
            imglist = []
        ##################################################################################

        datarawtable = 'photlcoraw'
        for img in imglist:
            print img
            if not lsc.mysqldef.getfromdataraw(conn, datarawtable, 'filename', string.split(img, '/')[-1],
                                               column2='filename') or _force:
                hdr = readhdr(img)
                telescope = hdr.get('telescop')
                instrument = readkey3(hdr, 'instrume')

                if telescope in ['Faulkes Telescope South', 'Faulkes Telescope North']:
                    if 'fs' in instrument:
                        hdr = readhdr(img)
                        if _object:
                            if readkey3(hdr, 'object') == _object:
                                _ingest = True
                            else:
                                _ingest = False
                        else:
                            if readkey3(hdr, 'propid') in _proposal or readkey3(hdr, 'object') in _objectstring:
                                if readkey3(hdr, 'object') in _objectskip:
                                    print 'reject autofocus data'
                                    _ingest = False
                                else:
                                    _ingest = True
                            else:
                                _ingest = False

                        if not _ingest:
                            dictionary = {}
                        else:
                            print '2mold'
                            if telescope in ['Faulkes Telescope South']:
                                telescope = '2m0-02'
                            elif telescope in ['Faulkes Telescope North']:
                                telescope = '2m0-01'
                            _tech = None
                            _tracknum = readkey3(hdr, 'TRACKNUM')
                            if not _tracknum.isdigit():
                                _tracknum = 0
                            dictionary = {'telescope': telescope, 'instrument': readkey3(hdr, 'instrume'), \
                                          'dec0': readkey3(hdr, 'DEC'), 'ra0': readkey3(hdr, 'RA'), \
                                          'ut': readkey3(hdr, 'ut'), 'dateobs': readkey3(hdr, 'date-obs'), \
                                          'exptime': readkey3(hdr, 'exptime'), 'filter': readkey3(hdr, 'filter'), \
                                          'mjd': readkey3(hdr, 'mjd'), 'airmass': readkey3(hdr, 'airmass'), \
                                          'objname': readkey3(hdr, 'object'), 'tracknumber': int(_tracknum), \
                                          'propid': readkey3(hdr, 'propid'), 'dayobs': readkey3(hdr, 'DAY-OBS'), \
                                          'obid': readkey3(hdr, 'BLKUID'), 'userid': readkey3(hdr, 'userid'), \
                                          'temperature': readkey3(hdr, 'CCDATEMP')}
                            dictionary['filename'] = string.split(img, '/')[-1]
                            dictionary['filepath'] = re.sub(dictionary['filename'], '', img)
                            _targetid = lsc.mysqldef.targimg(img)
                            dictionary['targetid'] = _targetid
                            if 'CAT-RA' in hdr:
                                dictionary['cat_ra'] = readkey3(hdr, 'CAT-RA')
                            if 'CAT-DEC' in hdr:
                                dictionary['cat_dec'] = readkey3(hdr, 'CAT-DEC')
                            if _tracknum:
                                gruppo = lsc.mysqldef.query(['select r.groupidcode from obslog as o join ' + \
                                                             'obsrequests as r where o.`requestsid`=r.id and o.tracknumber=' + \
                                                             str(int(_tracknum))], conn)
                            if len(gruppo):
                                dictionary['groupidcode'] = gruppo[0]['groupidcode']
                    else:
                        dictionary = {}
                elif telescope in lsc.util.site0 + lsc.util.telescope0['all'] + ['all', 'tar']:
                    if 'kb' in instrument or 'fl' in instrument:
                        print '1m'
                        hdr = readhdr(img)
                        if _object:
                            if readkey3(hdr, 'object') == _object:
                                _ingest = True
                            else:
                                _ingest = False
                        else:
                            if readkey3(hdr, 'propid') in _proposal or readkey3(hdr, 'object') in _objectstring:
                                if readkey3(hdr, 'object') in _objectskip:
                                    print 'reject autofocus data'
                                    _ingest = False
                                else:
                                    _ingest = True
                            else:
                                _ingest = False

                        if not _ingest:
                            dictionary = {}
                        else:
                            _tech = None
                            _tracknum = readkey3(hdr, 'TRACKNUM')
                            if not _tracknum.isdigit():
                                _tracknum = 0
                            print readkey3(hdr, 'propid'), readkey3(hdr, 'userid'), readkey3(hdr, 'object'), _tracknum
                            dictionary = {'telescope': hdr.get('telescop'), 'fwhm': readkey3(hdr, 'L1FWHM'), \
                                          'instrument': readkey3(hdr, 'instrume'), 'dec0': readkey3(hdr, 'DEC'), \
                                          'ra0': readkey3(hdr, 'RA'), 'ut': readkey3(hdr, 'ut'), \
                                          'dateobs': readkey3(hdr, 'date-obs'), 'dayobs': readkey3(hdr, 'DAY-OBS'), \
                                          'exptime': readkey3(hdr, 'exptime'), 'filter': readkey3(hdr, 'filter'), \
                                          'mjd': readkey3(hdr, 'mjd'), 'airmass': readkey3(hdr, 'airmass'), \
                                          'objname': readkey3(hdr, 'object'), 'tracknumber': int(_tracknum), \
                                          'propid': readkey3(hdr, 'propid'), 'obid': readkey3(hdr, 'BLKUID'), \
                                          'userid': readkey3(hdr, 'userid'), 'temperature': readkey3(hdr, 'CCDATEMP')}
                            dictionary['filename'] = string.split(img, '/')[-1]
                            dictionary['filepath'] = re.sub(dictionary['filename'], '', img)
                            _targetid = lsc.mysqldef.targimg(img)
                            dictionary['targetid'] = _targetid
                            if 'CAT-RA' in hdr:
                                dictionary['cat_ra'] = readkey3(hdr, 'CAT-RA')
                            if 'CAT-DEC' in hdr:
                                dictionary['cat_dec'] = readkey3(hdr, 'CAT-DEC')
                            if _tracknum:
                                gruppo = lsc.mysqldef.query(['select r.groupidcode from obslog as o join obsrequests ' + \
                                                             'as r where o.`requestsid`=r.id and o.tracknumber=' + str(
                                    int(_tracknum))], conn)
                                if len(gruppo):
                                    dictionary['groupidcode'] = gruppo[0]['groupidcode']
                                else:
                                    if readkey3(hdr, 'propid') == 'CON2014B-005':
                                        dictionary['groupidcode'] = 5
                    elif 'fs' in instrument:
                        print '2m'
                        #####  added new ingestion 2m
                        hdr = readhdr(img)
                        if _object:
                            if readkey3(hdr, 'object') == _object:
                                _ingest = True
                            else:
                                _ingest = False
                        else:
                            if readkey3(hdr, 'propid') in _proposal or readkey3(hdr, 'object') in _objectstring:
                                if readkey3(hdr, 'object') in _objectskip:
                                    print 'reject autofocus data'
                                    _ingest = False
                                else:
                                    _ingest = True
                            else:
                                _ingest = False
                        if not _ingest:
                            dictionary = {}
                        else:
                            _tech = None
                            _tracknum = readkey3(hdr, 'TRACKNUM')
                            if not _tracknum.isdigit():
                                _tracknum = 0
                            print readkey3(hdr, 'propid'), readkey3(hdr, 'userid'), readkey3(hdr, 'object'), _tracknum
                            dictionary = {'telescope': hdr.get('telescop'), 'fwhm': readkey3(hdr, 'L1FWHM'), \
                                          'instrument': readkey3(hdr, 'instrume'), 'dec0': readkey3(hdr, 'DEC'), \
                                          'ra0': readkey3(hdr, 'RA'), 'ut': readkey3(hdr, 'ut'), \
                                          'dateobs': readkey3(hdr, 'date-obs'), 'dayobs': readkey3(hdr, 'DAY-OBS'), \
                                          'exptime': readkey3(hdr, 'exptime'), 'filter': readkey3(hdr, 'filter'), \
                                          'mjd': readkey3(hdr, 'mjd'), 'airmass': readkey3(hdr, 'airmass'), \
                                          'objname': readkey3(hdr, 'object'), 'tracknumber': int(_tracknum), \
                                          'propid': readkey3(hdr, 'propid'), 'obid': readkey3(hdr, 'BLKUID'), \
                                          'userid': readkey3(hdr, 'userid'), 'temperature': readkey3(hdr, 'CCDATEMP')}
                            dictionary['filename'] = string.split(img, '/')[-1]
                            dictionary['filepath'] = re.sub(dictionary['filename'], '', img)
                            _targetid = lsc.mysqldef.targimg(img)
                            dictionary['targetid'] = _targetid
                            if 'CAT-RA' in hdr:
                                dictionary['cat_ra'] = readkey3(hdr, 'CAT-RA')
                            if 'CAT-DEC' in hdr:
                                dictionary['cat_dec'] = readkey3(hdr, 'CAT-DEC')
                            if _tracknum:
                                gruppo = lsc.mysqldef.query(
                                    ['select r.groupidcode from obslog as o join obsrequests as ' + \
                                     'r where o.`requestsid`=r.id and o.tracknumber=' + str(int(_tracknum))], conn)
                                if len(gruppo):
                                    dictionary['groupidcode'] = gruppo[0]['groupidcode']
                    else:
                        dictionary = {}
                else:
                    ##########################################
                    print 'try forcing it'
                    print img
                    hdr = readhdr(img)
                    if 'ra' in hdr:
                        _ra = hdr.get('ra')
                    else:
                        _ra = None
                        print 'ra not defined, please add ra keyword'
                    if 'dec' in hdr:
                        _dec = hdr.get('dec')
                    else:
                        _dec = None
                        print 'dec not defined, please add dec keyword'
                    if 'MJD-OBS' in hdr:
                        _mjd = hdr.get('MJD-OBS')
                    else:
                        _mjd = None
                        print 'MJD not defined, please add MJD-OBS keyword '
                    if 'filter' in hdr:
                        _filter = hdr.get('filter')
                    else:
                        _filter = None
                        print 'filter not defined, please add filter keyword'
                    if 'date-obs' in hdr:
                        _dateobs = hdr.get('date-obs')
                    else:
                        _dataobs = None
                    _dayobs = hdr.get('DAYOBS')
                    _telescope = hdr.get('TELESCOP')
                    _instrume = hdr.get('instrume')
                    _fwhm = hdr.get('L1FWHM')
                    filepath = re.sub(string.split(img, '/')[-1], '', img)

                    if _ra and _dec and _mjd and _filter and _dateobs:
                        _targetid = lsc.mysqldef.targimg(img)
                        dictionary = {'telescope': _telescope, \
                                      'fwhm': _fwhm, \
                                      'instrument': _instrume, \
                                      'dec0': _dec, \
                                      'ra0': _ra, \
                                      'filter': _filter, \
                                      'exptime': readkey3(hdr, 'exptime'), \
                                      'mjd': _mjd, \
                                      'airmass': readkey3(hdr, 'airmass'), \
                                      'dateobs': _dateobs, \
                                      'dayobs': _dayobs, \
                                      'objname': readkey3(hdr, 'object'), \
                                      'tracknumber': 0, \
                                      'targetid': _targetid, \
                                      'filename': string.split(img, '/')[-1], \
                                      'filepath': filepath, \
                                      'propid': 'externaldata', \
                                      'userid': 'externaldata'}
                        if 'CAT-RA' in hdr:
                            dictionary['cat_ra'] = readkey3(hdr, 'CAT-RA')
                        if 'CAT-DEC' in hdr:
                            dictionary['cat_dec'] = readkey3(hdr, 'CAT-DEC')
                    else:
                        dictionary = {}
                print dictionary
                ###################################################
                if dictionary:
                    if hdr.get('TELESCOP'):
                        _tel = hdr.get('TELESCOP')
                    else:
                        _tel = ''
                    if _tel in ['Faulkes Telescope South', 'fts']:
                        _tel = '2m0-02'
                    elif _tel in ['Faulkes Telescope North', 'ftn']:
                        _tel = '2m0-01'
                    _telid = lsc.mysqldef.getfromdataraw(conn, 'telescopes', 'name', _tel, column2='id')
                    if not _telid:
                        print 'Telescope ', _tel, ' not recognized.  Adding to telescopes table.'
                        lsc.mysqldef.insert_values(conn, 'telescopes', {'name': _tel})
                        _telid = lsc.mysqldef.getfromdataraw(conn, 'telescopes', 'name', _tel, column2='id')
                    telid = _telid[0]['id']
                    dictionary['telescopeid'] = str(telid)

                    _instid = lsc.mysqldef.getfromdataraw(conn, 'instruments', 'name', instrument, column2='id')
                    if not _instid:
                        print 'Instrument ', instrument, ' not recognized.  Adding to instruments table.'
                        lsc.mysqldef.insert_values(conn, 'instruments', {'name': instrument})
                        _instid = lsc.mysqldef.getfromdataraw(conn, 'instruments', 'name', instrument, column2='id')
                    instid = _instid[0]['id']
                    dictionary['instrumentid'] = str(instid)

                    ###################################
                if telescope in ['fts', 'ftn']:
                    if 'fs' in instrument:
                        if not lsc.mysqldef.getfromdataraw(conn, datarawtable, 'filename', string.split(img, '/')[-1],
                                                           column2='filename'):
                            lsc.mysqldef.insert_values(conn, datarawtable, dictionary)
                        elif _force:
                            for voce in dictionary:
                                if voce != 'id' and voce != 'filename':
                                    lsc.mysqldef.updatevalue(datarawtable, voce, dictionary[voce],
                                                             string.split(img, '/')[-1])
                elif telescope in lsc.util.site0 + lsc.util.telescope0['all'] + ['all', 'tar']:
                    if dictionary:
                        if 'kb' in instrument or 'fl' in instrument or 'fs' in instrument:
                            if not lsc.mysqldef.getfromdataraw(conn, datarawtable, 'filename',
                                                               string.split(img, '/')[-1], column2='filename'):
                                lsc.mysqldef.insert_values(conn, datarawtable, dictionary)
                                print 'insert ' + img
                            elif _force:
                                print 'reinsert ' + img
                                for voce in dictionary:
                                    if voce != 'id' and voce != 'filename':
                                        lsc.mysqldef.updatevalue(datarawtable, voce, dictionary[voce],
                                                                 string.split(img, '/')[-1])
                else:
                    if dictionary:
                        if not lsc.mysqldef.getfromdataraw(conn, datarawtable, 'filename', string.split(img, '/')[-1],
                                                           column2='filename'):
                            lsc.mysqldef.insert_values(conn, datarawtable, dictionary)
                            print 'insert ' + img
                        elif _force:
                            print 'reinsert ' + img
                            for voce in dictionary:
                                if voce != 'id' and voce != 'filename':
                                    lsc.mysqldef.updatevalue(datarawtable, voce, dictionary[voce],
                                                             string.split(img, '/')[-1])
            else:
                print img + ' already ingested'


###############################################################################################################################################

def ingestredu(imglist,force='no',dataredutable='photlco',filetype=1):
   import string,re,os,sys
   import lsc
   from lsc.util import readkey3, readhdr

   hostname, username, passwd, database=lsc.mysqldef.getconnection('lcogt2')
   conn = lsc.mysqldef.dbConnect(hostname, username, passwd, database)

   for fullpath in imglist:
      path, img = os.path.split(fullpath)
      path += '/'

      exist=lsc.mysqldef.getfromdataraw(conn,dataredutable,'filename', string.split(img,'/')[-1],column2='filename')
      exist2=lsc.mysqldef.getfromdataraw(conn,'photlcoraw','filename', string.split(img,'/')[-1],column2='filename, groupidcode')
      if exist2:
         print exist2
         _groupidcode=exist2[0]['groupidcode']
      else:
         _groupidcode=''

      if exist:
         if force=='yes':
            print img,database
            lsc.mysqldef.deleteredufromarchive(string.split(img,'/')[-1],dataredutable)
            print 'delete line from '+str(database)
            exist=lsc.mysqldef.getfromdataraw(conn,dataredutable,'filename', string.split(img,'/')[-1],column2='filename')

      if not exist or force =='update':
         hdr=readhdr(fullpath)
         _targetid=lsc.mysqldef.targimg(fullpath)
         try:
            _tracknumber=int(readkey3(hdr,'TRACKNUM'))
         except:
            _tracknumber=0
         if hdr.get('TELESCOP'):  
            _tel=hdr.get('TELESCOP')
         else: 
            _tel=''
         if _tel in ['Faulkes Telescope South','fts']:  
            _tel='2m0-02'
         elif _tel in ['Faulkes Telescope North','ftn']: 
            _tel='2m0-01'
         _inst=hdr.get('instrume')
         dictionary={'dateobs':readkey3(hdr,'date-obs'),'dayobs':readkey3(hdr,'DAY-OBS'),'filename':img,'filepath':path,'filetype':filetype,'targetid':_targetid,\
                     'exptime':readkey3(hdr,'exptime'), 'filter':readkey3(hdr,'filter'),'mjd':readkey3(hdr,'mjd'),'tracknumber':_tracknumber,'groupidcode':_groupidcode,\
                     'telescope':_tel,'airmass':readkey3(hdr,'airmass'),'objname':readkey3(hdr,'object'),'ut':readkey3(hdr,'ut'),\
                     'wcs':readkey3(hdr,'wcserr'),'instrument':_inst,'ra0':readkey3(hdr,'RA'),'dec0':readkey3(hdr,'DEC')}

         _telid=lsc.mysqldef.getfromdataraw(conn,'telescopes','name',_tel,column2='id')
         if not _telid:
           print 'Telescope ',_tel,' not recognized.  Adding to telescopes table.'
           lsc.mysqldef.insert_values(conn,'telescopes',{'name':_tel})
           _telid=lsc.mysqldef.getfromdataraw(conn,'telescopes','name',_tel,column2='id')
         telid=_telid[0]['id']
         dictionary['telescopeid']=str(telid)

         _instid=lsc.mysqldef.getfromdataraw(conn,'instruments','name',_inst,column2='id')
         if not _instid:
           print 'Instrument ',_inst,' not recognized.  Adding to instruments table.'
           lsc.mysqldef.insert_values(conn,'instruments',{'name':_inst})
           _instid=lsc.mysqldef.getfromdataraw(conn,'instruments','name',_inst,column2='id')
         instid=_instid[0]['id']
         dictionary['instrumentid']=str(instid)

         print dictionary
         print 'insert reduced'
         ggg=lsc.mysqldef.getfromdataraw(conn, dataredutable, 'filename',str(img), '*')
         if not ggg:
            lsc.mysqldef.insert_values(conn,dataredutable,dictionary)
         else:
            for voce in dictionary:
               lsc.mysqldef.updatevalue(dataredutable,voce,dictionary[voce],string.split(img,'/')[-1])
      else:
         print 'already ingested'


###############################################################################################################################

def getvaluefromarchive(table, column, value, column2):
    import sys
    import MySQLdb, os, string
    import lsc
    hostname, username, passwd, database = lsc.mysqldef.getconnection('lcogt2')
    conn = lsc.mysqldef.dbConnect(hostname, username, passwd, database)
    resultSet = lsc.mysqldef.getfromdataraw(conn, table, column, value, column2)
    if resultSet:
        result = resultSet
    else:
        result = []
    return result


def deleteredufromarchive(filename, archive='photlco', column='filename'):
    import sys
    import MySQLdb, os, string
    import lsc
    hostname, username, passwd, database = lsc.mysqldef.getconnection('lcogt2')
    conn = lsc.mysqldef.dbConnect(hostname, username, passwd, database)
    #######
    try:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("delete  from " + str(archive) + " where " + str(column) + "=" + "'" + filename + "'")
        resultSet = cursor.fetchall()
        if cursor.rowcount == 0:
            pass
        cursor.close()
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    return resultSet


###################################################################################################################
def updateDatabase(tarfile):
    import string, os, re, math, sys, shutil, glob, socket, pickle
    import MySQLdb
    host = socket.gethostname()
    import ntt
    from ntt.util import readkey3, readhdr
    from mysqldef import updatevalue, getvaluefromarchive, dbConnect, getfromdataraw, ingestredu
    os.system('tar -zxvf ' + str(tarfile))
    pklfile = re.sub('tar.gz', 'pkl', tarfile)
    if glob.glob(pklfile):
        pkl_file = open(pklfile, 'rb')
        mydict2 = pickle.load(pkl_file)
        pkl_file.close()
        fitsfile = []
        for i in mydict2:
            try:
                command = mydict2[i]['command']
                if command == 'ingestredu':
                    lista = mydict2[i]['lista']
                    instrument = mydict2[i]['instument']
                    output = mydict2[i]['output']
                    ingestredu(lista)
                    if output not in fitsfile: fitsfile.append(output)
                elif command == 'getvaluefromarchive':
                    table = mydict2[i]['table']
                    column = mydict2[i]['column']
                    value = mydict2[i]['value']
                    _input = mydict2[i]['input']
                    hh = getvaluefromarchive(table, column, _input, value)
                elif command == 'updatevalue':
                    table = mydict2[i]['table']
                    column = mydict2[i]['column']
                    value = mydict2[i]['value']
                    _input = mydict2[i]['input']
                    if value != 'voce':
                        updatevalue(table, column, value, _input)
                    else:
                        if column == 'voce':
                            for voce in hh:
                                if voce != 'id' and voce != 'filename':
                                    updatevalue(table, voce, hh[voce], _input)
                        else:
                            updatevalue(table, column, hh[column], _input)
                else:
                    print 'warning: command  not recognise'
            except:
                print '#####################'
                print mydict2[i]
                print 'problems'
        print fitsfile
        dir1 = '/data/obsdata/y20' + string.split(tarfile, '_')[2][-2:] + '/'
        dir2 = '/data/obsdata/y20' + string.split(tarfile, '_')[2][-2:] + '/' + string.split(tarfile, '_')[2] + '/'
        if not os.path.isdir(dir1):  os.mkdir(dir1)
        if not os.path.isdir(dir2):  os.mkdir(dir2)
        for img in fitsfile:
            arcfile = readkey3(readhdr(img), 'ARCFILE')
            print arcfile
            try:
                bbbb = getvaluefromarchive('datarawNTT', 'filename', arcfile, '*')
            except:
                bbbb = ''
            if bbbb:
                directoryraw = bbbb['filepath']
                directoryreduced = re.sub('raw/', '', directoryraw) + 'reduced/'
            else:
                dir3 = dir2 + string.split(tarfile, '_')[3] + '_' + string.split(tarfile, '_')[4] + '/'
                if not os.path.isdir(dir3):  os.mkdir(dir3)
                directoryreduced = dir3 + 'reduced/'

            if not os.path.isdir(directoryreduced):        os.mkdir(directoryreduced)
            os.system('cp ' + img + ' ' + directoryreduced)
            updatevalue('redulogNTT', 'filepath', directoryreduced, img)
            updatevalue('datareduNTT', 'filepath', directoryreduced, img)


##############################################################################

def getfromcoordinate(conn, table, ra0, dec0, distance):
    import sys
    import MySQLdb, os, string
    #  this is acually not needed
    if table == 'targets':
        ra1 = 'ra0'
        dec1 = 'dec0'
    elif table == 'photlcoraw':
        ra1 = 'ra0'
        dec1 = 'dec0'
    ####
    try:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        command = ["set @sc = pi()/180", "set @ra = " + str(ra0), "set @dec = " + str(dec0),
                   "set @distance = " + str(distance),
                   "SELECT *,abs(2*asin( sqrt( sin((a.dec0-@dec)*@sc/2)*sin((a.dec0-@dec)*@sc/2) + cos(a.dec0*@sc)*cos(@dec*@sc)*sin((a.ra0-@ra)*@sc/2)*sin((a.ra0-@ra)*@sc/2.0) )))*180/pi() as hsine FROM " + str(
                       table) + " as a HAVING hsine<@distance order by a.ra0 desc"]
        for ccc in command:
            cursor.execute(ccc)
        resultSet = cursor.fetchall()
        if cursor.rowcount == 0:
            pass
        cursor.close()
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    return resultSet


###################################################################################

def targimg(img='', hdrt=None):
    import lsc
    from lsc.util import readkey3, readhdr
    from lsc.mysqldef import getfromcoordinate
    from lsc import conn
    import string
    proposalgroup = lsc.util.proposalgroup
    _targetid = ''
    _group = ''
    if hdrt is None:
        hdrt = lsc.util.readhdr(img)
    if ('CAT-RA' in hdrt and 'CAT-DEC' in hdrt and
                hdrt['CAT-RA'] not in ['NaN', 'UNKNOWN', None, ''] and hdrt['CAT-DEC'] not in ['NaN', 'UNKNOWN', None,
                                                                                               '']):
        _ra = lsc.util.readkey3(hdrt, 'CAT-RA')
        _dec = lsc.util.readkey3(hdrt, 'CAT-DEC')
    elif ('RA' in hdrt and 'DEC' in hdrt and
                  hdrt['RA'] not in ['NaN', 'UNKNOWN', None, ''] and hdrt['DEC'] not in ['NaN', 'UNKNOWN', None, '']):
        _ra = lsc.util.readkey3(hdrt, 'RA')
        _dec = lsc.util.readkey3(hdrt, 'DEC')
    else:
        _ra = None
        _dec = None
    _object = lsc.util.readkey3(hdrt, 'object')
    if ':' in str(_ra):
        _ra, _dec = lsc.deg2HMS(_ra, _dec)

    #############  define groupid ################
    aaa = lsc.mysqldef.query(['select idcode, groupidcode from programs'], conn)
    grname = [i['idcode'] for i in aaa]
    gr = [i['groupidcode'] for i in aaa]
    if lsc.util.readkey3(hdrt, 'propid') in grname:
        if gr[grname.index(lsc.util.readkey3(hdrt, 'propid'))] not in [1, None]:
            _group = gr[grname.index(lsc.util.readkey3(hdrt, 'propid'))]
        else:
            _group = 32769
    else:
        _group = 32769
    ##############################################

    ########  define targetid  ##################
    _targetid = lsc.mysqldef.gettargetid(_object, '', '', conn, .01, False)
    if not _targetid:
        print '# no target with this name ' + _object
        _targetid = lsc.mysqldef.gettargetid('', _ra, _dec, conn, .01, False)
        if _targetid:
            print '# target at this coordinate with a different name, add name ' + str(_ra) + ' ' + str(_dec)
            dictionary1 = {'name': _object, 'targetid': _targetid, 'groupidcode': _group}
            lsc.mysqldef.insert_values(conn, 'targetnames', dictionary1)

            bb2 = lsc.mysqldef.query(['select id from targetnames where name = "' + _object + '"'], conn)
            dictionary3 = {'userid': 67, 'tablemodified': 'targetnames', 'idmodified': bb2[0]['id'],
                           'columnmodified': 'New Row', 'newvalue': 'Multiple'}
            lsc.mysqldef.insert_values(conn, 'useractionlog', dictionary3)
        else:
            print 'not found targetid with ra and dec ' + str(_ra) + ' ' + str(_dec)
    else:
        print 'found name= ' + _object + '  targetid= ' + str(_targetid)
    ##############################################

    if not _targetid:
        # no target
        print 'add new target ' + str(_ra) + ' ' + str(_dec) + ' ' + _object
        dictionary = {'ra0': _ra, 'dec0': _dec}
        lsc.mysqldef.insert_values(conn, 'targets', dictionary)
        bb = lsc.mysqldef.getfromcoordinate(conn, 'targets', _ra, _dec, .000156)

        dictionary2 = {'userid': 67, 'tablemodified': 'targets', 'idmodified': bb[0]['id'],
                       'columnmodified': 'New Row', 'newvalue': 'Multiple'}
        lsc.mysqldef.insert_values(conn, 'useractionlog', dictionary2)

        dictionary1 = {'name': _object, 'targetid': bb[0]['id'], 'groupidcode': _group}
        lsc.mysqldef.insert_values(conn, 'targetnames', dictionary1)

        bb2 = lsc.mysqldef.query(['select id from targetnames where name = "' + _object + '"'], conn)
        dictionary3 = {'userid': 67, 'tablemodified': 'targetnames', 'idmodified': bb2[0]['id'],
                       'columnmodified': 'New Row', 'newvalue': 'Multiple'}
        lsc.mysqldef.insert_values(conn, 'useractionlog', dictionary3)

        _targetid = bb[0]['id']
        print '\n add a target ' + str(_ra) + ' ' + str(_dec) + ' ' + str(bb[0]['id'])

    if _targetid and _group:
        cc = lsc.mysqldef.getfromdataraw(conn, 'permissionlog', 'targetid', str(_targetid), column2='groupname')
        if len(cc) == 0:
            _JDn = lsc.mysqldef.JDnow()
            print img
            dictionary2 = {'targetid': _targetid, 'jd': _JDn, 'groupname': _group}
            lsc.mysqldef.insert_values(conn, 'permissionlog', dictionary2)
    return _targetid


#################################################################################
def getsky(data):
    """
    Determine the sky parameters for a FITS data extension.

    data -- array holding the image data
    """
    from numpy import random

    # maximum number of interations for mean,std loop
    maxiter = 30

    # maximum number of data points to sample
    maxsample = 10000

    # size of the array
    ny, nx = data.shape

    # how many sampels should we take?
    if data.size > maxsample:
        nsample = maxsample
    else:
        nsample = data.size

    # create sample indicies
    xs = random.uniform(low=0, high=nx, size=nsample).astype('L')
    ys = random.uniform(low=0, high=ny, size=nsample).astype('L')

    # sample the data
    sample = data[ys, xs].copy()
    sample = sample.reshape(nsample)

    # determine the clipped mean and standard deviation
    mean = sample.mean()
    std = sample.std()
    oldsize = 0
    niter = 0
    while oldsize != sample.size and niter < maxiter:
        niter += 1
        oldsize = sample.size
        wok = (sample < mean + 3 * std)
        sample = sample[wok]
        wok = (sample > mean - 3 * std)
        sample = sample[wok]
        mean = sample.mean()
        std = sample.std()

    return mean, std


################################################################################

def getlike(conn, table, column, value, column2='*'):
    import sys
    import MySQLdb, os, string
    try:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "select " + column2 + " from " + str(table) + " where " + column + " like " + "'%" + value + "%'")
        resultSet = cursor.fetchall()
        if cursor.rowcount == 0:
            pass
        cursor.close()
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    return resultSet


##################################################################
def sqlquery(conn, query):
    import MySQLdb, os
    try:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(query)
        resultSet = cursor.fetchall()
        if cursor.rowcount == 0:
            pass
        cursor.close()
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
    return resultSet


def query(command, conn):
    import MySQLdb, os, string
    lista = ''
    # from lsc import conn
    try:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        for i in command:
            cursor.execute(i)
            lista = cursor.fetchall()
            if cursor.rowcount == 0:
                pass
        cursor.close()
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
    return lista


###############################
def JDnow(datenow='', verbose=False):
    import datetime
    import time
    _JD0 = 2455927.5
    if not datenow:
        datenow = datetime.datetime(time.gmtime().tm_year, time.gmtime().tm_mon, time.gmtime().tm_mday,
                                    time.gmtime().tm_hour, time.gmtime().tm_min, time.gmtime().tm_sec)
    _JDtoday = _JD0 + (datenow - datetime.datetime(2012, 01, 01, 00, 00, 00)).seconds / (3600. * 24) + \
               (datenow - datetime.datetime(2012, 01, 01, 00, 00, 00)).days
    if verbose: print 'JD= ' + str(_JDtoday)
    return _JDtoday


###################################

###############################
def MJDnow(datenow='', verbose=False):
    import datetime
    import time
    _JD0 = 55927.
    if not datenow:
        datenow = datetime.datetime(time.gmtime().tm_year, time.gmtime().tm_mon, time.gmtime().tm_mday,
                                    time.gmtime().tm_hour, time.gmtime().tm_min, time.gmtime().tm_sec)
    _JDtoday = _JD0 + (datenow - datetime.datetime(2012, 01, 01, 00, 00, 00)).seconds / (3600. * 24) + \
               (datenow - datetime.datetime(2012, 01, 01, 00, 00, 00)).days
    if verbose: print 'JD= ' + str(_JDtoday)
    return _JDtoday


###################################

def gettargetid(_name, _ra, _dec, conn, _radius=.01, verbose=False):
    import lsc
    from numpy import argmin
    if _name:
        _name = _name.lower().replace('at20', 'at20%').replace('sn20', 'sn20%').replace(' ', '%')
        command = [
            'select distinct(r.name), r.targetid, t.id, t.ra0, t.dec0 from targetnames as r join targets as t where r.name like "' + \
            _name + '" and t.id=r.targetid']
        lista = lsc.mysqldef.query(command, conn)
    elif _ra and _dec:
        if ':' in str(_ra):
            _ra, _dec = lsc.deg2HMS(_ra, _dec)
        lista = lsc.mysqldef.getfromcoordinate(conn, 'targets', _ra, _dec, _radius)
        if verbose:
            print _ra, _dec, _radius
            print lista
    if lista:
        ll0 = {}
        for jj in lista[0].keys(): ll0[jj] = []
        for i in range(0, len(lista)):
            for jj in lista[0].keys(): ll0[jj].append(lista[i][jj])
            ###########################################
        if len(set(ll0['id'])) == 1:
            _targetid = ll0['id'][0]
        elif len(set(ll0['id'])) > 1:
            if 'hsine' in ll0.keys():
                _targetid = ll0['id'][argmin(ll0['hsine'])]
            else:
                _targetid = ''
        else:
            _targetid = ''
    else:
        _targetid = ''
        if verbose:
            print 'no objects'
    return _targetid


###############################################################
def get_snex_uid(interactive=True, return_fullname=False):
    from getpass import getuser
    from lsc import conn

    snex_uids = {'griffin': 52, 'svalenti': 23, 'iarcavi': 43, 'cmccully': 78, 'dhiramatsu': 192}
    unix_user = getuser()

    if unix_user in snex_uids:
        snex_uid = snex_uids[unix_user]
        if return_fullname:
            usersdict = query(['select id, firstname, lastname from users where id=' + str(snex_uid)], conn)
            fullname = usersdict[0]['firstname'] + ' ' + usersdict[0]['lastname']
    else:
        print 'Your username is not associated with a SNEx account.'
        snex_uid = None
        fullname = None
        if interactive:
            snex_user = raw_input('If you have a SNEx username, input it here. Otherwise, press enter. ')
            if snex_user:
                usersdict = query(['select id, firstname, lastname from users where name="' + snex_user + '"'], conn)
                if usersdict:
                    snex_uid = usersdict[0]['id']
                    fullname = usersdict[0]['firstname'] + ' ' + usersdict[0]['lastname']
                else:
                    print 'SNEx username not found.'
    if return_fullname:
        return snex_uid, fullname
    else:
        return snex_uid

# def update_useractionlog(filename, snex_uid=None, mode='add'):
#    from lsc import conn
#    from sys import exit
#    row_id = query(["select id from spec where filename='"+filename+"'"], conn)
#    if row_id: rowid = [0]['id']
#    else: exit('No entry found for filename '+filename+'. User action not logged.')
#    if mode=='add':   vals = {'columnmodified':'New Row', 'prevvalue':'None', 'newvalue':'Multiple'}
#    elif mode=='del': vals = {'columnmodified':'All', 'prevvalue':'Multiple', 'newvalue':'None'}
#    elif mode=='upd': vals = {'columnmodified':'Multiple', 'prevvalue':'Multiple', 'newvalue':'Multiple'}
#    else: exit('Mode not recognized. User action not logged.')
#    if snex_uid is None: snex_uid = get_snex_uid()
#    if snex_uid is None: exit('SNEx User not found. User action not logged.')
#    vals['userid'] = snex_uid
#    vals['tablemodified'] = 'spec'
#    vals['idmodified'] = row_id
#    insert_values(conn, 'useractionlog', vals)
#    print 'useractionlog updated:', vals


