import os
import string
import re
import sys
import glob
import string
import lsc
import numpy as np
import math
from astropy.io import fits

def weighted_avg_and_std(values, weights):
    """
    Return the weighted average and standard deviation.

    values, weights -- Numpy ndarrays with the same shape.
    """
    average = np.average(values, weights=weights)
    variance = np.average((values-average)**2, weights=weights)  # Fast and numerically precise
    return (average, math.sqrt(variance))

try:
    import mysqldef
    hostname, username, passwd, database = mysqldef.getconnection('lcogt2')
    conn = mysqldef.dbConnect(hostname, username, passwd, database)
except ImportError as e:
    print e
    print 'try running one of these:'
    print 'pip install mysql-python'
    print 'conda install mysql-python'
except:
    print '### warning: problem connecting to the database'

def run_getmag(imglist, _output='', _interactive=False, _show=False, _bin=1e-10, magtype='mag', database='photlco'):
    import lsc
    import datetime
    import mysqldef
    from numpy import array, compress, abs, mean, asarray, std, take, argsort, sort, sqrt
    import os, string, glob, re, sys

    if len(imglist)==0:
        print 'error: no images selected'
        return

    direc = lsc.__path__[0]
    if magtype == 'mag':
        mtype = 'mag'
        mtypeerr = 'dmag'
    elif magtype == 'fit':
        mtype = 'psfmag'
        mtypeerr = 'psfdmag'
    elif magtype == 'ph':
        mtype = 'apmag'
        mtypeerr = 'psfdmag'

    setup = {}
    mag, dmag, mjd, filt, tel, date, filename = [], [], [], [], [], [], []
    z1, z2 = [], []
    magtype = []
    for img in imglist:
        ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
        if ggg[0][mtype]:
            if abs(ggg[0][mtype]) <= 99:
                mag.append(ggg[0][mtype])
                dmag.append(ggg[0][mtypeerr])
                mjd.append(ggg[0]['mjd'])
                filename.append(img)
                filt.append(ggg[0]['filter'])
                tel.append(ggg[0]['telescope'])
                date.append(ggg[0]['dateobs'])
                z1.append(ggg[0]['z1'])
                z2.append(ggg[0]['z2'])
                magtype.append(ggg[0]['magtype'])
                if tel[-1] not in setup:  setup[tel[-1]] = {}
                if filt[-1] not in setup[tel[-1]]:  setup[tel[-1]][filt[-1]] = {}

    for _tel in setup:
        for _fil in setup[_tel]:
            mjd0 = compress((array(filt) == _fil) & (array(tel) == _tel), array(mjd))
            mag0 = compress((array(filt) == _fil) & (array(tel) == _tel), array(mag))
            dmag0 = compress((array(filt) == _fil) & (array(tel) == _tel), array(dmag))
            date0 = compress((array(filt) == _fil) & (array(tel) == _tel), array(date))
            filename0 = compress((array(filt) == _fil) & (array(tel) == _tel), array(filename))
            z10 = compress((array(filt) == _fil) & (array(tel) == _tel), array(z1))
            z20 = compress((array(filt) == _fil) & (array(tel) == _tel), array(z2))
            magtype0 = compress((array(filt) == _fil) & (array(tel) == _tel), array(magtype))
            inds = argsort(mjd0)
            mag0 = take(mag0, inds)
            dmag0 = take(dmag0, inds)
            date0 = take(date0, inds)
            filename0 = take(filename0, inds)
            mjd0 = take(mjd0, inds)
            z10 = take(z10, inds)
            z20 = take(z20, inds)
            magtype0 = take(magtype0, inds)
            # z3= 
            magtype1, mag1, dmag1, mjd1, date1, filename1 = [], [], [], [], [], []
            done = []
            for i in range(0, len(mjd0)):
                if i not in done:
                    ww = asarray([j for j in range(len(mjd0)) if (mjd0[j] - mjd0[i]) < _bin and (
                    mjd0[j] - mjd0[i]) >= 0.0])  # abs(jd0[j]-jd0[i])<bin])
                    for jj in ww: done.append(jj)
                    if len(ww) >= 2:
                        mjd1.append(mean(mjd0[ww]))

                        av,st=weighted_avg_and_std(mag0[ww], 1/(dmag0[ww])**2)
                        print av,st
                        mag1.append(av)
                        try:
                            # error underestimate, adding 0.01 to take in account the error in the zeropoint
                            dmag1.append(st+0.01)
                            #dmag1.append(st)
                        except:
                            dmag1.append(0.0)
                        magtype1.append(std(magtype0[ww]))
                        filename1.append(filename0[ww])
                        date1.append(date0[ww][0] + datetime.timedelta(mean(mjd0[ww]) - mjd0[ww][0]))
                    elif len(ww) == 1:
                        mjd1.append(mjd0[ww][0])
                        mag1.append(mag0[ww][0])
                        magtype1.append(magtype0[ww][0])
                        dmag1.append(dmag0[ww][0])
                        date1.append(date0[ww][0])
                        filename1.append(filename0[ww][0])
            setup[_tel][_fil]['mag'] = mag1
            setup[_tel][_fil]['magtype'] = magtype1
            setup[_tel][_fil]['dmag'] = dmag1
            setup[_tel][_fil]['mjd'] = list(array(mjd1))
            setup[_tel][_fil]['jd'] = list(array(mjd1) + 2400000.5)
            setup[_tel][_fil]['date'] = date1
            setup[_tel][_fil]['filename'] = filename1

    if _show:
        plotfast2(setup)
    elif _output:
        plotfast(setup, _output)

    linetot = {}
    if _output:
        ff = open(_output, 'w')

    filters_used = sum([[lsc.sites.filterst1[filt] for filt in setup[_tel].keys()] for _tel in setup], [])
    filters = []
    for filt in 'UBVRIugriz':
        if filt in filters_used:
            filters.append(filt)
    for _tel in setup:
        line0 = '# %15s%15s' % ('dateobs', 'jd')
        for filt in filters:
            if filt in [lsc.sites.filterst1[key] for key in setup[_tel]]:
                line0 += '%12s%12s ' % (str(filt), str(filt) + 'err')
        for _fil in setup[_tel]:
            for j in range(0, len(setup[_tel][_fil]['mjd'])):
                line = '  %10s %12.4f ' % (str(setup[_tel][_fil]['date'][j]), setup[_tel][_fil]['jd'][j])
                for filt in filters:
                    if _fil in lsc.sites.filterst[filt]:
                        line += '%12.4f %12.4f ' % (setup[_tel][_fil]['mag'][j], setup[_tel][_fil]['dmag'][j])
                    else:
                        line += '%12s %12s ' % ('9999', '0.0')
                line += '%6s %2s\n' % (_tel, lsc.sites.filterst1[_fil])
                linetot[setup[_tel][_fil]['mjd'][j]] = line
    aaa = linetot.keys()
    if _output:
        for gg in sort(aaa):
            ff.write(linetot[gg])
    else:
        for gg in sort(aaa):
            print linetot[gg]
    if _output:
        ff.close()

def run_cat(imglist, extlist, _interactive=False, mode=1, _type='fit', _fix=False, database='photlco', _field='slaon'):
    import lsc

    direc = lsc.__path__[0]
    from numpy import where, array
    import mysqldef
    import os, string, glob  # MySQLdb,

    status = []
    if mode == 1:
        _mode = 'lsccatalogue.py'
        stat = 'abscat'
    elif mode == 2:
        _mode = 'lscmag.py'
        stat = 'mag'
    if len(extlist) > 0:
        for img in extlist:  status.append(checkstage(img, stat))
        extlist = extlist[where(array(status) > 0)]
        status = array(status)[where(array(status) > 0)]
        f = open('_tmpext.list', 'w')
        for img in extlist:
            ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
            _dir = ggg[0]['filepath']
            f.write(_dir + re.sub('fits', 'sn2.fits', img) + '\n')
        f.close()
    else:
        for img in imglist:
            status.append(checkstage(img, stat))
        imglist = imglist[where(array(status) > 0)]
        status = array(status)[where(array(status) > 0)]

    f = open('_tmp.list', 'w')
    for img in imglist:
        ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
        _dir = ggg[0]['filepath']
        f.write(_dir + re.sub('fits', 'sn2.fits', img) + '\n')
    f.close()
    if _interactive:
        ii = ' -i '
    else:
        ii = ''
    if _fix:
        ff = ' -c '
    else:
        ff = ''
    tt = ' -t ' + _type + ' '
    if _field:
        ss = ' -s ' + _field
    else:
        ss = ''
    # catalogue doesn't want to specify the system (sloan.landolt,apass)
    if mode == 1: ss = ''

    if len(extlist) > 0:
        command = _mode + ' _tmp.list -e _tmpext.list ' + ii + tt + ff + ss
    else:
        command = _mode + ' _tmp.list ' + ii + tt + ff + ss
    print command
    os.system(command)


def run_wcs(imglist, interactive=False, redo=False, _xshift=0, _yshift=0, catalogue='', database='photlco', mode='sv'):
    for img in imglist:
        status = checkstage(img, 'wcs')
        if status == -4 and redo:
            print 'wcs not good, try again'
            lsc.mysqldef.updatevalue(database, 'quality', 0, os.path.split(img)[-1])
            status = checkstage(img, 'wcs')
        if status >= -1:
            ggg = lsc.mysqldef.getfromdataraw(conn, database, 'filename', img, '*')
            _dir = ggg[0]['filepath']
            if mode =='sv':
                command = 'lscastro.py ' + _dir + img + ' -m  vizir --xshift ' + str(_xshift) + ' --yshift ' + str(_yshift)
                if status == 0 or redo:
                    command += ' -r'
                if interactive:
                    command += ' -i'
                if catalogue:
                    command += ' -c ' + catalogue
                else:
                    for field in ['apass', 'sloan', 'landolt']:
                        _catalogue = lsc.util.getcatalog(_dir + img, field)
                        if _catalogue:
                            command += ' -c ' + _catalogue
                            break
                print command
                os.system(command)
            elif mode == 'astrometry':
                lsc.lscastrodef.run_astrometry(_dir + img, True, redo)
            else:
                print str(_mode)+' not defined'
        elif status == 0:
            print 'status ' + str(status) + ': WCS stage not done'
        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        else:
            print 'status ' + str(status) + ': unknown status'


def run_zero(imglist, _fix, _type, _field, catalogue, _color='', interactive=False, redo=False, show=False, _cutmag=99,
             database='photlco', _calib='', zcatnew=False):
    import lsc
    import os, string, glob  # MySQLdb,

    direc = lsc.__path__[0]
    for img in imglist:
        if interactive:
            ii = '-i'
        else:
            ii = ''
        if _fix:
            ff = '-f'
        else:
            ff = ''
        if redo:
            rr = '-r'
        else:
            rr = ''
        if _field:
            ss = '-s ' + _field
        else:
            ss = ''
        if show:
            dd = '--show'
        else:
            dd = ''
        if _calib:
            ll = '--calib ' + _calib
        else:
            ll = ''
        if _color:
            hh = '-C ' + _color
        else:
            hh = ''
        status = checkstage(img, 'zcat')
        if status == 1: rr = '-r'
        if status >= 1:
            ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
            _dir = ggg[0]['filepath']
            if catalogue:
                cc = '-c ' + catalogue
            else:
                _catalogue = lsc.util.getcatalog(_dir + img, _calib if _calib else _field)
                if _catalogue:
                    cc = '-c ' + _catalogue
                else:
                    cc = ''
            if zcatnew: zcn = '--zcatnew'
            else: zcn = ''
            command = ' '.join(['lscabsphot.py', _dir+re.sub('fits', 'sn2.fits',img), ii, rr, ff, cc, '-t', _type, ss, dd, hh, ll, '--cutmag', str(_cutmag), zcn])
            print '_'*100
            print command
            os.system(command)
        elif status == 0:
            print 'status ' + str(status) + ': WCS stage not done'
        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        else:
            print 'status ' + str(status) + ': unknown status'


