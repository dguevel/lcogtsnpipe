#!/usr/bin/env python
description = ">> make catalogue from table"
usage = "%prog image [options] "

import os
import string
import re
import sys
from optparse import OptionParser
import time
import lsc
from lsc.sites import filterst1
import numpy as np

if __name__ == "__main__":
    start_time = time.time()
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-i", "--interactive", action="store_true", dest='interactive', default=False, \
                      help='Interactive \t\t\t [%default]')
    parser.add_option("-e", "--exzp", dest="exzp", default='',
                      type='str', help='external zero point from different field \t\t %default')
    parser.add_option("-c", "--color", action="store_true", dest='color', default=False, \
                      help='use specific color \t\t\t [%default]')
    parser.add_option("-t", "--typemag", dest="typemag", default='fit',
                      type='str', help='type of magnitude fit,ph \t\t %default')

    option, args = parser.parse_args()
    if len(args) < 1:
        sys.argv.append('--help')
    _typemag = option.typemag
    if _typemag not in ['fit', 'ph']:
        sys.argv.append('--help')
    option, args = parser.parse_args()
    imglist = args[0]
    lista = lsc.util.readlist(imglist)
    hdr = lsc.util.readhdr(lista[0])
    tel = lsc.util.readkey3(hdr, 'telescop')
    _exzp = option.exzp
    _interactive = option.interactive
    _color = option.color
    dicti = lsc.lscabsphotdef.makecatalogue(lista)
    namemag = {'fit': ['smagf', 'smagerrf'], 'ph': ['magp3', 'merrp3']}
    allfilters = ''
    for fil in dicti:
        allfilters += filterst1[fil]
    queste0 = lsc.myloopdef.chosecolor(allfilters, False)
    queste1 = lsc.myloopdef.chosecolor(allfilters, True)

    if _exzp: # copy all the zero points from the standards to the science images (in headers & database)
        lista2 = lsc.util.readlist(_exzp)
        dicti2 = lsc.lscabsphotdef.makecatalogue(lista2)
        for _filter2 in dicti2:
            img2 = dicti2[_filter2].keys()[0]
            for jj in dicti2[_filter2][img2].keys():
                if 'ZP' in jj:
                    if _filter2 in dicti:
                        for img in dicti[_filter2].keys():
                            dicti[_filter2][img][jj] = dicti2[_filter2][img2][jj]
                            lsc.util.updateheader(img, 0, {jj: [dicti2[_filter2][img2][jj], 'a b sa sb in y=a+bx']})
                            lsc.util.updateheader(img, 0, {'CATALOG': [str(img2), 'catalogue source']})
                            mm = jj[2:]
                            result = string.split(dicti2[_filter2][img2][jj])
                            if mm[0] == mm[2]:
                                num = 2
                            elif mm[0] == mm[1]:
                                num = 1
                            lsc.mysqldef.updatevalue('photlco', 'zcol' + str(num), mm[1:],
                                                     string.split(re.sub('sn2.fits', 'fits', img), '/')[-1])
                            lsc.mysqldef.updatevalue('photlco', 'z' + str(num), result[1],
                                                     string.split(re.sub('sn2.fits', 'fits', img), '/')[-1])
                            lsc.mysqldef.updatevalue('photlco', 'c' + str(num), result[2],
                                                     string.split(re.sub('sn2.fits', 'fits', img), '/')[-1])
                            lsc.mysqldef.updatevalue('photlco', 'dz' + str(num), result[3],
                                                     string.split(re.sub('sn2.fits', 'fits', img), '/')[-1])
                            lsc.mysqldef.updatevalue('photlco', 'dc' + str(num), result[4],
                                                     string.split(re.sub('sn2.fits', 'fits', img), '/')[-1])
    for _filter in dicti:
        for img in dicti[_filter]:
            secondimage = []
            mjdvec = []
            filtvec = []
            colore = []
            for ii in dicti[_filter][img].keys():
                if 'ZP' in ii:  # for each zero point available
                    cc = ii[-2:]  #  color used
                    for filt2 in dicti.keys():
                        if filt2 != _filter:
                            for jj in dicti[filt2].keys():
                                for ll in dicti[filt2][jj].keys():
                                    if 'ZP' in ll and ll[-2:] == cc: # different filter with same color
                                        secondimage.append(jj)
                                        mjdvec.append(dicti[filt2][jj]['mjd'] - dicti[_filter][img]['mjd'])
                                        filtvec.append(filt2)
                                        colore.append(cc)

            if len(secondimage) > 0:
                colorescelto = ''
                vv = queste1[filterst1[_filter]]
                if len(vv) > 0:
                    if vv[0].upper() in colore:
                        colorescelto = vv[0].upper()
                else:
                    vv = queste0[filterst1[_filter]]
                    if len(vv) > 0:
                        if vv[0].upper() in colore:
                            colorescelto = vv[0].upper()
                if colorescelto:
                    print 'use ' + _filter + ' with color ' + colorescelto
                    filtvec = np.compress(np.array(colore) == colorescelto, filtvec)
                    mjdvec = np.compress(np.array(colore) == colorescelto, mjdvec)
                    secondimage = np.compress(np.array(colore) == colorescelto, secondimage)
                    colore = np.compress(np.array(colore) == colorescelto, colore)

                dicti[_filter][img]['secondimg'] = secondimage[np.argmin(mjdvec)]  # the closest image
                dicti[_filter][img]['secondfilt'] = filtvec[np.argmin(mjdvec)]  # the closest image
                _filter2 = dicti[_filter][img]['secondfilt']
                col = colore[np.argmin(mjdvec)]
                ra0 = dicti[_filter][img]['ra0']
                dec0 = dicti[_filter][img]['dec0']
                ra = dicti[_filter][img]['ra']
                dec = dicti[_filter][img]['dec']
                siteid = dicti[_filter][img]['siteid']
                if siteid in lsc.sites.extinction:
                    kk = lsc.sites.extinction[siteid]
                else:
                    print dicti[_filter][img]
                    sys.exit('siteid not in lsc.sites.extinction')
                mag0 = dicti[_filter][img][namemag[_typemag][0]] - kk[filterst1[_filter]] * dicti[_filter][img][
                    'airmass']
                dmag0 = dicti[_filter][img][namemag[_typemag][1]]

                # img 2  ###############
                img2 = dicti[_filter][img]['secondimg']
                ra1 = dicti[_filter2][img2]['ra0']
                dec1 = dicti[_filter2][img2]['dec0']

                siteid = dicti[_filter2][img2]['siteid']
                if siteid in lsc.sites.extinction:
                    kk = lsc.sites.extinction[siteid]
                else:
                    print dicti[_filter2][img2]
                    sys.exit('siteid not in lsc.sites.extinction')
                mag1 = dicti[_filter2][img2][namemag[_typemag][0]] - kk[filterst1[_filter2]] * dicti[_filter2][img2][
                    'airmass']
                dmag1 = dicti[_filter2][img2][namemag[_typemag][1]]

                if _interactive:
                    lsc.util.marksn2(re.sub('sn2.fits', 'fits', img), img, 1, img2)
                    lsc.util.marksn2(re.sub('sn2.fits', 'fits', img2), img2, 2, img)
                    print img, img2, _filter, _filter2, 2.5 * np.log10(dicti[_filter2][img2]['exptime']), kk[filterst1[
                        _filter2]] * dicti[_filter2][img2]['airmass']

                distvec, pos0, pos1 = lsc.lscastrodef.crossmatch(np.array(ra0), np.array(dec0), np.array(ra1),
                                                                 np.array(dec1), 10)

                mag0cut = mag0[pos0]
                mag1cut = mag1[pos1]
                dmag0cut = dmag0[pos0]
                dmag1cut = dmag1[pos1]
                ra0cut = ra0[pos0]
                dec0cut = dec0[pos0]
                racut = ra[pos0]
                deccut = dec[pos0]
                ww = np.asarray([i for i in range(len(mag0cut)) if
                                 (abs(float(mag0cut[i])) < 99 and abs(float(mag1cut[i])) < 99    )])
                if len(ww) > 0:
                    mag0cut, mag1cut, dmag0cut, dmag1cut, ra0cut, dec0cut, racut, deccut = mag0cut[ww], mag1cut[ww], \
                                                                                           dmag0cut[ww], dmag1cut[ww], \
                                                                                           ra0cut[ww], dec0cut[ww], \
                                                                                           racut[ww], deccut[ww]

                if _interactive:
                    from pylab import *

                    ion()
                    clf()
                    plot(ra1, dec1, 'xb')
                    plot(ra0, dec0, 'xr')
                    plot(ra0cut, dec0cut, 'xg')

                output = re.sub('sn2.fits', 'cat', img)
                f = open(output, 'w')
                f.write('#daophot+standardfield\n#ra   dec   ' + filterst1[_filter] + '   d' + filterst1[_filter] + '\n')
                if filterst1[_filter].upper() == col[0]:
                    Z1 = float(string.split(dicti[_filter][img]['ZP' + filterst1[_filter].upper() + col.upper()])[1])
                    C1 = float(string.split(dicti[_filter][img]['ZP' + filterst1[_filter].upper() + col.upper()])[2])
                    Z2 = float(string.split(dicti[_filter2][img2]['ZP' + filterst1[_filter2].upper() + col.upper()])[1])
                    C2 = float(string.split(dicti[_filter2][img2]['ZP' + filterst1[_filter2].upper() + col.upper()])[2])
                    DZ1 = 0.0
                    DZ2 = 0.0
                    M1, M2 = lsc.lscabsphotdef.finalmag(Z1, Z2, C1, C2, mag0cut, mag1cut)
                    dc1, dc2, dz1, dz2, dm1, dm2 = lsc.lscabsphotdef.erroremag(Z1, Z2, M1, M2, C1, C2, 0)
                    DM11 = np.sqrt((dm1 * dmag0cut) ** 2 + (dz1 * DZ1) ** 2 + (dm2 * dmag1cut) ** 2 + (dz2 * DZ2) ** 2)

                    if _interactive:
                        print '\n####  example computation '
                        print 'Z1  Z1  C1   C2   mag1    mag 2'
                        print 'M1   M2 '
                        for gg in range(0, len(mag0cut)):
                            print racut[gg], deccut[gg], Z1, Z2, C1, C2, mag0cut[gg], mag1cut[gg], M1[gg], M2[gg]

                    for i in range(0, len(ra0cut)):
                        f.write('%15s \t%15s \t%s\t%s\n' % (racut[i], deccut[i], M1[i], dmag0cut[i]))
                else:
                    Z2 = float(string.split(dicti[_filter][img]['ZP' + filterst1[_filter].upper() + col.upper()])[1])
                    C2 = float(string.split(dicti[_filter][img]['ZP' + filterst1[_filter].upper() + col.upper()])[2])
                    Z1 = float(string.split(dicti[_filter2][img2]['ZP' + filterst1[_filter2].upper() + col.upper()])[1])
                    C1 = float(string.split(dicti[_filter2][img2]['ZP' + filterst1[_filter2].upper() + col.upper()])[2])
                    M1, M2 = lsc.lscabsphotdef.finalmag(Z1, Z2, C1, C2, mag1cut, mag0cut)
                    DZ1 = 0.0
                    DZ2 = 0.0
                    dc1, dc2, dz1, dz2, dm1, dm2 = lsc.lscabsphotdef.erroremag(Z1, Z2, mag0cut, mag1cut, C1, C2, 1)
                    DM22 = np.sqrt((dm1 * dmag0cut) ** 2 + (dz1 * DZ1) ** 2 + (dm2 * dmag1cut) ** 2 + (dz2 * DZ2) ** 2)

                    if _interactive:
                        print '\n####  example computation '
                        print 'Z1  Z1  C1   C2   mag1    mag 2'
                        print 'M1   M2 '
                        for gg in range(0, len(mag0cut)):
                            print racut[gg], deccut[gg], Z1, Z2, C1, C2, mag0cut[gg], mag1cut[gg], M1[gg], M2[gg]

                    for i in range(0, len(ra0cut)):
                        f.write('%15s \t%15s \t%s\t%s\n' % (racut[i], deccut[i], M2[i], dmag0cut[i]))
                f.close()

                if _interactive:    raw_input('go on')
                if os.path.isfile(re.sub('sn2.fits', 'cat', img)):
                    lsc.mysqldef.updatevalue('photlco', 'abscat', string.split(output, '/')[-1],
                                             re.sub('sn2.fits', 'fits', string.split(img, '/')[-1]))
                else:
                    lsc.mysqldef.updatevalue('photlco', 'abscat', 'X',
                                             re.sub('sn2.fits', 'fits', string.split(img, '/')[-1]))
            else:
                print 'no other filters with calibration in ' + _filter + ' band'
                print img, _filter, dicti[_filter][img].keys()
                lsc.mysqldef.updatevalue('photlco', 'abscat', 'X',
                                         re.sub('sn2.fits', 'fits', string.split(img, '/')[-1]))

