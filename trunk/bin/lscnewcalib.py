#!/usr/bin/env python
description = ">> new calibration"
usage = "%prog image [options] "

import os
import string
import re
import sys
import glob
from optparse import OptionParser
import time
import lsc
from astropy.io import fits
import numpy as np


def vizq(_ra, _dec, catalogue, radius):
    ''' Query vizquery '''
    import os, string, re

    _site = 'vizier.cfa.harvard.edu'
    # _site='vizier.u-strasbg.fr'
    cat = {'usnoa2': ['I/252/out', 'USNO-A2.0', 'Rmag'], '2mass': ['II/246/out', '2MASS', 'Jmag'],
           'landolt': ['II/183A/table2', '', 'Vmag,B-V,U-B,V-R,R-I,Star,e_Vmag'],
           'apass': ['I/322A/out', '', 'Bmag,Vmag,gmag,rmag,imag,e_Vmag,e_Bmag,e_gmag,e_rmag,e_imag,UCAC4'],
           'usnob1': ['I/284/out', 'USNO-B1.0', 'R2mag'],
           'sdss7': ['II/294/sdss7', '', 'objID,umag,gmag,rmag,imag,zmag,gc'],
           'sdss9': ['V/139/sdss9', '', 'objID,umag,gmag,rmag,imag,zmag,e_umag,e_gmag,e_rmag,e_imag,e_zmag,gc'],
           'sdss7': ['II/294/sdss7', '', 'objID,umag,gmag,rmag,imag,zmag,e_umag,e_gmag,e_rmag,e_imag,e_zmag,gc'],
           'sdss8': ['II/306/sdss8', '', 'objID,umag,gmag,rmag,imag,zmag,e_umag,e_gmag,e_rmag,e_imag,e_zmag,gc']}

    a = os.popen('vizquery -mime=tsv  -site=' + _site + ' -source=' + cat[catalogue][0] + \
                 ' -c.ra=' + str(_ra) + ' -c.dec=' + str(_dec) + ' -c.eq=J2000 -c.rm=' + str(radius) + \
                 ' -c.geom=b -oc.form=h -sort=_RA*-c.eq -out.add=_RAJ2000,_DEJ2000 -out.max=10000 -out=' + \
                 cat[catalogue][1] + ' -out=' + cat[catalogue][2] + '').read()
    print 'vizquery -mime=tsv  -site=' + _site + ' -source=' + cat[catalogue][0] + \
          ' -c.ra=' + str(_ra) + ' -c.dec=' + str(_dec) + ' -c.eq=J2000 -c.rm=' + str(radius) + \
          ' -c.geom=b -oc.form=h -sort=_RA*-c.eq -out.add=_RAJ2000,_DEJ2000 -out.max=10000 -out=' + \
          cat[catalogue][1] + ' -out=' + cat[catalogue][2] + ''
    aa = a.split('\n')
    bb = []
    for i in aa:
        if i and i[0] != '#':   bb.append(i)
    _ra, _dec, _name, _mag = [], [], [], []
    for ii in bb[3:]:
        aa = ii.split('\t')
        rr, dd = lsc.lscabsphotdef.deg2HMS(ra=re.sub(' ', ':', aa[0]), dec=re.sub(' ', ':', aa[1]), round=False)
        _ra.append(rr)
        _dec.append(dd)
        _name.append(aa[2])
    dictionary = {'ra': _ra, 'dec': _dec, 'id': _name}
    sss = string.split(cat[catalogue][2], ',')
    for ii in sss: dictionary[ii] = []
    for ii in bb[3:]:
        aa = ii.split('\t')
        for gg in range(0, len(sss)):
            if sss[gg] not in ['UCAC4', 'id']:
                try:
                    dictionary[sss[gg]].append(float(aa[2 + gg]))
                except:
                    dictionary[sss[gg]].append(float(9999))
            else:
                dictionary[sss[gg]].append(str(aa[2 + gg]))

    if catalogue in ['sdss7', 'sdss9', 'sdss8']:
        dictionary['u'] = dictionary['umag']
        dictionary['g'] = dictionary['gmag']
        dictionary['r'] = dictionary['rmag']
        dictionary['i'] = dictionary['imag']
        dictionary['z'] = dictionary['zmag']
        dictionary['uerr'] = dictionary['e_umag']
        dictionary['gerr'] = dictionary['e_gmag']
        dictionary['rerr'] = dictionary['e_rmag']
        dictionary['ierr'] = dictionary['e_imag']
        dictionary['zerr'] = dictionary['e_zmag']
        for key in dictionary.keys():
            if key != 'r':
                dictionary[key] = \
                    np.compress((np.array(dictionary['r']) < 19) & (np.array(dictionary['r'] > 10)), dictionary[key])
        dictionary['r'] = np.compress((np.array(dictionary['r']) < 19) & (np.array(dictionary['r'] > 10)),
                                      dictionary['r'])

    elif catalogue == 'landolt':
        dictionary['B'] = np.array(dictionary['Vmag']) + np.array(dictionary['B-V'])
        dictionary['U'] = np.array(dictionary['B']) + np.array(dictionary['U-B'])
        dictionary['V'] = np.array(dictionary['Vmag'])
        dictionary['Verr'] = np.array(dictionary['e_Vmag'])
        dictionary['R'] = np.array(dictionary['Vmag']) - np.array(dictionary['V-R'])
        dictionary['I'] = np.array(dictionary['R']) - np.array(dictionary['R-I'])
        dictionary['id'] = np.array(dictionary['Star'])
    elif catalogue == 'apass':
        dictionary['B'] = np.array(dictionary['Bmag'])
        dictionary['V'] = np.array(dictionary['Vmag'])
        dictionary['g'] = np.array(dictionary['gmag'])
        dictionary['r'] = np.array(dictionary['rmag'])
        dictionary['i'] = np.array(dictionary['imag'])
        dictionary['Berr'] = np.array(dictionary['e_Bmag'], float) / 100.
        dictionary['Verr'] = np.array(dictionary['e_Vmag'], float) / 100.
        dictionary['gerr'] = np.array(dictionary['e_gmag'], float) / 100.
        dictionary['rerr'] = np.array(dictionary['e_rmag'], float) / 100.
        dictionary['ierr'] = np.array(dictionary['e_imag'], float) / 100.
        dictionary['id'] = np.array(dictionary['UCAC4'], str)
        for key in dictionary.keys():
            if key != 'r':
                dictionary[key] = \
                    np.compress((np.array(dictionary['r']) < 22) & (np.array(dictionary['r'] > 10.5)), dictionary[key])
        dictionary['r'] = np.compress((np.array(dictionary['r']) < 22) & (np.array(dictionary['r'] > 10.5)),
                                      dictionary['r'])
    return dictionary