def run_psf(imglist, treshold=5, interactive=False, _fwhm='', show=False, redo=False, xwindow='',\
            fix=True, catalog='', database='photlco', use_sextractor=False, datamax=None, nstars=6):
    import lsc
    import os
    import  string
    import sys

    direc = lsc.__path__[0]
    for img in imglist:
        if interactive:
            ii = '-i'
        else:
            ii = ''
        if show:
            ss = '-s'
        else:
            ss = ''
        if redo:
            rr = '-r'
        else:
            rr = ''
        if _fwhm:
            ff = '-f ' + str(_fwhm) + ' '
        else:
            ff = ''
        if fix:
            gg = ' '
        else:
            gg = ' --fix '
        if catalog:
            cc=' --catalog '+catalog+' '
        else:
            cc=' '
        if use_sextractor:
            xx = ' --use-sextractor '
        else:
            xx = ''
        if datamax is not None:
            dm = ' --datamax ' + str(datamax) + ' '
        else:
            dm = ' '
        pp = ' -p ' + str(nstars) + ' '

        status = checkstage(img, 'psf')
        print status
        if status == 1:
            rr = '-r'
        if status >= 1:
            ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
            print ggg
            if str(ggg[0]['filetype']) == '3':
                ##################################################################################
                print '\n### get parameters for difference image'
                _dir = ggg[0]['filepath']
                hdrdiff=lsc.util.readhdr(_dir+img)
                if 'PSF' not in hdrdiff:
                    sys.exit('\n### warning PSF file not defined')
                else:
                    imgpsf=hdrdiff['PSF']
                    print '\n### psf file for difference image: '+imgpsf
                    statuspsf = checkstage(imgpsf, 'psf')
                    print statuspsf
                    if statuspsf == 2:
                        print 'psf file for difference image found'
                        gggpsf = mysqldef.getfromdataraw(conn, database, 'filename', str(imgpsf), '*')
                        _dirpsf = gggpsf[0]['filepath']
                        os.system('cp '+_dirpsf+re.sub('.fits', '.psf.fits', imgpsf)+' '+_dir+
                                  re.sub('.fits', '.psf.fits', img))
                        lsc.mysqldef.updatevalue('photlco', 'psf', re.sub('.fits', '.psf.fits', img),
                                             string.split(img, '/')[-1])
                        print '\n ### copy '+re.sub('.fits', '.psf.fits', imgpsf)+' in '+re.sub('.fits', '.psf.fits', img)

                    else:
                        print '\n### ERROR: PSF file not found \n please run psf file on image: '+imgpsf
                #####################################################################################
                if 'PHOTNORM' not in hdrdiff:
                    sys.exit('\n ### warning PHOTNORM file not defined')
                else:
                    photnorm=hdrdiff['PHOTNORM']
                    if photnorm=='t':
                        print '\n ### zero point done with template'
                        imgtable = hdrdiff['TEMPLATE']

                    elif photnorm=='i':
                        print '\n ### zero point done with target'
                        imgtable = hdrdiff['TARGET']

                    sntable = re.sub('.fits','.sn2.fits',imgtable)
                    gggtable = lsc.mysqldef.getfromdataraw(conn, database, 'filename', str(imgtable), '*')
                    dirtable = gggtable[0]['filepath']

                    if os.path.isfile(dirtable+sntable):
                        print '\n ### fits table found '
                        print 'cp ' + dirtable + sntable + ' ' + _dir + re.sub('.fits', '.sn2.fits', img)
                        os.system('cp ' + dirtable + sntable + ' ' + _dir + re.sub('.fits', '.sn2.fits', img))
                    else:
                        sys.exit('ERROR: fits table not there, run psf for ' + sntable)
            else:
                _dir = ggg[0]['filepath']
                img0 = img
                command = 'lscpsf.py ' + _dir + img0 + ' ' + ii + ' ' + ss + ' ' + rr + ' ' + ff + ' ' + '-t ' + str(
                    treshold) + xwindow + gg + cc + xx + dm + pp
                print command
                os.system(command)
        elif status == 0:
            print 'status ' + str(status) + ': WCS stage not done'
        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        else:
            print 'status ' + str(status) + ': unknown status'
    # #################################################################


def run_fit(imglist, _ras='', _decs='', _xord=3, _yord=3, _bkg=4, _size=7, _recenter=False, _ref='', interactive=False,
            show=False, redo=False, dmax=None, dmin=None, database='photlco', _ra0='', _dec0=''):
    import lsc
    import os, string
    from astropy.io import fits

    direc = lsc.__path__[0]

    if interactive:
        ii = ' -i'
    else:
        ii = ''
    if _recenter:
        cc = ' -c'
    else:
        cc = ''
    if show:
        ss = ' -s'
    else:
        ss = ''
    if redo:
        rr = ' -r'
    else:
        rr = ''
    if _ras:
        _ras = ' -R ' + str(_ras)
    if _decs:
        _decs = ' -D ' + str(_decs)
    if _ra0:
        _ra0 =  ' --RA0 ' + str(_ra0)
    if _dec0:
        _dec0 = ' --DEC0 ' + str(_dec0)
    if dmax is not None:
        _dmax = ' --datamax ' + str(dmax)
    else:
        _dmax = ''
    if dmin is not None:
        _dmin = ' --datamin ' + str(dmin)
    else:
        _dmin = ''

    for img in imglist:
        status = checkstage(img, 'psfmag')
        print status
        if status >= 1:
            ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
            _dir = ggg[0]['filepath']
            img0 = re.sub('.fits', '.sn2.fits', img)

            if _ref:
                print img0, _ref, show
                _ras, _decs = lsc.myloopdef.getcoordfromref(img0, _ref, show)

            command = 'lscsn.py ' + _dir + img + ii + ss + rr + cc + ' -x ' + str(_xord) + ' -y ' + str(_yord) + \
                      _ras + _decs + _ra0 + _dec0 + ' -b ' + str(_bkg) + ' -z ' + str(_size) + _dmax + _dmin
            #if str(ggg[0]['filetype']) == '3':
            #    try:
            #        img2 = fits.getheader(_dir + img)['PSF']
            #        ggg2 = mysqldef.getfromdataraw(conn, database, 'filename', str(img2), '*')
            #        _dir2 = ggg2[0]['filepath']
            #        pp = ' -p ' + _dir2 + re.sub('.fits', '.psf.fits', img2) + ' '
            #        command = command + pp
            #    except:
            #        command = ''
            #        print 'PSF header not found in ' + str(img)
            print command
            os.system(command)
        elif status == 0:
            print 'status ' + str(status) + ': psf stage not done'
        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        else:
            print 'status ' + str(status) + ': unknown status'
    # #################################################################


def checkstage(img, stage, database='photlco'):
    # -4  bad quality
    #  -3  image not ingested in the dedu table
    #  -2  image not in the working directory
    #  -1  sn2 not in the working directory
    #   0  not done and previous stage not done
    #   1  not done and possible since previous stage done
    #   2  done and possible to do again
    #   3  local sequence catalogue available  
    import mysqldef
    import os

    status = 0
    ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
    if not ggg:
        status = -3  # not in the redo table
    else:
        _dir = ggg[0]['filepath']
        if ggg[0]['quality'] == 1:
            status = -4  #  bad quality image
        else:
            if not os.path.isfile(_dir + img):
                status = -2  # fits image not in working dir
            elif not os.path.isfile(_dir + re.sub('fits', 'sn2.fits', img)):
                status = -1  # sn2 table not in working dir
    if stage == 'wcs' and status >= -1:
        if ggg[0]['wcs'] != 0:
            status = 1
        else:
            status = 2
    elif stage == 'psf' and status >= -1 and ggg[0]['wcs'] == 0:
        if ggg[0]['psf'] == 'X':
            status = 1
        else:
            status = 2
    elif stage == 'psfmag' and status >= 0 and ggg[0]['psf'] != 'X' and ggg[0]['wcs'] == 0:
        if ggg[0]['psfmag'] == 9999 or ggg[0]['psfmag'] == 9999:
            status = 1
        else:
            status = 2
    elif stage == 'zcat' and status >= 0 and ggg[0]['psf'] != 'X' and ggg[0]['wcs'] == 0:
        if ggg[0]['zcat'] == 'X':
            status = 1
        else:
            status = 2
    elif stage == 'mag' and status >= 0 and ggg[0]['zcat'] != 'X' and ggg[0]['psfmag'] != 9999:
        if ggg[0]['mag'] == 9999:
            status = 1
        else:
            status = 2
    elif stage == 'abscat' and status >= 0 and ggg[0]['zcat'] != 'X' and ggg[0]['psf'] != 'X':
        if ggg[0]['abscat'] == 'X':
            status = 1  # mag should be replaced with 'cat'
        else:
            status = 2
    elif stage == 'checkpsf' and status >= -1 and ggg[0]['wcs'] == 0:
        if ggg[0]['psf'] == 'X':
            status = 1
        else:
            status = 2
    elif stage == 'checkmag' and status >= 0 and ggg[0]['psf'] != 'X' and ggg[0]['wcs'] == 0:
        if ggg[0]['psfmag'] == 9999:
            status = 1
        else:
            status = 2
    else:
        pass
    return status


# ###################################################################################
def getcoordfromref(img2, img1, _show, database='photlco'):  #img1.sn2  img2.sn2  import pyraf outside
    import lsc
    from astropy.io import fits
    from numpy import zeros, array, median, compress
    from pyraf import iraf

    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    ggg1 = mysqldef.getfromdataraw(conn, database, 'filename', re.sub('sn2.fits', 'fits', img1), '*')
    _dir1 = ggg1[0]['filepath']

    ggg2 = mysqldef.getfromdataraw(conn, database, 'filename', re.sub('sn2.fits', 'fits', img2), '*')
    _dir2 = ggg2[0]['filepath']

    print _dir1, _dir2, img1, img2

    dicti1 = lsc.lscabsphotdef.makecatalogue([_dir1 + img1])
    dicti2 = lsc.lscabsphotdef.makecatalogue([_dir2 + img2])
    for i in dicti1.keys():
        for j in dicti1[i].keys():
            ra01 = dicti1[i][j]['ra0']
            dec01 = dicti1[i][j]['dec0']
    for i in dicti2.keys():
        for j in dicti2[i].keys():
            ra02 = dicti2[i][j]['ra0']
            dec02 = dicti2[i][j]['dec0']

    print _dir1 + img1
    t = fits.open(_dir1 + img1)
    tbdata = t[1].data
    hdr1 = t[0].header
    psfx1 = lsc.util.readkey3(hdr1, 'PSFX1')
    psfy1 = lsc.util.readkey3(hdr1, 'PSFY1')
    print psfx1, psfy1, 'dddd'
    if psfx1 != None and psfy1 != None:
        lll = str(psfx1) + ' ' + str(psfy1)
        aaa = iraf.wcsctran('STDIN', 'STDOUT', _dir1 + img1 + '[0]', Stdin=[lll], inwcs='logical', units='degrees degrees',
                            outwcs='world', columns='1 2', formats='%10.5f %10.5f', Stdout=1)[3]
        rasn1, decsn1 = string.split(aaa)
        if _show:
            iraf.set(stdimage='imt8192')
            iraf.display(_dir1 + re.sub('sn2.fits', 'fits', img1) + '[0]', 1, fill=True, Stdout=1, zsc='yes',
                         zra='yes')  #,z1=0,z2=3000)
            iraf.tvmark(1, 'STDIN', Stdin=[lll], mark="cross", number='no', label='no', radii=5, nxoffse=5, nyoffse=5,
                        color=205, txsize=1)

        #    ra01,dec01,ra02,dec02=array(ra01,float),array(dec01,float),array(ra02,float),array(dec02,float)
    distvec, pos1, pos2 = lsc.lscastrodef.crossmatch(list(ra01), list(dec01), list(ra02), list(dec02), 5)
    #    from pylab import ion,plot
    #    ion()
    #    plot(ra01,dec01,'or')
    #    plot(ra02,dec02,'xb',markersize=10)
    #    plot(array(ra01)[pos1],array(dec01)[pos1],'3g',markersize=20)
    #    plot(array(ra02)[pos2],array(dec02)[pos2],'*m',markersize=10)
    #    raw_input('ddd')
    rra = ra01[pos1] - ra02[pos2]
    ddec = dec01[pos1] - dec02[pos2]
    rracut = compress((abs(array(ra02[pos2]) - float(rasn1)) < .05) & (abs(array(dec02[pos2]) - float(decsn1)) < .05),
                      array(rra))
    ddeccut = compress((abs(array(ra02[pos2]) - float(rasn1)) < .05) & (abs(array(dec02[pos2]) - float(decsn1)) < .05),
                       array(ddec))

    if len(rracut) > 10:
        rasn2c = float(rasn1) - median(rracut)
        decsn2c = float(decsn1) - median(ddeccut)
    else:
        rasn2c = float(rasn1) - median(rra)
        decsn2c = float(decsn1) - median(ddec)

    if _show:
        print 'shift in arcsec (ra dec)'
        print len(pos1), len(ra01)
        print median(rra), median(ddec)
        print 'SN position on image 2 computed'
        print rasn2c, decsn2c
        iraf.display(_dir2 + re.sub('sn2.fits', 'fits', img2) + '[0]', 2, fill=True, Stdout=1, zsc='yes',
                     zra='yes')  #,z1=0,z2=3000)
        lll = str(rasn2c) + ' ' + str(decsn2c)
        bbb = iraf.wcsctran('STDIN', 'STDOUT', _dir2 + img2 + '[0]', Stdin=[lll], inwcs='world', units='degrees degrees',
                            outwcs='logical', columns='1 2', formats='%10.5f %10.5f', Stdout=1)[3]
        iraf.tvmark(2, 'STDIN', Stdin=[bbb], mark="cross", number='no', label='no', radii=5, nxoffse=5, nyoffse=5,
                    color=206, txsize=1)
        from pylab import ion, plot

        ion()
        plot(rra, ddec, 'or')
        plot(rracut, ddeccut, 'xb')

    return rasn2c, decsn2c


def filtralist(ll2, _filter, _id, _name, _ra, _dec, _bad, _filetype=1, _groupid='', _instrument='', _temptel='', _difftype=''):
    from numpy import array, asarray
    import string, re, os, sys
    import lsc

    ll1 = {}
    for key in ll2.keys():
        ll1[key] = ll2[key][:]

    if len(_difftype) > 0:
        ww = asarray([i for i in range(len(ll1['difftype'])) if ((str(ll1['difftype'][i]) in str(_difftype)))])
        if len(ww) > 0:
            for jj in ll1.keys():
                ll1[jj] = array(ll1[jj])[ww]
        else:
            for jj in ll1.keys():
                ll1[jj] = []

    if _filetype:
        if int(_filetype) in [1, 2, 3, 4]:
            ww = asarray([i for i in range(len(ll1['filetype'])) if ((ll1['filetype'][i] == str(_filetype)))])
            if len(ww) > 0:
                for jj in ll1.keys():
                    ll1[jj] = array(ll1[jj])[ww]
            else:
                for jj in ll1.keys():
                    ll1[jj] = []

    if _bad and _bad == 'quality':
        pass

    else:
        ww = asarray([i for i in range(len(ll1['quality'])) if ((ll1['quality'][i] != 1))])
        if len(ww) > 0:
            for jj in ll1.keys():
                ll1[jj] = array(ll1[jj])[ww]
        else:
            for jj in ll1.keys():
                ll1[jj] = []
    if _filter:  #filter 
        if _filter == 'sloan':
            ww = asarray([i for i in range(len(ll1['filter'])) if (
            (ll1['filter'][i] in ['zs', 'up', 'gp', 'ip', 'rp', 'SDSS-G', 'SDSS-R', 'SDSS-I', 'Pan-Starrs-Z']))])
        elif _filter == 'landolt':
            ww = asarray([i for i in range(len(ll1['filter'])) if (
            (ll1['filter'][i] in ['U', 'B', 'V', 'R', 'I', 'Bessell-B', 'Bessell-V', 'Bessell-R', 'Bessell-I']))])
        elif _filter == 'apass':
            ww = asarray([i for i in range(len(ll1['filter']))
                          if ((ll1['filter'][i] in ['B', 'V', 'Bessell-B','Bessell-V', 'gp', 'ip', 'rp', 'SDSS-G',
                                                    'SDSS-R', 'SDSS-I']))])
        else:
            lista = []
            for fil in string.split(_filter, ','):
                print fil
                if fil in lsc.sites.filterst:
                    lista += lsc.sites.filterst[fil]
                elif fil in ['zs', 'up', 'gp', 'ip', 'rp', 'U', 'B', 'V', 'R', 'I', 'SDSS-G', 'SDSS-R', 'SDSS-I',
                             'Pan-Starrs-Z', 'Bessell-B', 'Bessell-V', 'Bessell-R', 'Bessell-I']:
                    lista.append(fil)
            print lista
            ww = asarray([i for i in range(len(ll1['filter'])) if ((ll1['filter'][i] in lista))])
        if len(ww) > 0:
            for jj in ll1.keys():
                ll1[jj] = array(ll1[jj])[ww]
        else:
            for jj in ll1.keys():
                ll1[jj] = []
    if _id:  # ID
        try:
            xx = '0000'[len(_id):] + _id
            ww = asarray([i for i in range(len(ll1['filter'])) if ((_id in string.split(ll1['filename'][i], '-')[3]))])
        except:
            ww = asarray([i for i in range(len(ll1['filter'])) if (_id in ll1['filename'][i])])
        if len(ww) > 0:
            for jj in ll1.keys():
                ll1[jj] = array(ll1[jj])[ww]
        else:
            for jj in ll1.keys():
                ll1[jj] = []
    if _name:  # name
        _targetid = lsc.mysqldef.gettargetid(_name, '', '', conn, 0.01, False)
        if _targetid:
            print _targetid
            ww = asarray([i for i in range(len(ll1['filter'])) if ((_targetid == ll1['targetid'][i]))])
        else:
            ww = asarray([i for i in range(len(ll1['filter'])) if ((_name in ll1['objname'][i]))])

        if len(ww) > 0:
            for jj in ll1.keys():
                ll1[jj] = array(ll1[jj])[ww]
        else:
            for jj in ll1.keys():
                ll1[jj] = []
    if _groupid:
        ww = asarray([i for i in range(len(ll1['filter'])) if ((ll1['groupidcode'][i] != _groupid))])
        if len(ww) > 0:
            for jj in ll1.keys():
                ll1[jj] = array(ll1[jj])[ww]
        else:
            for jj in ll1.keys():
                ll1[jj] = []

    if _ra and _dec:
        from numpy import abs

        ww = asarray([i for i in range(len(ll1['ra'])) if
                      ( abs(float(ll1['ra'][i]) - float(_ra)) < .5 and abs(float(ll1['dec'][i]) - float(_dec)) < .5 )])
        if len(ww) > 0:
            for jj in ll1.keys():
                ll1[jj] = array(ll1[jj])[ww]
        else:
            for jj in ll1.keys():
                ll1[jj] = []
####################
    #    add filter using instrument
    if _instrument:
        print _instrument
        ww = asarray([i for i in range(len(ll1['instrument'])) if (ll1['instrument'][i] == _instrument)])
        if len(ww) > 0:
            for jj in ll1.keys():
                ll1[jj] = array(ll1[jj])[ww]
        else:
            for jj in ll1.keys():
                ll1[jj] = []

    if _filetype == 3 and _temptel:
        temptels = np.array([fn.split('.')[1] if fn.count('.') == 3 else inst[0:2] for fn, inst in zip(ll1['filename'], ll1['instrument'])], dtype=str)
        for jj in ll1:
            ll1[jj] = array(ll1[jj])[temptels == _temptel]

######################
    if _bad:
        if _bad == 'wcs':
            ww = asarray([i for i in range(len(ll1[_bad])) if (ll1[_bad][i] != 0)])
        elif _bad == 'zcat' or _bad == 'abscat':
            ww = asarray([i for i in range(len(ll1[_bad])) if (ll1[_bad][i] == 'X' )])
        elif _bad == 'goodcat':
            ww = asarray([i for i in range(len(ll1['abscat'])) if (ll1['abscat'][i] != 'X' )])
        elif _bad == 'psf':
            ww = asarray([i for i in range(len(ll1['psf'])) if (ll1['psf'][i] == 'X' )])
        elif _bad == 'quality':
            ww = asarray([i for i in range(len(ll1['quality'])) if ((ll1['quality'][i] == 1))])
        elif _bad == 'cosmic':
            maskexists = [os.path.isfile(filepath+filename.replace('.fits', '.mask.fits'))
                            for filepath, filename in zip(ll1['filepath'], ll1['filename'])]
            ww = np.flatnonzero(np.logical_not(np.array(maskexists)))
        elif _bad == 'diff':
            maskexists = [os.path.isfile(filepath+filename.replace('.fits', '.diff.fits'))
                            for filepath, filename in zip(ll1['filepath'], ll1['filename'])]
            ww = np.flatnonzero(np.logical_not(np.array(maskexists)))
        elif _bad == 'mag':
            ww = asarray([i for i in range(len(ll1['mag'])) if (ll1['mag'][i] >= 1000 or ll1[_bad][i] < 0)])
        else:
            ww = asarray([i for i in range(len(ll1[_bad])) if (ll1[_bad][i] >= 1000)])
        if len(ww) > 0:
            for jj in ll1.keys(): ll1[jj] = array(ll1[jj])[ww]
        else:
            for jj in ll1.keys(): ll1[jj] = []

        if _bad == 'psfmag':  # do not consider standard field as bad psfmag files
            ww = asarray([i for i in range(len(ll1['objname'])) if (
            (ll1['objname'][i]) not in ['L104', 'L105', 'L95', 'L92', 'L106', 'L113', 'L101', 'L107', 'L110', 'MarkA',
                                        's82_00420020', 's82_01030111', 'Ru152'])])
            if len(ww) > 0:
                for jj in ll1.keys(): ll1[jj] = array(ll1[jj])[ww]
            else:
                for jj in ll1.keys(): ll1[jj] = []
            #          if _bad in ['goodcat']:
            #          else:
            #               ww=asarray([i for i in range(len(ll1[_bad])) if ((ll1['quality'][i]!=1))])
            #          if len(ww)>0:
            #               for jj in ll1.keys(): ll1[jj]=array(ll1[jj])[ww]
            #          else:  
            #               for jj in ll1.keys(): ll1[jj]=[]

    return ll1