# #######################################################################
def crossmatch(_ra0, _dec0, _ra1, _dec1, tollerance):  # degree,degree,degree,degree,arcsec
    scal = np.pi / 180.
    distvec = []
    pos0 = []
    pos1 = []
    i = 0
    _ra0, _dec0, _ra1, _dec1 = np.array(_ra0, float), np.array(_dec0, float), np.array(_ra1, float), np.array(_dec1,
                                                                                                              float)
    for jj in range(0, len(_ra0)):
        try:
            distance = np.arccos(np.array(np.sin(np.array(_dec1, np.float64) * scal) * np.sin(_dec0[jj] * scal)) + \
                                 np.array(np.cos(np.array(_dec1, np.float64) * scal) * np.cos(_dec0[jj] * scal) *
                                          np.cos((np.array(_ra1, np.float64) - _ra0[jj]) * scal)))
            if np.min(distance) <= tollerance * np.pi / (180 * 3600):
                distvec.append(np.min(distance))
                pos0.append(jj)
                pos1.append(np.argmin(distance))
        except:
            pass
    return distvec, pos0, pos1  #

# #######################################################################

if __name__ == "__main__":
    start_time = time.time()
    parser = OptionParser(usage=usage, description=description)
    option, args = parser.parse_args()
    if len(args) < 1: sys.argv.append('--help')
    option, args = parser.parse_args()
    imglist = lsc.util.readlist(args[0])
    for img in imglist:
        print img
        table = lsc.lscabsphotdef.makecatalogue([img])
        _filter = table.keys()[0]
        _rasex = table[table.keys()[0]][table[table.keys()[0]].keys()[0]]['ra0']
        _decsex = table[table.keys()[0]][table[table.keys()[0]].keys()[0]]['dec0']
        _magp3 = table[table.keys()[0]][table[table.keys()[0]].keys()[0]]['magp3']
        _merrp3 = table[table.keys()[0]][table[table.keys()[0]].keys()[0]]['merrp3']
        #    _magp2=table[table.keys()[0]][table[table.keys()[0]].keys()[0]]['magp2']
        #    _magp3=table[table.keys()[0]][table[table.keys()[0]].keys()[0]]['magp3']
        #    _merrp2=table[table.keys()[0]][table[table.keys()[0]].keys()[0]]['merrp2']
        #    _merrp3=table[table.keys()[0]][table[table.keys()[0]].keys()[0]]['merrp3']
        hdr = fits.open(img)[0].header
        _ra0 = hdr['RA']
        _dec0 = hdr['DEC']

        _exptime = hdr['exptime']
        _object = lsc.util.readkey3(hdr, 'object')

        mag = _magp3
        magerr = _merrp3
        _filter = re.sub('p', '', _filter)
        _filter = re.sub('s', '', _filter)

        _cat = ''
        if _filter in ['u', 'g', 'r', 'i', 'z']:
            _catalogue = glob.glob(lsc.__path__[0] + '/standard/cat/sloan/' + _object + '*')
            if _catalogue:
                _sloan = lsc.lscastrodef.readtxt(_catalogue[0])
                for _id in _sloan:
                    try:
                        _sloan[_id] = np.array(_sloan[_id], float)
                    except:
                        pass

                print 'use catalogue from archive for object ' + str(_object)
            else:
                _sloan = ''
            if not _sloan:
                _sloan = vizq(_ra0, _dec0, 'sdss7', 20)

            if _sloan:
                _cat = _sloan
            else:
                if _filter in ['g', 'r', 'i']:
                    _apass = vizq(_ra0, _dec0, 'apass', 20)
                    if _apass:   _cat = _apass
        elif _filter in ['U', 'B', 'V', 'R', 'I']:
            _catalogue = glob.glob(lsc.__path__[0] + '/standard/cat/landolt/' + _object + '*')
            if _catalogue:
                _landolt = lsc.lscastrodef.readtxt(_catalogue[0])
                print 'use catalogue from archive for object ' + str(_object)
                for _id in _landolt:
                    try:
                        _landolt[_id] = np.array(_landolt[_id], float)
                    except:
                        pass

            else:
                _landolt = ''
            if not _landolt:
                if _filter in ['B', 'V']:
                    _landolt = vizq(_ra0, _dec0, 'apass', 20)
            if _landolt:   _cat = _landolt

        if _cat:
            distvec, pos0, pos1 = crossmatch(_rasex, _decsex, _cat['ra'], _cat['dec'], 5)
        else:
            pos0 = []

        if len(pos0) >= 3:
            xx = np.compress((np.array(_cat[_filter])[pos1] <= 99) & ((np.array(mag[pos0])) <= 99),
                             np.array(_cat[_filter])[pos1])
            yy = np.compress((np.array(_cat[_filter])[pos1] <= 99) & ((np.array(mag[pos0])) <= 99), np.array(mag[pos0]))
            yyerr = np.compress((np.array(_cat[_filter])[pos1] <= 99) & ((np.array(mag[pos0])) <= 99),
                                np.array(magerr[pos0]))
            xxerr = np.compress((np.array(_cat[_filter])[pos1] <= 99) & ((np.array(mag[pos0])) <= 99),
                                np.array(_cat[_filter + 'err'])[pos1])

            ZZ = np.array(xx - yy)
            data2, std2, ZZ0 = lsc.lscabsphotdef.zeronew(ZZ, maxiter=10, nn=2, verbose=True, show=False)
            lsc.mysqldef.updatevalue('photlco', 'zn', float(ZZ0), string.split(re.sub('sn2.', '', img), '/')[-1])
            lsc.mysqldef.updatevalue('photlco', 'dzn', float(std2), string.split(re.sub('sn2.', '', img), '/')[-1])
            lsc.mysqldef.updatevalue('photlco', 'znnum', len(data2), string.split(re.sub('sn2.', '', img), '/')[-1])
            headers = {'zn': [float(ZZ0), 'zeropoint'], 'dzn': [float(std2), 'zeropoint std'],
                       'znnum': [len(data2), 'number of stars used for zeropoint']}
            lsc.util.updateheader(img, 0, headers)
            print 'zero point ', ZZ0
            from pyraf import iraf

            iraf.astcat(_doprint=0)
            iraf.imcoords(_doprint=0)
            iraf.digiphot(_doprint=0)
            iraf.daophot(_doprint=0)
            from iraf import digiphot
            from iraf import daophot
            from iraf import ptools

            targ = lsc.mysqldef.targimg(img)
            aa = lsc.mysqldef.query(['select ra0,dec0 from targets where id="' + str(targ) + '"'], lsc.conn)
            if len(aa) > 0:
                rasn = aa[0]['ra0']
                decsn = aa[0]['dec0']
                lll = [str(rasn) + '    ' + str(decsn)]
                sss = iraf.wcsctran('STDIN', 'STDOUT', img + '[0]', Stdin=lll, inwcs='world', units='degrees degrees',
                                    outwcs='logical', columns='1 2', formats='%10.1f %10.1f', Stdout=1)
                f = open('_coord', 'w')
                f.write(sss[-1])
                f.close()
                _gain = lsc.util.readkey3(hdr, 'gain')
                _ron = lsc.util.readkey3(hdr, 'ron')
                _exptime = lsc.util.readkey3(hdr, 'exptime')
                _pixelscale = lsc.util.readkey3(hdr, 'PIXSCALE')
                _datamin = lsc.util.readkey3(hdr, 'datamin')
                _datamax = lsc.util.readkey3(hdr, 'datamax')

                a1, a2, a3, a4, = float(5. / _pixelscale), float(8. / _pixelscale), float(10. / _pixelscale), float(
                    20. / _pixelscale)
                ap = str(a1) + "," + str(a2) + "," + str(a3)
                iraf.noao.digiphot.daophot.photpars.zmag = 0
                iraf.noao.digiphot.daophot.datapars.readnoi = _gain  #1.4   #_ron
                iraf.noao.digiphot.daophot.datapars.epadu = _ron  #  13      #_gain
                iraf.noao.digiphot.daophot.datapars.datamin = _datamin
                iraf.noao.digiphot.daophot.datapars.datamax = _datamax
                iraf.noao.daophot.fitskypars.salgori = 'centroid'  # 'median', default is 'mode'
                iraf.noao.daophot.fitskypars.annulus = a3
                iraf.noao.daophot.fitskypars.dannulus = a4
                iraf.noao.daophot.photpars.apertures = ap
                iraf.noao.digiphot.daophot.datapars.exposure = 'exptime'
                iraf.noao.digiphot.daophot.datapars.airmass = 'airmass'
                iraf.noao.digiphot.daophot.datapars.filter = 'filter2'
                iraf.noao.digiphot.daophot.daopars.psfrad = a3
                iraf.noao.digiphot.daophot.daopars.fitrad = a1
                iraf.noao.digiphot.daophot.daopars.sannulus = int(a3)
                iraf.noao.digiphot.daophot.daopars.wsannul = int(a4)
                iraf.noao.digiphot.daophot.daopars.recenter = 'no'
                iraf.noao.digiphot.daophot.daopars.fitsky = 'yes'
                iraf.noao.digiphot.daophot.centerpars.cbox = 1
                iraf.noao.digiphot.daophot.centerpars.calgori = 'gauss'
                ####################################################
                #                    this is in the case we want to measure magnitudes on images cleaned from cosmic
                ####################################################
                #            if os.path.isfile(re.sub('sn2.','clean.',img)):
                #                print 'compute aperture mag on clean image'
                #                aaa=iraf.noao.digiphot.daophot.phot(re.sub('sn2.','clean.',img),'_coord','STDOUT',veri='no',verbose='no',Stdout=1)
                #            else:
                #                aaa=iraf.noao.digiphot.daophot.phot(re.sub('sn2.','',img),'_coord','STDOUT',veri='no',verbose='no',Stdout=1)
                ####################################################
                aaa = iraf.noao.digiphot.daophot.phot(re.sub('sn2.', '', img), '_coord', 'STDOUT', veri='no',
                                                      verbose='no', Stdout=1)

                #            for ii in aaa: print ii

                epadu = float(string.split([i for i in aaa if 'EPADU' in i][0])[3])
                aaa = [i for i in aaa if i[0] != '#']
                rad3, sum3, area3, flux3, mag3, dmag3 = string.split(aaa[-1])[0:6]
                rad2, sum2, area2, flux2, mag2, dmag2 = string.split(aaa[-2])[0:6]
                rad1, sum1, area1, flux1, mag1, dmag1 = string.split(aaa[-3])[0:6]
                MSKY, STDEV, SSKEW, NSKY, NSREJ, SIER, SERROR, _ = string.split(aaa[2])
                error1 = np.sqrt(float(flux1) / float(epadu) + float(area1) * (float(STDEV) ** 2) +
                                 (float(area1) ** 2) * float(STDEV) ** 2 / float(NSKY))

                #################################################################################
                ###  this should be revisited depending if we calibrate to target or reference
                ################################################################################
                if 'diff' in img:
                    if 'apfl1re' in hdr and 'dapfl1re' in hdr:
                        print 'zeropoint there'
                        FLUXref = hdr['apfl1re']
                        dFLUXref = hdr['dapfl1re']
                    else:
                        FLUXref = ''
                    if 'ZNref' in hdr:
                        print 'flux there'
                        ZZ0ref = hdr['ZNref']
                    else:
                        ZZ0ref = ''
                    if FLUXref and ZZ0ref:
                        print FLUXref, dFLUXref, flux1, error1
                        if float(ZZ0ref) == float(ZZ0):
                            print 'difference image scaled to the reference, zero point of the difference image is the same'
                            magfromflux = -2.5 * np.log10((float(FLUXref)) + (float(flux1) / _exptime))
                            dmagfromflux = 1.0857 * np.sqrt((error1 / _exptime) ** 2 + (float(dFLUXref)) ** 2) / (
                                (float(flux1) / _exptime) + float(FLUXref))
                        else:
                            magfromflux = -2.5 * np.log10((float(FLUXref)) * 10 ** ((float(ZZ0ref) - ZZ0) / -2.5) +
                                                          (float(flux1) / _exptime))
                            dmagfromflux = 1.0857 * np.sqrt((error1 / _exptime) ** 2 + (float(dFLUXref)) ** 2) / (
                                (float(flux1) / _exptime) + float(FLUXref))
                            print  'this is a difference image\n I found a zeropoint and flux measurment in the reference image'
                            print  "I'm going to replace tha magnitude at aperture 3 with this value"
                        mag1 = magfromflux
                        dmag1 = dmagfromflux
                        print mag1, dmag1
                    else:
                        print 'Warning: this is a difference image, but I did not find a flux and zeropoint\n'
                        print 'for the reference image, the reference image does not include the target we are measuring'
                        ##################################################################################

                lsc.mysqldef.updatevalue('photlco', 'apflux', float(flux1) / _exptime,
                                         string.split(re.sub('sn2.', '', img), '/')[-1])
                lsc.mysqldef.updatevalue('photlco', 'dapflux', float(error1) / _exptime,
                                         string.split(re.sub('sn2.', '', img), '/')[-1])

                if mag1 != 'INDEF':
                    print float(mag1)
                    try:
                        lsc.mysqldef.updatevalue('photlco', 'apmag', float(mag1),
                                                 string.split(re.sub('sn2.', '', img), '/')[-1])
                        lsc.mysqldef.updatevalue('photlco', 'dapmag', float(dmag1),
                                                 string.split(re.sub('sn2.', '', img), '/')[-1])
                    except:
                        pass

            headers = {'apflux': [float(flux1) / _exptime, ''], 'dapflux': [float(error1) / _exptime, '']}
            lsc.util.updateheader(img, 0, headers)