#########################################################################
def run_local(imglist, _field, _interactive=False, database='photlco'):
    import lsc

    direc = lsc.__path__[0]
    import os, string, glob  #MySQLdb,

    ff = open('_tmpcat.list', 'w')
    for img in imglist:
        ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
        if ggg:
            _dir = ggg[0]['filepath']
            if ggg[0]['abscat'] != 'X':
                ff.write(_dir + re.sub('.fits', '.cat', img) + '\n')
    ff.close()
    if _interactive:
        ii = ' -i '
    else:
        ii = ''
    if _field:
        _field = ' -f ' + _field
    else:
        _field = ''
    command = 'lscmaglocal.py _tmpcat.list ' + ii + ' ' + _field
    print command
    os.system(command)


##########################################################################
def position(imglist, ra1, dec1, show=False):
    import lsc
    from pyraf import iraf
    from astropy.io import fits
    from numpy import array, zeros, median, argmin, cos, abs, pi, mean

    iraf.imcoords(_doprint=0)
    ra, dec = [], []
    if not ra1 and not dec1:
        for img in imglist:
            t = fits.open(img)
            tbdata = t[1].data
            hdr1 = t[0].header
            psfx = lsc.util.readkey3(hdr1, 'PSFX1')
            psfy = lsc.util.readkey3(hdr1, 'PSFY1')
            if psfx != None and psfy != None:
                lll = str(psfx) + ' ' + str(psfy)
                aaa = iraf.wcsctran('STDIN', 'STDOUT', img + '[0]', Stdin=[lll], inwcs='logical', units='degrees degrees',
                                    outwcs='world', columns='1 2', formats='%10.5f %10.5f', Stdout=1)[3]
                try:
                    ra.append(float(string.split(aaa)[0]))
                    dec.append(float(string.split(aaa)[1]))
                except:
                    pass
    else:
        for img in imglist:
            dicti = lsc.lscabsphotdef.makecatalogue([img])
            for i in dicti.keys():
                for j in dicti[i].keys():
                    ra0 = dicti[i][j]['ra']
                    dec0 = dicti[i][j]['dec']
                    ra00 = zeros(len(ra0))
                    dec00 = zeros(len(ra0))
                    for i in range(0, len(ra0)):
                        ra00[i] = float(iraf.real(ra0[i])) * 15
                        dec00[i] = float(iraf.real(dec0[i]))
                    distvec, pos0, pos1 = lsc.lscastrodef.crossmatch(array([float(ra1)]), array([float(dec1)]),
                                                                     array(ra00, float), array(dec00, float), 5)
                    if len(pos1) >= 1:
                        ra.append(ra00[pos1[argmin(distvec)]])
                        dec.append(dec00[pos1[argmin(distvec)]])
                        print i, j, ra00[pos1[argmin(distvec)]], dec00[pos1[argmin(distvec)]]
                    #                        iraf.display(re.sub('.sn2.','.',j),1,fill=True,Stdout=1)
                    #                        lll=str(ra00[pos1[argmin(distvec)]])+' '+str(dec00[pos1[argmin(distvec)]])
                    #                        aaa=iraf.wcsctran('STDIN','STDOUT',j,Stdin=[lll],inwcs='world',units='degrees degrees',outwcs='logical',columns='1 2',formats='%10.5f %10.5f',Stdout=1)[3]
                    #                        iraf.tvmark(1,'STDIN',Stdin=list([aaa]),mark="circle",number='yes',label='no',radii=20,nxoffse=5,nyoffse=5,color=205,txsize=2)
                    #                        raw_input('ddd')
    if show:
        from pylab import ion, plot, xlim, ylim, xlabel, ylabel, getp, setp, legend, gca

        ion()
        xlabel('ra (arcsec)')
        ylabel('dec (arcsec)')
        yticklabels = getp(gca(), 'yticklabels')
        xticklabels = getp(gca(), 'xticklabels')
        setp(xticklabels, fontsize='20')
        setp(yticklabels, fontsize='20')
        legend(numpoints=1, markerscale=1.5)
        print median(dec)
        plot(((ra - median(ra)) * 3600) * cos(median(dec) * pi / 180.), (dec - median(dec)) * 3600, 'or',
             label='position')
    try:
        ra, dec = mean(ra), mean(dec)
    except:
        ra = ''
        dec = ''
    return ra, dec


#########################################################################
def checkcat(imglist, database='photlco'):
    import lsc
    import os, string  #MySQLdb,

    for img in imglist:
        status = checkstage(img, 'checkpsf')
        #print img,status
        if status >= 1:
            ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
            _dir = ggg[0]['filepath']
            print _dir, img
            if os.path.isfile(_dir + re.sub('.fits', '.cat', img)):
                aa = raw_input('>>>good catalogue [[y]/n] or [b] bad quality ? ')
                if not aa: aa = 'y'
                if aa in ['n', 'N', 'No', 'NO', 'bad', 'b', 'B']:
                    print 'updatestatus bad catalogue'
                    lsc.mysqldef.updatevalue(database, 'abscat', 'X', string.split(img, '/')[-1])
                    lsc.util.delete(_dir + re.sub('.fits', '.cat', img))
                    if aa in ['bad', 'b', 'B']:
                        print 'updatestatus bad quality'
                        lsc.mysqldef.updatevalue(database, 'quality', 1, string.split(img, '/')[-1])
                        lsc.util.delete(_dir + re.sub('.fits', '.cat', img))
            else:
                lsc.mysqldef.updatevalue(database, 'abscat', 'X', string.split(img, '/')[-1])
        elif status == 0:
            print 'status ' + str(status) + ': WCS stage not done'
        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        else:
            print 'status ' + str(status) + ': unknown status'


def checkpsf(imglist, database='photlco'):
    import lsc
    import os, string  #MySQLdb,
    import mysqldef

    direc = lsc.__path__[0]
    from pyraf import iraf

    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    for img in imglist:
        status = checkstage(img, 'checkpsf')
        print img, status
        if status >= 1:
            ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
            _dir = ggg[0]['filepath']
            iraf.delete('_psf.psf.fits', verify=False)
            if os.path.isfile(_dir + re.sub('.fits', '.psf.fits', img)):
                print img
                lsc.util.marksn2(_dir + img, _dir + re.sub('fits', 'sn2.fits', img))
                iraf.seepsf(_dir + re.sub('.fits', '.psf.fits', img), '_psf.psf')
                iraf.surface('_psf.psf')
                aa = raw_input('>>>good psf [[y]/n] or [b] bad quality ? ')
                if not aa: aa = 'y'
                if aa in ['n', 'N', 'No', 'NO', 'bad', 'b', 'B']:
                    print 'updatestatus bad'
                    mysqldef.updatevalue(database, 'psf', 'X', string.split(img, '/')[-1])
                    mysqldef.updatevalue(database, 'psfmag', 9999, string.split(img, '/')[-1])
                    if os.path.isfile(_dir + re.sub('.fits', '.psf.fits', img)):
                        print 'rm ' + _dir + re.sub('.fits', '.psf.fits', img)
                        os.system('rm ' + _dir + re.sub('.fits', '.psf.fits', img))
                    if os.path.isfile(_dir + re.sub('.fits', '.sn2.fits', img)):
                        print 'rm ' + _dir + re.sub('.fits', '.sn2.fits', img)
                        os.system('rm ' + _dir + re.sub('.fits', '.sn2.fits', img))
                    if aa in ['bad', 'b', 'B']:
                        print 'updatestatus bad quality'
                        mysqldef.updatevalue(database, 'quality', 1, string.split(img, '/')[-1])
        elif status == 0:
            print 'status ' + str(status) + ': WCS stage not done'
        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        else:
            print 'status ' + str(status) + ': unknown status'

    #############################################################################


def checkwcs(imglist, force=True, database='photlco', _z1='', _z2=''):
    import lsc
    import os, string  #MySQLdb,
    import mysqldef  #import updatevalue

    direc = lsc.__path__[0]
    from pyraf import iraf

    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    iraf.set(stdimage='imt1024')
    print force
    print _z1, _z2
    for img in imglist:
        status = checkstage(img, 'wcs')
        if status >= 0 or force == False:
            ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
            _dir = ggg[0]['filepath']
            _filter = ggg[0]['filter']
            _exptime = ggg[0]['exptime']
            if _z1 != None and _z2 != None:
                iraf.display(_dir + img + '[0]', 1, fill=True, Stdout=1, zscale='no', zrange='no', z1=_z1, z2=_z2)
            else:
                iraf.display(_dir + img + '[0]', 1, fill=True, Stdout=1)
                ###########################################
            _ra0, _dec0, _SN0 = lsc.util.checksnlist(_dir + img, 'supernovaelist.txt')
            if not _SN0:    _ra0, _dec0, _SN0 = lsc.util.checksnlist(_dir + img, 'standardlist.txt')
            if not _SN0:    _ra0, _dec0, _SN0, _tt = lsc.util.checksndb(_dir + img, 'targets')
            print _ra0, _dec0, _SN0, img, _filter, _exptime
            if _SN0:
                ccc = iraf.wcsctran('STDIN', 'STDOUT', _dir + img + '[0]', Stdin=[str(_ra0) + ' ' + str(_dec0)], inwcs='world',
                                    units='degrees degrees', outwcs='logical', \
                                    columns='1 2', formats='%10.5f %10.5f', Stdout=1)
                iraf.tvmark(1, 'STDIN', Stdin=list(ccc), mark="circle", number='yes', label='no', radii=15, nxoffse=5,
                            nyoffse=5, color=206, txsize=3)

            for field in ['sloan', 'apass', 'landolt']:
                _catalogue = lsc.util.getcatalog(_dir + img, field)
                if _catalogue:
                    catvec = lsc.lscastrodef.readtxt(_catalogue)
                    bbb = [ra + ' ' + dec for ra, dec in zip(catvec['ra'], catvec['dec'])]
                    aaa = iraf.wcsctran('STDIN', 'STDOUT', _dir + img + '[0]', Stdin=bbb, inwcs='world', units='degrees degrees',
                                        outwcs='logical', columns='1 2', formats='%10.5f %10.5f', Stdout=1)
                    iraf.tvmark(1, 'STDIN', Stdin=list(aaa), mark="cross", number='yes', label='no', radii=1, nxoffse=5,
                                nyoffse=5, color=204, txsize=1)
                    break
            else:
                catvec = lsc.lscastrodef.querycatalogue('usnoa2', _dir + img, 'vizir')
                apix1 = catvec['pix']
                iraf.tvmark(1, 'STDIN', Stdin=list(apix1), mark="circle", number='yes', label='no', radii=20, nxoffse=5,
                            nyoffse=5, color=205, txsize=2)
            aa = raw_input('>>>good wcs [[y]/n] or [b] bad quality ? ')
            if not aa:
                aa = 'y'
            if aa in ['n', 'N', 'No', 'NO', 'bad', 'b', 'B']:
                print 'updatestatus bad'
                mysqldef.updatevalue(database, 'wcs', 9999, string.split(img, '/')[-1])
                mysqldef.updatevalue(database, 'psf', 'X', string.split(img, '/')[-1])
                mysqldef.updatevalue(database, 'psfmag', 9999, string.split(img, '/')[-1])
                if os.path.isfile(_dir + re.sub('.fits', '.psf.fits', img)):
                    print 'rm ' + _dir + re.sub('.fits', '.psf.fits', img)
                    os.system('rm ' + _dir + re.sub('.fits', '.psf.fits', img))
                if os.path.isfile(_dir + re.sub('.fits', '.sn2.fits', img)):
                    print 'rm ' + _dir + re.sub('.fits', '.sn2.fits', img)
                    os.system('rm ' + _dir + re.sub('.fits', '.sn2.fits', img))
                if aa in ['bad', 'b', 'B']:
                    print 'updatestatus bad quality'
                    mysqldef.updatevalue(database, 'quality', 1, string.split(img, '/')[-1])
            elif aa in ['c', 'C', 'cancel']:
                print 'remove from database'
                os.system('rm ' + _dir + img)
                lsc.mysqldef.deleteredufromarchive(string.split(img, '/')[-1], 'photlco', 'filename')
                lsc.mysqldef.deleteredufromarchive(string.split(img, '/')[-1], 'photpairing', 'nameout')
            #          elif status==0: print 'status '+str(status)+': WCS stage not done' 
        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        else:
            print 'status ' + str(status) + ': unknown status'

    ##################################################################


#############################################################################

def makestamp(imglist, database='photlco', _z1='', _z2='', _interactive=True, redo=False, _output=''):
    import lsc
    import os, string
    from astropy.io import fits
    import numpy as np
    import pylab as plt
    from astropy.wcs import WCS

    for img in imglist:
        _targetid = ''
        status = lsc.checkstage(img, 'wcs')
        if status >= 0:  # or force==False:
            ggg = lsc.mysqldef.getfromdataraw(lsc.conn, database, 'filename', str(img), '*')
            _dir = ggg[0]['filepath']
            _output = re.sub('.fits', '.png', _dir + '/' + img)
            if os.path.isfile(_output):
                if redo:
                    os.remove(_output)
                else:
                    status = -5
        if status >= 0:  # or force==False:
            _targetid = ggg[0]['targetid']
            hdr = fits.open(_dir + img)
            X = hdr[0].data
            header = hdr[0].header
            wcs = WCS(header)
            _ra0, _dec0, _SN0, _tt = lsc.util.checksndb(_dir + img, 'targets')
            if _SN0:
                [[xPix, yPix]] = wcs.wcs_world2pix([(_ra0, _dec0)], 1)
                if (xPix > 0 and xPix <= header.get('NAXIS1')) and (yPix <= header.get('NAXIS2') and yPix > 0):
                    xmin, xmax = xPix - 300, xPix + 300
                    ymin, ymax = yPix - 300, yPix + 300
                else:
                    try:
                        xmin, xmax = 0, header.get('NAXIS1')
                        ymin, ymax = 0, header.get('NAXIS2')
                    except:
                        xmin, xmax = 0, 1000
                        ymin, ymax = 0, 1000
                _sky, _sig = lsc.myloopdef.getsky(X[xmin:xmax, ymin:ymax])
                _z1 = _sky - _sig
                _z2 = _sky + _sig * 5
                plt.clf()
                try:
                    im = plt.imshow(X, cmap='gray', norm=None, aspect=None, interpolation='nearest', alpha=None,
                                    vmin=float(_z1), vmax=float(_z2), origin='upper', extent=None)
                except:
                    im = plt.imshow(X, cmap='gray', norm=None, aspect=None, interpolation='nearest', alpha=None, vmin=0,
                                    vmax=1000, origin='upper', extent=None)
                plt.xlim(float(xPix) - 200, float(xPix) + 200)
                plt.ylim(float(yPix) + 200, float(yPix) - 200)
                plt.plot([float(xPix)], [float(yPix)], marker='o', mfc='none', markersize=25, markeredgewidth=2,
                         markeredgecolor='r', label=str(_SN0))
                if _interactive:
                    plt.show()
                else:
                    print _output
                    lsc.delete(_output)
                    plt.savefig(_output)
            else:
                print _dir + img, _targetid
                print 'SN not found'

        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        elif status == -5:
            print 'status ' + str(status) + ': png already done'
        else:
            print 'status ' + str(status) + ': unknown status'


def checkfast(imglist, force=True, database='photlco'):
    import lsc
    import os, string  #MySQLdb,
    #     import  mysqldef #import updatevalue
    direc = lsc.__path__[0]
    from pyraf import iraf

    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    print force
    for img in imglist:
        status = checkstage(img, 'wcs')
        if status >= 0 or force == False:
            ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
            _dir = ggg[0]['filepath']
            iraf.display(_dir + img + '[0]', 1, fill=True, Stdout=1)
            ###########################################
            aa = raw_input('>>>good or bad quality [[g]/b]? ')
            if not aa: aa = 'g'
            if aa in ['bad', 'b', 'B']:
                lsc.mysqldef.updatevalue(database, 'wcs', 9999, string.split(img, '/')[-1])
                lsc.mysqldef.updatevalue(database, 'psf', 'X', string.split(img, '/')[-1])
                lsc.mysqldef.updatevalue(database, 'psfmag', 9999, string.split(img, '/')[-1])
                if os.path.isfile(_dir + re.sub('.fits', '.psf.fits', img)):
                    print 'rm ' + _dir + re.sub('.fits', '.psf.fits', img)
                    os.system('rm ' + _dir + re.sub('.fits', '.psf.fits', img))
                if os.path.isfile(_dir + re.sub('.fits', '.sn2.fits', img)):
                    print 'rm ' + _dir + re.sub('.fits', '.sn2.fits', img)
                    os.system('rm ' + _dir + re.sub('.fits', '.sn2.fits', img))
                print 'updatestatus bad quality'
                lsc.mysqldef.updatevalue(database, 'quality', 1, string.split(img, '/')[-1])
            else:
                print 'updatestatus quality good'
                lsc.mysqldef.updatevalue(database, 'quality', 127, string.split(img, '/')[-1])
            #          elif status==0: print 'status '+str(status)+': WCS stage not done' 
        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        else:
            print 'status ' + str(status) + ': unknown status'

    ##################################################################
def checkcosmic(imglist, database='photlco'):
    import lsc, os
    from pyraf import iraf
    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    for img in imglist:
        status = checkstage(img, 'wcs')
        if status >= 0:
            photlcodict = lsc.mysqldef.getfromdataraw(conn, database, 'filename', img, '*')
            _dir = photlcodict[0]['filepath']
            origimg = _dir + img
            maskimg = origimg.replace('.fits', '.mask.fits')
            cleanimg = origimg.replace('.fits', '.clean.fits')
            diffimg = origimg.replace('.fits', '.diff.fits')
            if os.path.isfile(origimg) and os.path.isfile(maskimg):
                print img, photlcodict[0]['filter']
                iraf.display(origimg + '[0]', 1, fill=True, Stdout=1)
                iraf.display(maskimg, 2, fill=True, Stdout=1)
                ans = raw_input('>>> good mask [[y]/n] or [b]ad quality? ')
                if ans in ['n', 'N', 'No', 'NO', 'bad', 'b', 'B']:
                    print 'updatestatus bad'
                    print 'rm', maskimg
                    os.system('rm ' + maskimg)
                    print 'rm', cleanimg
                    os.system('rm ' + cleanimg)
                    print 'rm', diffimg.replace('.fits', '*')
                    os.system('rm ' + diffimg.replace('.fits', '*'))
                    print 'delete', os.path.basename(diffimg), 'from database'
                    lsc.mysqldef.deleteredufromarchive(os.path.basename(diffimg), 'photlco', 'filename')
                if ans in ['bad', 'b', 'B']:
                    print 'updatestatus bad quality'
                    lsc.mysqldef.updatevalue(database, 'quality', 1, img)
            else:
                for f in [origimg, maskimg, cleanimg, diffimg]:
                    if not os.path.isfile(f): print f, 'not found'
        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        else:
            print 'status ' + str(status) + ': unknown status'

def checkdiff(imglist, database='photlco'):
    import lsc, os
    from pyraf import iraf
    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    iraf.set(stdimage='imt1024')
    for img in imglist:
        status = checkstage(img, 'wcs')
        if status >= 0:
            photlcodict = lsc.mysqldef.getfromdataraw(conn, database, 'filename', img, '*')
            _dir = photlcodict[0]['filepath']
            diffimg = _dir + img
            origimg = re.sub('\..*diff', '', diffimg)
            tempimg = diffimg.replace('diff', 'ref')
            if os.path.isfile(diffimg) and os.path.isfile(origimg) and os.path.isfile(tempimg):
                print img, photlcodict[0]['filter']
                iraf.display(origimg + '[0]', 1, fill=True, Stdout=1)
                iraf.display(tempimg, 2, fill=True, Stdout=1)
                iraf.display(diffimg, 3, fill=True, Stdout=1)
                ans = raw_input('>>> good difference [[y]/n] or [b]ad quality (original image)? ')
                if ans in ['n', 'N', 'No', 'NO', 'bad', 'b', 'B']:
                    print 'updatestatus bad'
                    print 'rm', diffimg.replace('.fits', '*')
                    os.system('rm ' + diffimg.replace('.fits', '*'))
                    print 'rm', tempimg
                    os.system('rm ' + tempimg)
                    print 'delete', img, 'from database'
                    lsc.mysqldef.deleteredufromarchive(img, 'photlco', 'filename')
                if ans in ['bad', 'b', 'B']:
                    print 'updatestatus bad quality'
                    lsc.mysqldef.updatevalue(database, 'quality', 1, os.path.basename(origimg))
            else:
                for f in [origimg, tempimg, diffimg]:
                    if not os.path.isfile(f): print f, 'not found'
        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        else:
            print 'status ' + str(status) + ': unknown status'

def display_psf_fit(img, datamax=None):
    ggg = lsc.mysqldef.getfromdataraw(conn, 'photlco', 'filename', img, '*')
    ogfile = ggg[0]['filepath'] + img.replace('.fits', '.og.fits')
    rsfile = ggg[0]['filepath'] + img.replace('.fits', '.rs.fits')
    if os.path.isfile(ogfile) and os.path.isfile(rsfile):
        ogdata, hdr = fits.getdata(ogfile, header=True)
        rsdata = fits.getdata(rsfile)
        if datamax is None:
            datamax = lsc.util.readkey3(hdr, 'datamax')
        plt.clf()
        axL = plt.subplot(1, 2, 1, adjustable='box-forced')
        axR = plt.subplot(1, 2, 2, sharex=axL, sharey=axL, adjustable='box-forced')
        vmin = np.percentile(ogdata, 5)
        vmax = np.percentile(ogdata, 95)
        im = axL.imshow(ogdata, vmin=vmin, vmax=vmax)
        axR.imshow(rsdata, vmin=vmin, vmax=vmax)
        j_sat, i_sat = np.where(ogdata > datamax)
        if len(i_sat):
            axL.plot(i_sat, j_sat, 'rx', label='{:d} pixels > {:.0f} ADU'.format(len(i_sat), datamax))
            axL.legend()
        plt.colorbar(im, ax=[axL, axR], orientation='horizontal')
        plt.gcf().text(0.5, 0.99, '{filename}\nfilter = {filter}\nexptime = {exptime:.0f} s\npsfmag = {psfmag:.2f} mag'.format(**ggg[0]), va='top', ha='center')
    return ogfile, rsfile

def checkmag(imglist, datamax=None):
    plt.ion()
    for img in imglist:
        status = checkstage(img, 'checkmag')
        if status > 1:
            ogfile, rsfile = display_psf_fit(img, datamax)
            aa = raw_input('>>>good mag [[y]/n] or [b] bad quality ? ')
            if aa in ['n', 'N', 'No', 'NO', 'bad', 'b', 'B']:
                print 'update status: bad psfmag & mag'
                lsc.mysqldef.updatevalue('photlco', 'psfmag', 9999, img)
                lsc.mysqldef.updatevalue('photlco', 'mag', 9999, img)
                os.system('rm -v ' + ogfile)
                os.system('rm -v ' + rsfile)
            if aa in ['bad', 'b', 'B']:
                print 'update status: bad quality'
                lsc.mysqldef.updatevalue('photlco', 'quality', 1, img)
        elif status == 1:
            print 'status ' + str(status) + ': psfmag stage not done'
        elif status == 0:
            print 'status ' + str(status) + ': WCS stage not done'
        elif status == -1:
            print 'status ' + str(status) + ': sn2.fits file not found'
        elif status == -2:
            print 'status ' + str(status) + ': .fits file not found'
        elif status == -4:
            print 'status ' + str(status) + ': bad quality image'
        else:
            print 'status ' + str(status) + ': unknown status'


def checkpos(imglist, _ra, _dec, database='photlco'):
    import lsc
    import os, string  #,MySQLdb
    #     import  mysqldef #import updatevalue
    imglist2 = []
    for img in imglist:
        status = checkstage(img, 'checkmag')
        if status >= 1:
            ggg = mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
            _dir = ggg[0]['filepath']
            if os.path.isfile(_dir + re.sub('fits', 'sn2.fits', img)):  imglist2.append(
                _dir + re.sub('fits', 'sn2.fits', img))
    print imglist2, _ra, _dec
    ra, dec = lsc.myloopdef.position(imglist2, _ra, _dec, show=True)
    print '######## mean ra and dec position  ############'
    print 'ra= ' + str(ra)
    print 'dec= ' + str(dec)
    print '#############'


def checkquality(imglist, database='photlco'):
    import lsc
    import os, string  #MySQLdb
    #     import  mysqldef #import updatevalue
    direc = lsc.__path__[0]
    from pyraf import iraf

    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    iraf.set(stdimage='imt1024')
    for img in imglist:
        status = checkstage(img, 'checkquality')
        if status == -4:
            ggg = lsc.mysqldef.getfromdataraw(conn, database, 'filename', str(img), '*')
            if not ggg:
                status = -3  # not in the redo table
            else:
                _dir = ggg[0]['filepath']
                if os.path.isfile(_dir + img):
                    iraf.display(_dir + img + '[0]', 1, fill=True, Stdout=1)
                    aa = raw_input('>>>good image [y/[n]] ? ')
                    if not aa: aa = 'n'
                    if aa in ['n', 'N', 'No', 'NO']:
                        print 'status bad'
                    else:
                        print 'updatestatus good'
                        lsc.mysqldef.updatevalue(database, 'quality', 127, string.split(img, '/')[-1])
                        #updatevalue('photlco','psfmag',9999,string.split(img,'/')[-1])
                        #if os.path.isfile(_dir+re.sub('.fits','.psf.fits',img)):
                        #print 'rm '+_dir+re.sub('.fits','.psf.fits',img)
                        #os.system('rm '+_dir+re.sub('.fits','.psf.fits',img))
                        #if os.path.isfile(_dir+re.sub('.fits','.sn2.fits',img)):
                        #print 'rm '+_dir+re.sub('.fits','.sn2.fits',img)
                        #os.system('rm '+_dir+re.sub('.fits','.sn2.fits',img))
                        #else: print 'status: quality good '


##################################################################

def onkeypress2(event):
    import matplotlib.pyplot as plt
    from numpy import argmin, sqrt, mean, array, std, median
    import lsc, os, re

    global idd, _mjd, _mag, _setup, _filename, shift, _database
    xdata, ydata = event.xdata, event.ydata
    dist = sqrt((xdata - _mjd) ** 2 + (ydata - _mag) ** 2)
    ii = argmin(dist)
    if ii in idd: idd.remove(ii)
    print _filename[ii]
    print _mag[ii]
    import os, string  #, MySQLdb,
    #    import  mysqldef #import updatevalue,getvaluefromarchive
    _dir = mysqldef.getvaluefromarchive(_database, 'filename', _filename[ii], 'filepath')
    if 'filepath' in _dir[0]:
        _dir = _dir[0]['filepath']
    else:
        _dir = ''
    if _dir:
        if os.path.isfile(_dir + re.sub('.fits', '.og.fits', _filename[ii])) and os.path.isfile(
                        _dir + re.sub('.fits', '.rs.fits', _filename[ii])):
            from pyraf import iraf

            iraf.digiphot(_doprint=0)
            iraf.daophot(_doprint=0)
            iraf.display(_dir + re.sub('.fits', '.og.fits', _filename[ii]), 1, fill=True, Stdout=1)
            iraf.display(_dir + re.sub('.fits', '.rs.fits', _filename[ii]), 2, fill=True, Stdout=1)
    if event.key in ['d']:
        lsc.mysqldef.updatevalue(_database, 'mag', 9999, _filename[ii])
        lsc.mysqldef.updatevalue(_database, 'psfmag', 9999, _filename[ii])
        lsc.mysqldef.updatevalue(_database, 'apmag', 9999, _filename[ii])
        if _dir:
            lsc.util.updateheader(_dir + re.sub('.fits', '.sn2.fits', _filename[ii]), 0,
                                  {'PSFMAG1': [9999, 'psf magnitude']})
            lsc.util.updateheader(_dir + re.sub('.fits', '.sn2.fits', _filename[ii]), 0,
                                  {'APMAG1': [9999, 'ap magnitude']})
    elif event.key in ['u']:
        lsc.mysqldef.updatevalue(_database, 'magtype', -1, _filename[ii])
        print '\n### set as a limit'
    elif event.key in ['b']:
        lsc.mysqldef.updatevalue(_database, 'quality', 1, _filename[ii])
        print '\n### set bad quality'
    print '\n### press:\n d to cancel value,\n c to check one point\n u to set the upper limit\n b to set bad quality.\n Return to exit ...'

    nonincl = []
    for i in range(len(_mjd)):
        if i not in idd: nonincl.append(i)
    _symbol = 'sdo+34<>^*sdo+34<>^*sdo+34<>^*sdo+34<>^*'
    _color = {'U': 'b', 'B': 'r', 'V': 'g', 'R': 'c', 'I': 'm', 'up': 'b', 'gp': 'r', 'rp': 'g', 'ip': 'c', 'zs': 'm', \
              'Bessell-B': 'r', 'Bessell-V': 'g', 'Bessell-R': 'c', 'Bessell-I': 'm', \
              'SDSS-G': 'r', 'SDSS-R': 'g', 'SDSS-I': 'c', 'Pan-Starrs-Z': 'm'}
    _shift = {'U': -2, 'B': -1, 'V': 0, 'R': 1, 'I': 2, 'up': -2, 'gp': -1, 'rp': 0, 'ip': 1, 'zs': 2, \
              'Bessell-B': -1, 'Bessell-V': 0, 'Bessell-R': 1, 'Bessell-I': 2, \
              'SDSS-G': -1, 'SDSS-R': 0, 'SDSS-I': 1, 'Pan-Starrs-Z': 2}
    ii = 0
    mag, mjd = [], []
    for _tel in _setup:
        shift = 0
        for _fil in _setup[_tel]:
            shift = _shift[_fil]
            col = _color[_fil]
            plt.plot(array(_setup[_tel][_fil]['mjd']), array(_setup[_tel][_fil]['mag']) + shift, _symbol[ii], color=col,
                     markersize=10)
            mag = list(mag) + list(array(_setup[_tel][_fil]['mag']) + shift)
            mjd = list(mjd) + list(_setup[_tel][_fil]['mjd'])
            ii = ii + 1

    plt.xlabel('mjd')
    plt.ylabel('magnitude')
    _mag = mag[:]
    _mjd = mjd[:]
    _mjd = array(_mjd)
    _mag = array(_mag)
    idd = range(len(_mjd))

    yticklabels = plt.getp(plt.gca(), 'yticklabels')
    xticklabels = plt.getp(plt.gca(), 'xticklabels')
    plt.setp(xticklabels, fontsize='10')
    plt.setp(yticklabels, fontsize='10')
    plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0., markerscale=.8, numpoints=1)
    #    plt.legend(numpoints=1,markerscale=.8)
    leg = plt.gca().get_legend()
    ltext = leg.get_texts()
    plt.setp(ltext, fontsize=10)
    plt.plot(_mjd, _mag, 'ok', markersize=1)
    plt.plot(_mjd[nonincl], _mag[nonincl], 'ow')

##################################################################

import matplotlib.pyplot as plt
import numpy as np

class PickablePlot():
    def __init__(self, x, y, mainmenu='', selectedmenu='', hooks={}):
        self.x = x
        self.y = y
        self.selectedmenu = selectedmenu
        self.hooks = hooks
        
        plt.ion()
        fig = plt.figure()
        fig.canvas.mpl_connect('pick_event', self.onclick)
        self.i_active = None
        self.xdel = np.array([])
        self.ydel = np.array([])

        axlims = None
        while True:
            fig.clf()
            hooks['plot']()
            plt.plot(self.x, self.y, 'k,', picker=5)
            plt.plot(self.xdel, self.ydel, 'kx', ms=10)
            if axlims is not None:
                plt.axis(axlims)
            key = raw_input(mainmenu)
            if key in hooks and self.i_active is not None:
                hooks[key](self.i_active)
            if key == '':
                break
            else:
                self.delete_current()
                self.i_active = None
            plt.draw()
            axlims = plt.axis()
        
    def onclick(self, event):
        print # to get off the raw_input line
        self.i_active = event.ind[0]
        if 'click' in self.hooks:
            self.hooks['click'](self.i_active)
        print self.selectedmenu

    def delete_current(self):
        if self.i_active is None:
            print 'no point selected'
        else:
            self.xdel = np.append(self.xdel, self.x[self.i_active])
            self.ydel = np.append(self.ydel, self.y[self.i_active])
            self.x[self.i_active] = np.nan
            self.y[self.i_active] = np.nan

def plotfast2(setup):
    _symbol = 'sdo+34<>^*sdo+34<>^*sdo+34<>^*sdo+34<>^*sdo+34<>^*sdo+34<>^*sdo+34<>^*sdo+34<>^*'
    _color = {'u': '#2c0080', 'g': '#00ccff', 'r': '#ff7d00', 'i': '#90002c', 'z': '#000000',
              'U': '#3c0072', 'B': '#0057ff', 'V': '#79ff00', 'R': '#ff7000', 'I': '#80000d'}
    _shift = {'U': -3, 'B': -2, 'V': -1, 'R': 0, 'I': 1, 'u': -2, 'g': -1, 'r': 0, 'i': 1, 'z': 2}

    filenames = []
    mjds = []
    mags = []
    shifts = []
    for _telescope in setup:
        for _filter in setup[_telescope]:
            filenames += setup[_telescope][_filter]['filename']
            mjds += setup[_telescope][_filter]['mjd']
            mags += setup[_telescope][_filter]['mag']
            shifts += [_shift[lsc.sites.filterst1[_filter]]] * len(setup[_telescope][_filter]['mag'])

    def plot_hook():
        plt.figure(1)
        plt.gca().invert_yaxis()
        plt.xlabel('MJD')
        plt.ylabel('Magnitude')
        for _tel, mark in zip(setup.keys(), _symbol):
            for _fil, data_dict in setup[_tel].items():
                _fil = lsc.sites.filterst1[_fil]
                plt.errorbar(data_dict['mjd'], np.array(data_dict['mag']) + _shift[_fil], data_dict['dmag'],
                            ls='none', color=_color[_fil], marker=mark, label=_tel+' '+_fil+'{:+.0f}'.format(_shift[_fil]))
        plt.legend(loc='best', fontsize='small', numpoints=1)

    def click_hook(i):
        from pyraf import iraf
        print filenames[i], 'selected'
        print 'mjd = {:.2f}\tmag = {:.2f} ({:+d} shift on plot)'.format(mjds[i], mags[i], shifts[i])
        dbrow = mysqldef.getvaluefromarchive('photlco', 'filename', filenames[i], 'filepath, mjd, mag')[0]
        print 'mjd = {:.2f}\tmag = {:.2f} (from database)'.format(dbrow['mjd'], dbrow['mag'])
        plt.figure(2)
        display_psf_fit(filenames[i])

    def delete_hook(i):
        lsc.mysqldef.updatevalue('photlco', 'mag', 9999, filenames[i])
        lsc.mysqldef.updatevalue('photlco', 'psfmag', 9999, filenames[i])
        lsc.mysqldef.updatevalue('photlco', 'apmag', 9999, filenames[i])
        _dir = mysqldef.getvaluefromarchive('photlco', 'filename', filenames[i], 'filepath')[0]['filepath']
        if _dir:
            lsc.util.updateheader(_dir + filenames[i].replace('.fits', '.sn2.fits'), 0,
                                  {'PSFMAG1': [9999, 'psf magnitude'], 'APMAG1': [9999, 'ap magnitude']})
        print 'deleted', filenames[i]

    def bad_hook(i):
        lsc.mysqldef.updatevalue('photlco', 'magtype', -1, filenames[i])
        print 'marked', filenames[i], 'as bad'

    def limit_hook(i):
        lsc.mysqldef.updatevalue('photlco', 'quality', 1, filenames[i])
        print 'changed', filenames[i], 'to upper limit'

    PickablePlot(mjds, np.array(mags) + np.array(shifts),
                mainmenu='Click to select a point. Press return to exit.',
                selectedmenu='Enter d to delete a point, b to mark an image as bad, or u to set a point as an upper limit.',
                hooks={'plot': plot_hook, 'click': click_hook, 'd': delete_hook, 'b': bad_hook, 'u': limit_hook})

##############################################################################
def plotfast(setup, output='', database='photlco'):  #,band,color,fissa=''):
    import matplotlib.pyplot as plt
    from numpy import argmin, sqrt, mean, array, std, median, compress

    global idd, _mjd, _mag, _setup, _filename, shift, _database  #,testo,lines,pol,sss,f,fixcol,sigmaa,sigmab,aa,bb
    if not output:   
        plt.ion()
    plt.rcParams['figure.figsize'] = 9, 5
    fig = plt.figure()
    plt.axes([.15, .05, .65, .85])
    _symbol = 'sdo+34<>^*sdo+34<>^*sdo+34<>^*sdo+34<>^*sdo+34<>^*sdo+34<>^*sdo+34<>^*sdo+34<>^*'
    _color = {'U': 'b', 'B': 'r', 'V': 'g', 'R': 'c', 'I': 'm', 'up': 'b', 'gp': 'r', 'rp': 'g', 'ip': 'c', 'zs': 'm',
              'Bessell-B': 'r', 'Bessell-V': 'g', 'Bessell-R': 'c', 'Bessell-I': 'm',
              'SDSS-G': 'r', 'SDSS-R': 'g', 'SDSS-I': 'c', 'Pan-Starrs-Z': 'm'}
    _shift = {'U': -2, 'B': -1, 'V': 0, 'R': 1, 'I': 2, 'up': -2, 'gp': -1, 'rp': 0, 'ip': 1, 'zs': 2,
              'Bessell-B': -1, 'Bessell-V': 0, 'Bessell-R': 1, 'Bessell-I': 2,
              'SDSS-G': -1, 'SDSS-R': 0, 'SDSS-I': 1, 'Pan-Starrs-Z': 2}
    _setup = setup
    _database = database
    ii = 0
    mag, mjd, filename = [], [], []
    for _tel in _setup:
        shift = 0
        for _fil in _setup[_tel]:
            shift = _shift[_fil]
            col = _color[_fil]
            print _tel, _fil
            jj = array(_setup[_tel][_fil][
                'mjd'])  #compress(array(_setup[_tel][_fil]['magtype'])>=1,array(_setup[_tel][_fil]['jd']))
            mm = array(_setup[_tel][_fil][
                'mag'])  #compress(array(_setup[_tel][_fil]['magtype'])>=1,array(_setup[_tel][_fil]['mag']))
            plt.plot(jj, mm + shift, _symbol[ii], color=col, label=_tel + ' ' + _fil + ' ' + str(shift), markersize=10)

            jj1 = compress(array(_setup[_tel][_fil]['magtype']) < 0, array(_setup[_tel][_fil]['mjd']))
            mm1 = compress(array(_setup[_tel][_fil]['magtype']) < 0, array(_setup[_tel][_fil]['mag']))
            if len(mm1) > 0:
                plt.errorbar(jj1, mm1, mm1 / 100, lolims=True, fmt=None, ecolor='k')

            mag = list(mag) + list(array(_setup[_tel][_fil]['mag']) + _shift[_fil])
            mjd = list(mjd) + list(_setup[_tel][_fil]['mjd'])
            filename = list(filename) + list(_setup[_tel][_fil]['filename'])
            ii = ii + 1

    plt.xlabel('mjd')
    plt.ylabel('magnitude')
    plt.xlim(min(mjd) - 5, max(mjd) + 5)
    plt.ylim(max(mag) + .5, min(mag) - .5)
    yticklabels = plt.getp(plt.gca(), 'yticklabels')
    xticklabels = plt.getp(plt.gca(), 'xticklabels')
    plt.setp(xticklabels, fontsize='10')
    plt.setp(yticklabels, fontsize='10')
    #    plt.legend(numpoints=1,markerscale=.8)
    plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0., markerscale=.8, numpoints=1)
    leg = plt.gca().get_legend()
    ltext = leg.get_texts()
    plt.setp(ltext, fontsize=10)
    _mag = mag[:]
    _mjd = mjd[:]
    _filename = filename[:]
    _mjd = array(_mjd)
    _mag = array(_mag)
    idd = range(len(_mjd))
    plt.plot(_mjd, _mag, 'ok', markersize=1)
    kid = fig.canvas.mpl_connect('key_press_event', onkeypress2)
    #    cid = fig.canvas.mpl_connect('button_press_event',onclick2)
    if not output:
        plt.ion()
        plt.draw()
        raw_input('press d to mark. Return to exit ...\n')
        plt.close()
    else:
        plt.savefig(output.replace('.txt', '.png'), format='png')


################################################################

def subset(xx, _avg=''):  # lista  mjd
    from numpy import array

    diff = [xx[i + 1] - xx[i] for i in range(len(xx) - 1)]
    if _avg:
        avg = float(_avg)
    else:
        avg = sum(diff) / len(diff)
        if avg >= 1:
            avg = .5
        elif avg <= 0.1:
            avg = .5
    i = 1
    subset = {}
    position = {}
    subset[1] = [xx[0]]
    position[1] = [0]
    for j in range(0, len(diff)):
        if diff[j] > avg:   i = i + 1
        if i not in subset:  subset[i] = []
        if i not in position:  position[i] = []
        subset[i].append(xx[j + 1])
        position[i].append(j + 1)
    return subset, position


##########################################################

def chosecolor(allfilter, usegood=False, _field=''):
    color = {filt: [] for filt in allfilter}
    for col in ['UB', 'BV', 'VR', 'RI', 'ug', 'gr', 'ri', 'iz']:
        if col[0] in allfilter and col[1] in allfilter:
            color[col[0]].append(col)
            color[col[1]].append(col)
    if usegood:
        goodcol = {'U': 'UB', 'B': 'BV', 'V': 'VR', 'R': 'VR', 'I': 'RI',
                   'u': 'ug', 'g': 'gr', 'r': 'ri', 'i': 'ri', 'z': 'iz'}
        for filt in color:
            if goodcol[filt] in color[filt]: color[filt] = [goodcol[filt]]
    return color


###########################################################################
def get_list(epoch, _telescope='all', _filter='', _bad='', _name='', _id='', _ra='', _dec='', database='photlco',
             filetype=1):
    from numpy import argsort, take
    import string, re, sys
    import lsc
    #     from lsc.mysqldef import getlistfromraw
    import datetime

    if '-' not in str(epoch):
        epoch0 = re.sub('-', '', str(datetime.date(int(epoch[0:4]), int(epoch[4:6]), int(epoch[6:8]))))
        lista = lsc.mysqldef.getlistfromraw(lsc.myloopdef.conn, database, 'dayobs', str(epoch0), '', '*', _telescope)
    else:
        epoch1, epoch2 = string.split(epoch, '-')
        start = re.sub('-', '', str(datetime.date(int(epoch1[0:4]), int(epoch1[4:6]), int(epoch1[6:8]))))
        stop = re.sub('-', '', str(datetime.date(int(epoch2[0:4]), int(epoch2[4:6]), int(epoch2[6:8]))))
        lista = lsc.mysqldef.getlistfromraw(lsc.myloopdef.conn, database, 'dayobs', str(start), str(stop), '*',
                                            _telescope)
    if lista:
        ll0 = {}
        for jj in lista[0].keys(): ll0[jj] = []
        for i in range(0, len(lista)):
            for jj in lista[0].keys(): ll0[jj].append(lista[i][jj])

        inds = argsort(ll0['mjd'])  #  sort by mjd
        for i in ll0.keys():
            ll0[i] = take(ll0[i], inds)

        ll0['ra'] = []
        ll0['dec'] = []
        if 'ra0' not in ll0.keys():
            for i in ll0['filename']:
                print i
                ggg = lsc.mysqldef.getfromdataraw(lsc.myloopdef.conn, 'photlcoraw', 'filename', i, '*')
                ll0['ra'].append(ggg[0]['ra0'])
                ll0['dec'].append(ggg[0]['dec0'])
        else:
            ll0['ra'] = ll0['ra0']
            ll0['dec'] = ll0['dec0']
        ll = lsc.myloopdef.filtralist(ll0, _filter, _id, _name, _ra, _dec, _bad)
    else:
        ll = ''
    return ll


######

def check_missing(lista, database='photlco'):
    import mysqldef  #import getlistfromraw,getfromdataraw
    from numpy import argsort, take
    import string, re, sys, os
    import lsc
    import datetime

    if len(lista) > 0:
        for i in lista:
            xx = mysqldef.getfromdataraw(lsc.myloopdef.conn, 'photlcoraw', 'filename', str(i), column2='filepath')
            yy = mysqldef.getfromdataraw(lsc.myloopdef.conn, database, 'filename', str(i), column2='filepath')
            xx, yy = xx[0]['filepath'], yy[0]['filepath']
            if not os.path.isfile(yy + i):
                os.system('cp ' + xx + i + ' ' + yy + i)
                print xx, str(i), yy + i


def checkfilevsdatabase(lista, database='photlco'):
    #     import  mysqldef #import getlistfromraw,getfromdataraw
    import lsc
    import os, string, re, sys

    if lista:
        if len(lista['filename']) > 0:
            for i in range(0, len(lista['filename'])):
                imgsn = re.sub('.fits', '.sn2.fits', lista['filepath'][i] + lista['filename'][i])
                if os.path.isfile(imgsn):
                    hdr1 = lsc.util.readhdr(imgsn)
                    _filter = lsc.util.readkey3(hdr1, 'filter')
                    _exptime = lsc.util.readkey3(hdr1, 'exptime')
                    _airmass = lsc.util.readkey3(hdr1, 'airmass')
                    _telescope = lsc.util.readkey3(hdr1, 'telescop')
                    _psfmag = lsc.util.readkey3(hdr1, 'PSFMAG1')
                    _psfdmag1 = lsc.util.readkey3(hdr1, 'PSFDMAG1')
                    _apmag = lsc.util.readkey3(hdr1, 'APMAG1')
                    _mag = lsc.util.readkey3(hdr1, 'MAG')
                    if not _mag:  #  mag
                        if lista['mag'][i] != 9999.0:
                            print lista['filename'][i], _mag, lista['mag'][i], 'mag'
                            lsc.mysqldef.updatevalue(database, 'mag', 9999.0, lista['filename'][i])
                    else:
                        if _mag == 9999.0:
                            if lista['mag'][i] != 9999.0:
                                print lista['filename'][i], _mag, lista['mag'][i], 'mag'
                                lsc.mysqldef.updatevalue(database, 'mag', 9999.0, lista['filename'][i])
                        elif _mag != 9999.0:
                            if round(lista['mag'][i], 4) != round(float(_mag), 4):
                                print lista['filename'][i], _mag, lista['mag'][i], 'mag'
                                lsc.mysqldef.updatevalue(database, 'mag', _mag, lista['filename'][i])

                    if not _psfmag:  #  psfmag
                        if lista['psfmag'][i] != 9999.0:
                            print lista['filename'][i], _mag, lista['psfmag'][i], 'psfmag'
                            lsc.mysqldef.updatevalue(database, 'psfmag', 9999.0, lista['filename'][i])
                    else:
                        if _psfmag == 9999.0:
                            if lista['psfmag'][i] != 9999.0:
                                print lista['filename'][i], _psfmag, lista['psfmag'][i], 'psfmag'
                                lsc.mysqldef.updatevalue(database, 'psfmag', 9999.0, lista['filename'][i])
                        elif _psfmag != 9999.0:
                            if round(lista['psfmag'][i], 4) != round(float(_psfmag), 4):
                                print lista['filename'][i], _psfmag, lista['psfmag'][i], 'psfmag'
                                lsc.mysqldef.updatevalue(database, 'psfmag', _psfmag, lista['filename'][i])

                    if not _apmag:  #  apmag
                        if lista['mag'][i] != 9999.0:
                            print lista['filename'][i], _mag, lista['mag'][i], 'apmag'
                            lsc.mysqldef.updatevalue(database, 'apmag', 9999.0, lista['filename'][i])
                    else:
                        if _apmag == 9999.0:
                            if lista['apmag'][i] != 9999.0:
                                print lista['filename'][i], _apmag, lista['apmag'][i], 'apmag'
                                lsc.mysqldef.updatevalue(database, 'apmag', 9999.0, lista['filename'][i])
                        elif _apmag != 9999.0:
                            if round(lista['apmag'][i], 4) != round(float(_apmag), 4):
                                print lista['filename'][i], _apmag, lista['apmag'][i], 'apmag'
                                lsc.mysqldef.updatevalue(database, 'apmag', _apmag, lista['filename'][i])


#########################################################################################
def run_merge(imglist, _redu=False):
    import lsc

    direc = lsc.__path__[0]
    from numpy import where, array
    import mysqldef
    import os, string, glob  #, MySQLdb,

    status = []
    stat = 'psf'
    for img in imglist:
        status.append(checkstage(string.split(img, '/')[-1], stat))
    print imglist
    print status
    imglist = imglist[where(array(status) > 0)]
    status = array(status)[where(array(status) > 0)]

    f = open('_tmp.list', 'w')
    for jj in range(0, len(imglist)):
        f.write(imglist[jj] + '\n')
    f.close()
    if _redu:
        ii = ' -f '
    else:
        ii = ''
    #     if _fix: ff=' -c '
    #     else:    ff=''
    #     tt=' -t '+_type+' '
    command = 'lscmerge.py _tmp.list ' + ii  #+tt+ff
    print command
    os.system(command)

########################################################################################

def run_ingestsloan(imglist,imgtype = 'sloan', ps1frames='', show=False, force=False):
    command = 'lscingestsloan.py ' + ' '.join(imglist)
    if imgtype != 'sloan':
        command += ' --type ' + imgtype
    if ps1frames:
        command += ' --ps1frames ' + ps1frames
    if show:
        command += ' --show'
    if force:
        command += ' -F'
    print command
    os.system(command)

#####################################################################
def run_diff(listtar, listtemp, _show=False, _force=False, _normalize='i', _convolve='', _bgo=3, _fixpix=False, _difftype='0', suffix='.diff.fits'):
    import lsc

    direc = lsc.__path__[0]
    from numpy import where, array
    import mysqldef
    import os, string, glob

    status = []
    stat = 'psf'
    for img in listtar:
        status.append(checkstage(string.split(img, '/')[-1], stat))
    listtar = listtar[where(array(status) > 0)]
    status = array(status)[where(array(status) > 0)]

    f = open('_tar.list', 'w')
    for jj in range(0, len(listtar)):
        f.write(listtar[jj] + '\n')
    f.close()
    f = open('_temp.list', 'w')
    for jj in range(0, len(listtemp)):
        f.write(listtemp[jj] + '\n')
    f.close()
    if _show:
        ii = ' --show '
    else:
        ii = ''
    if _force:
        ff = ' -f '
    else:
        ff = ' '

    if _convolve:
        _convolve = ' --convolve '+_convolve+' '
    else:
        _convolve=''
    if _bgo:
        _bgo=' --bgo '+str(_bgo)
    else:
        _bgo=''
    if _fixpix:
        fixpix = ' --fixpix '
    else:
        fixpix = ''
    command = 'lscdiff.py _tar.list _temp.list ' + ii + ff + '--normalize ' + _normalize+_convolve+_bgo + fixpix + ' --difftype ' + _difftype + ' --suffix ' + suffix
    print command
    os.system(command)


######################################################################3

def run_template(listtemp, show=False, _force=False, _interactive=False, _ra=None, _dec=None, _psf=None, _mag=0, _clean=True, _subtract_mag_from_header=False):
    import lsc

    direc = lsc.__path__[0]
    from numpy import where, array
    import mysqldef
    import os, string, glob

    status = []
    stat = 'psf'
    for img in listtemp:  status.append(checkstage(string.split(img, '/')[-1], stat))
    listtemp = listtemp[where(array(status) > 0)]
    status = array(status)[where(array(status) > 0)]

    f = open('_temp.list', 'w')
    for jj in range(0, len(listtemp)):
        f.write(listtemp[jj] + '\n')
    f.close()
    command = 'lscmaketempl.py _temp.list'
    if show:
        command += ' --show'
    if _force:
        command += ' -f'
    if _interactive:
        command += ' -i'
    if _ra:
        command += ' -R ' + str(_ra)
    if _dec:
        command += ' -D ' + str(_dec)
    if _psf:
        command += ' -p ' + _psf
    if _mag:
        command += ' --mag ' + str(_mag)
    if not _clean:
        command += ' --uncleaned'
    if _subtract_mag_from_header:
        command += ' --subtract-mag-from-header'
    print command
    os.system(command)


#####################################################################
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


###################################################################

def run_cosmic(imglist, database='photlco', _sigclip=4.5, _sigfrac=0.2, _objlim=4, _force=False):
    import lsc
    direc = lsc.__path__[0]
    import os, string, glob
########  SV 20161129  add multiprocess
    for ggg in imglist:
            _dir,img = os.path.split(ggg)
            if _dir:
                _dir = _dir+'/'
            print _dir + img
            if os.path.isfile(_dir + img):
                if os.path.isfile(_dir + re.sub('.fits', '.var.fits', img)):
                    print 'variance image found'
                    os.system('cp '+_dir + img+' '+_dir + re.sub('.fits', '.clean.fits',img))
                    ar, hd = fits.getdata(_dir + img, header=True)
                    out_fits = fits.PrimaryHDU(header=hd,data=(ar-ar).astype('uint8'))
                    out_fits.writeto(re.sub('.fits', '.mask.fits', _dir + img), overwrite=True, output_verify='fix')
                else:
                    if not os.path.isfile(_dir + img.replace('.fits', '.clean.fits')) or not os.path.isfile(_dir + img.replace('.fits', '.mask.fits')) or _force:
                        output, mask, satu = lsc.util.Docosmic(_dir + img, _sigclip, _sigfrac, _objlim)
                        lsc.util.updateheader(output, 0, {'DOCOSMIC': [True, 'Cosmic rejection using LACosmic']})
                        print 'mv ' + output + ' ' + _dir
                        os.system('mv ' + output + ' ' + _dir)
                        os.system('mv ' + mask + ' ' + _dir)
                        os.system('mv ' + satu + ' ' + _dir)
                        print output, mask, satu
                    else:
                        print 'cosmic rejection already done'
            else:
                print img, ' not found'


###################################################################

def run_apmag(imglist, database='photlco'):
    import lsc

    direc = lsc.__path__[0]
    import os, string, glob

    for img in imglist:
        ggg = lsc.mysqldef.getfromdataraw(lsc.conn, database, 'filename', str(img), '*')
        if ggg:
            _dir = ggg[0]['filepath']
            img1 = re.sub('.fits', '.sn2.fits', img)
            print _dir + img1
            if os.path.isfile(_dir + img1):
                command = 'lscnewcalib.py ' + _dir + img1
                print command
                os.system(command)
            else:
                print img1, ' not found'

###################################################################

