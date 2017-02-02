#!/usr/bin/env python
description = ">> New automated sn measurement"
usage = "%prog image [options] "

import time
from numpy import array,log10
import numpy as np
import lsc
import glob
import os
import sys
import shutil
import string
import re
from astropy.io.fits import getheader
from astropy.io import fits
from optparse import OptionParser

if __name__ == "__main__":
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-p", "--psf", dest="psf", default='',
                      type='str', help='psf file \t\t\t %default')
    parser.add_option("-R", "--RA", dest="RA", default='', type='str', help='RA coordinate \t\t\t %default')
    parser.add_option("-D", "--DEC", dest="DEC", default='', type='str',
                      help='DEC coordinate \t\t\t %default')
    parser.add_option("--RA0", dest="RA0", default='', type='str',
                      help='RA coordinate where centering the box stamp \t\t\t %default')
    parser.add_option("--DEC0", dest="DEC0", default='', type='str',
                      help='DEC coordinate where centering the box stamp \t\t\t %default')
    parser.add_option("-n", "--iteration", dest="niter", default=3, type='int',
                      help=' number of iterations \t\t %default')
    parser.add_option("-x", "--xorder", dest="xorder", default=2, type='int',
                      help=' order for backgorund in x \t\t %default')
    parser.add_option("-y", "--yorder", dest="yorder", default=2, type='int',
                      help=' order for backgroun in y \t\t %default')
    parser.add_option("-b", "--bkg", dest="bkg", default=4, type='float',
                      help=' backgroun radius dimension \t\t %default')
    parser.add_option("-z", "--size", dest="size", default=7, type='float',
                      help=' half size of the stamp \t\t %default')
    parser.add_option("-m", "--datamax", dest="datamax", default=51000, type='float',
                      help=' data max for saturation \t\t %default')
    parser.add_option("--datamin", dest="datamin", default=-500, type='float',
                      help=' data min for saturation \t\t %default')
    parser.add_option("-i", "--interactive", action="store_true", dest='interactive', default=False,
                      help='Interactive \t\t\t [%default]')
    parser.add_option("-s", "--show", action="store_true", dest='show', default=False,
                      help='display images \t\t\t [%default]')
    parser.add_option("-c", "--center", action="store_false", dest='recenter', default=True,
                      help='recenter \t\t\t [%default]')
    parser.add_option("-r", "--redo", dest="redo", action="store_true",
                      default=False, help=' redo measurement \t\t\t [%default]')
    option, args = parser.parse_args()
    if len(args) < 1: sys.argv.append('--help')
    option, args = parser.parse_args()
    imglist = lsc.util.readlist(args[0])
    if option.psf:
        psflist = lsc.util.readlist(option.psf)
    else:
        psflist = ''
    _ra = option.RA
    _dec = option.DEC
    _ra0 = option.RA0
    _dec0 = option.DEC0
    _size = option.size
    _fb = option.bkg
    _xord = option.xorder
    _yord = option.yorder
    _numiter = option.niter
    _dmax = option.datamax
    _dmin = option.datamin
    _interactive = option.interactive
    arterr = ''

    _ra = string.split(_ra,',')
    _dec = string.split(_dec,',')

    if option.recenter == False:
        _recenter = True
    else:
        _recenter = False
    if option.show == False:
        _show = False
    else:
        _show = True
    if option.redo == False:
        redo = False
    else:
        redo = True

    if _interactive:
        _show = True

    #####################   if the centering coordinates are not defined, use coordinate of the object
    if _ra and not _ra0:
        _ra0 = _ra[0]
    if _dec and not _dec0:
        _dec0 = _dec[0]

    # ####################### SET   IRAF   PARAMETERS  #######################
    from pyraf import iraf

    iraf.astcat(_doprint=0)
    iraf.imcoords(_doprint=0)
    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    from iraf import digiphot
    from iraf import daophot
    from iraf import ptools

    zmag = 0
    iraf.digiphot.daophot.photpars.zmag = zmag

    warn = '##################################\n'
    for imglong in imglist:
        if imglong:
            if imglong[-5:] == '.fits':
                img = imglong[:-5]
            else:
                img = imglong
            ######    set database value to 9999 before calculating them again ##################
            try:
                print string.split(img, '/')[-1] + '.fits'
                lsc.mysqldef.updatevalue('photlco', 'psfmag', 9999, string.split(img, '/')[-1] + '.fits')
                lsc.mysqldef.updatevalue('photlco', 'psfdmag', 9999, string.split(img, '/')[-1] + '.fits')
                lsc.mysqldef.updatevalue('photlco', 'psfx', 9999, string.split(img, '/')[-1] + '.fits')
                lsc.mysqldef.updatevalue('photlco', 'psfy', 9999, string.split(img, '/')[-1] + '.fits')
                lsc.mysqldef.updatevalue('photlco', 'apmag', 9999, string.split(img, '/')[-1] + '.fits')
            except:
                print 'module mysqldef not found'
            ####################################################################################

            #########  read header, find psf file  #############################################
            hdr = lsc.util.readhdr(imglong)
            _instrument = lsc.util.readkey3(hdr, 'instrume')
            filter = lsc.util.readkey3(hdr, 'filter')
            print '##########  ' + str(filter) + '  ##############'
            ###################        added for difference images ###############
            DM = 0
            if 'CONVOL00' in hdr:
                if hdr['CONVOL00'] == 'TEMPLATE':
                    _difexp  = lsc.util.readkey3(hdr, 'exptime')
                    _targexp = lsc.util.readkey3(hdr, 'exptarg')
                    _tempexp = lsc.util.readkey3(hdr, 'exptemp')
                    print _difexp, _targexp, _tempexp
                    DM = 2.5*log10(_targexp)-2.5*log10(_difexp)
            print '#### ',str(DM)
            ######################################################################
            if not psflist:
                psfimage = img + '.psf'
            else:
                psfimage = re.sub('.fits', '', psflist[0])
            skip = 0

            if os.path.exists(img + '.sn2.fits'):
                hdr2 = lsc.util.readhdr(img + '.sn2.fits')
                snmag1 = lsc.util.readkey3(hdr2, 'PSFMAG1')
                if snmag1 and not redo:
                    skip = 1
            else:
                sys.exit('psf not computed')
            print psfimage
            if not os.path.exists(psfimage + '.fits'):
                sys.exit('missing psf file')
            if redo:
                skip = 0
            ####################################################################################


            #######################  plot image, find fwhm  #####################################
            if skip == 0:
                iraf.set(stdimage='imt2048')
                if _interactive:
                    _z1, _z2, goon = lsc.util.display_image(img + '.fits', 1, '', '', True, _xsize=1, _ysize=1)
                elif _show:
                    _z1, _z2, goon = lsc.util.display_image(img + '.fits', 1, '', '', False)
                apco0 = lsc.util.readkey3(hdr2, 'APCO')

                if 'PIXSCALE' in hdr2:
                    pixelscale = lsc.util.readkey3(hdr2, 'PIXSCALE')
                elif 'CCDSCALE' in hdr2:
                    pixelscale = lsc.util.readkey3(hdr2, 'CCDSCALE')

                if 'fs' in _instrument or 'em' in _instrument:
                    if 'CCDXBIN' in hdr2:
                        fwhm0 = lsc.util.readkey3(hdr2, 'PSF_FWHM') / (pixelscale * lsc.util.readkey3(hdr2, 'CCDXBIN'))
                    elif 'CCDSUM' in hdr2:
                        fwhm0 = lsc.util.readkey3(hdr2, 'PSF_FWHM') / (
                        pixelscale * int(string.split(lsc.util.readkey3(hdr2, 'CCDSUM'))[0]))
                    else:
                        fwhm0 = lsc.util.readkey3(hdr2, 'PSF_FWHM') / (pixelscale)
                else:
                    fwhm0 = lsc.util.readkey3(hdr2, 'PSF_FWHM') / pixelscale
                if not apco0:
                    print '\n### warning: apco not found'
                    apco0 = 0
                if not fwhm0:
                    print '\n### warning: fwhm not found'
                    fwhm0 = 6
            ##################################################################################

            ##################  find coordinate for the box position      #########
            xx0, yy0 = '', ''
            if skip == 0:
                if not _ra0 and not _dec0:
                    try:
                        print 'no box coordinate from input, take coordinate from database'
                        _ra0, _dec0, _SN0, _tt = lsc.util.checksndb(img + '.fits', 'targets')
                    except:
                        print 'no coordinate from database'
                        _ra0,_dec0,_SN0='','',''
                    if _SN0:
                        print '\n###  SN in our list ' + _SN0
                if not _ra[0] and not _dec[0]:
                    print 'no sn coordinate from input'
                    if _ra0:
                        print 'use coordinate from the box for the SN'
                        _ra= [_ra0]
                    else:
                        sys.exit('no box and sn coordinate ')
                    if _dec0:
                        _dec= [_dec0]
                    else:
                        sys.exit('no box and sn coordinate ')



                if _ra and _dec:
                    os.system('rm -rf tmp.*')
                    lll=[]
                    for jj in range(0,len(_ra)):
                        lll.append(str(_ra[jj]) + '    ' + str(_dec[jj]))
                        #lll = [str(_ra) + '    ' + str(_dec)]
                    iraf.wcsctran('STDIN', 'tmp.pix', img + '[0]', Stdin=lll, inwcs='world', units='degrees degrees',
                                  outwcs='logical', columns='1 2', formats='%10.1f %10.1f')
                    if _show:
                        iraf.tvmark(1, 'tmp.pix', mark="circle", number='yes', radii=10, nxoffse=5, nyoffse=5,
                                           color=214, txsize=2)
                    xxsn, yysn = [], []

                    for kk in iraf.fields('tmp.pix', '1,2', Stdout=1):
                        if kk:
                            xxsn.append(string.split(kk)[0])
                            yysn.append(string.split(kk)[1])

                    xxsn = array(xxsn,float)
                    yysn = array(yysn,float)

                    print 'SN coordinate ',xxsn, yysn

                if _ra0 and _dec0:
                    os.system('rm -rf tmp.*')
                    lll = [str(_ra0) + '    ' + str(_dec0)]
                    iraf.wcsctran('STDIN', 'tmp.pix', img + '[0]', Stdin=lll, inwcs='world', units='degrees degrees',
                                  outwcs='logical', columns='1 2', formats='%10.1f %10.1f')
                    if _show:
                        iraf.tvmark(1, 'tmp.pix', mark="circle", number='yes', radii=10, nxoffse=5, nyoffse=5,
                                           color=214, txsize=2)
                    xx0, yy0 = string.split(iraf.fields('tmp.pix', '1,2', Stdout=1)[2])
                    print 'box coordinate ',xx0, yy0
                    os.system('rm -rf tmp.*')
                else:
                    xx0, yy0 = '', ''

                if xx0 == '' and not _interactive:
                    sys.exit('coordinate of the object not found, reduction not possible')

                if _interactive:
                    repeat = 'y'
                    while repeat == 'y':
                        print "_____________________________________________"
                        print "  MARK SN REGION WITH - x -, EXIT  - q -"
                        try:
                            iraf.imexamine(img + '.fits', 1, wcs='logical', logfile='tmp.log', keeplog=True)
                            xytargets = iraf.fields('tmp.log', '1,2', Stdout=1)
                            xx0 = xytargets[0].split()[0]
                            yy0 = xytargets[0].split()[1]
                            lsc.util.delete("tmplabel")
                            ff = open('tmplabel', 'w')
                            ff.write(str(xx0) + ' ' + str(yy0) + ' -1' + ' \n')
                            ff.close()
                            iraf.tvmark(1, 'tmplabel', autol='no', mark="cross", inter='no', label='no', txsize=4)
                            repeat = raw_input('### repeat selection ? [y/n] ? [n] ')
                            if not repeat:
                                repeat = 'n'
                            elif repeat == 'yes':
                                repeat = 'y'
                            elif repeat == 'YES':
                                repeat = 'y'
                        except:
                            #x = y = value = 0
                            print '### WARNING: SN REGION NOT SELECTED !!!'
                            repeat = raw_input('### repeat selection ? [y/n] ? [n] ')
                            if not repeat:    repeat = 'n'
                            if repeat in ['Y', 'y', 'YES', 'yes', 'Yes']:
                                repeat = 'y'
                            else:
                                sys.exit('error: no coordinate for box position selected')

            #################################################################################

            ######################################    chose    size of the box  and cut it ###############
            if skip == 0:
                if not _interactive:
                    if not fwhm0:
                        sys.exit('error:  fwhm not defined ')
                    if not xx0:
                        sys.exit('error: no coordinate for box position selected')
                    if _size:
                        size = _size
                    else:
                        size = 7
                    lsc.util.delete("original.fits")
                    lsc.util.imcopy(imglong, 'original.fits', (float(xx0), float(yy0)), 2*size*fwhm0)
                else:
                    repeat = 'n'
                    while repeat in ['n','no','NO','N']:
                        size = raw_input('Size of the cut frame (fwhm) [' + str(_size) + '] ? ')
                        if not size:
                            size = _size
                        else:
                            size = int(size)
                        lsc.util.delete("original.fits")
                        lsc.util.imcopy(imglong, 'original.fits', (float(xx0), float(yy0)), 2*size*fwhm0)
                        iraf.set(stdimage='imt512')
                        _tmp1, _tmp2, goon = lsc.util.display_image('original.fits', 1, '', '', False, _xsize=.5,
                                                                    _ysize=.5)
                        repeat = raw_input('### ok ? [y/n] ? [y] ')
                        if not repeat:
                            repeat = 'y'
                x1 = float(xx0) - size * fwhm0
                y1 = float(yy0) - size * fwhm0
                xxsn -= x1
                yysn -= y1
            ####################################### plot with right cuts   ##########################
            z11, z22='',''
            if skip == 0:
                if _show:
                    _z11, _z22, good = lsc.util.display_image('original.fits', 1, '', '', False, _xsize=.5, _ysize=.5)
                    z11, z22 = _z11, _z22
                if _interactive:
                    answ = 'y'
                    answ = raw_input(">>>>> Cuts OK [y/n] [y]?")
                    if not answ:
                        answ = 'y'
                    elif answ == 'no':
                        answ = 'n'
                    while answ == 'n':
                        z11 = raw_input('>>> z1 = ? [' + str(_z11) + '] ? ')
                        z22 = raw_input('>>> z2 = ? [' + str(_z22) + '] ? ')
                        if not z11:
                            z11 = _z11
                        else:
                            z11 = float(z11)
                        if not z22:
                            z22 = _z22
                        else:
                            z22 = float(z22)
                        _z11, _z22, goon = lsc.util.display_image('original.fits', 1, z11, z22, False)
                        answ = raw_input(">>>>> Cuts OK [y/n] [y]?")
                        if not answ:
                            answ = 'y'
                        elif answ == 'no':
                            answ = 'n'
                        z11 = float(_z11)
                        z22 = float(_z22)
            ###############################################################################################3
            ########################################  write  SN coordinates in coo file  ########################
            if skip == 0:
                if not _interactive:
                    #_dimension = string.split((string.split(iraf.imheader('original', Stdout=1)[0], ']')[0]), '[')[1]
                    #aa, bb = string.split(_dimension, ',')
                    #aa, bb = float(aa) / 2, float(bb) / 2
                    vector=[]
                    for ii in range(0,len(xxsn)):
                        vector.append(str(xxsn[ii]) + '  ' + str(yysn[ii]) + '  1')

                    ff = open('tmplabel', 'w')
                    for i in vector:
                        ff.write(i + ' \n')
                    ff.close()
                    if _show:
                        iraf.tvmark(1, 'tmplabel', autol='no', mark="circle", radii=10, inter='no', label='no',
                                    number='yes', pointsize=20, txsize=2, color=204)
                    os.system('cp tmplabel ' + img + '.sn.coo')
                else:
                    answ0 = 'n'
                    while answ0 == 'n':
                        _tmp1, _tmp2, goon = lsc.util.display_image('original.fits', 1, z11, z22, False)
                        print "   ", str(z11), str(z22)
                        print "__________________________________________________"
                        print "IDENTIFY SN AND CO-STARS(S) WITH - x -, EXIT - q -"
                        print "__________________________________________________"
                        print " 1 1 'ID. SN AND CO-STAR(S) WITH -x- EXIT -q-'"
                        lsc.util.delete("tmplabel")
                        vector = iraf.imexamine('original.fits', 1, wcs='logical', xformat='', yformat='',
                                                use_display='no', Stdout=1)
                        if string.count(vector[0], 'z1') == 1: vector = vector[1:]
                        ff = open('tmplabel', 'w')
                        for i in vector:
                            ff.write(i + ' \n')
                        ff.close()
                        if _show:
                            iraf.tvmark(1, 'tmplabel', autol='no', mark="circle", radii=10, inter='no',
                                        label='no', number='yes', pointsize=20, txsize=2, color=204)
                        os.system('cp tmplabel ' + img + '.sn.coo')
                        answ0 = raw_input(">>>>> SN AND CO-STARS(S) IDENTIFICATIONS OK [y/n] [y]?")
                        if not answ0:
                            answ0 = 'y'
                        elif answ0 == 'no':
                            answ0 = 'n'



            if skip == 0:
                ############################ BACKGROUND FIT   ###############################
                print ' ************  background fit **********************'
                answ0 = 'n'
                while answ0 == 'n':
                    lsc.util.delete("sky.fits,bg.fits,bgs.fits,sn.fits,residual.fits")
                    if _show:      lsc.util.display_image('original.fits', 1, z11, z22, False, _xsize=.5, _ysize=.5)
                    nax = int(getheader('original.fits')['NAXIS1'])
                    nay = int(getheader('original.fits')['NAXIS2'])
                    if len(vector) == 1:
                        xb, yb, value = string.split(vector[0])
                        checkleng0 = 'yes'
                        while checkleng0 == 'yes':
                            if not _interactive:
                                    leng0 = _fb
                            else:
                                leng0 = raw_input('>>> length of square for background in units of FWHM [3] ? ')
                                if not leng0:
                                    leng0 = 3
                            try:
                                float(leng0)
                                checkleng0 = 'no'
                            except:
                                print 'WARNING: the FWHM should be a number !!!!'
                                checkleng0 == 'yes'
                        if _show:
                            iraf.tvmark(1, img + ".sn.coo", auto='no', mark="rectangle",
                                                 length=int(fwhm0 * float(leng0)), inter='no', color=204)
                        xb1 = int(float(xb) - fwhm0 * float(leng0) / 2)
                        xb2 = int(float(xb) + fwhm0 * float(leng0) / 2)
                        yb1 = int(float(yb) - fwhm0 * float(leng0) / 2)
                        yb2 = int(float(yb) + fwhm0 * float(leng0) / 2)
                        sec = "1 " + str(xb1) + " 1 " + str(nay) + '\n'
                        sec = sec + str(xb2) + ' ' + str(nax) + " 1 " + str(nay) + '\n'
                        sec = sec + str(xb1) + ' ' + str(xb2) + " 1 " + str(yb1) + '\n'
                        sec = sec + str(xb1) + ' ' + str(xb2) + ' ' + str(yb2) + ' ' + str(nay) + '\n'
                        ff = open('sec', 'w')
                        ff.write(sec)
                        ff.close()
                        inp = "bg.fits[" + str(xb1) + ":" + str(xb2) + "," + str(yb1) + ":" + str(yb2) + "]"
                        out = "sky.fits[" + str(xb1) + ":" + str(xb2) + "," + str(yb1) + ":" + str(yb2) + "]"
                        checkorder = 'yes'
                        while checkorder == 'yes':
                            if not _interactive or _xord and _yord:
                                if _xord and _yord:
                                    xbgord0 = _xord
                                    ybgord0 = _yord
                                else:
                                    xbgord0 = _xbgord0
                                    ybgord0 = _ybgord0
                            else:
                                xbgord0 = raw_input('>>> Order of function in x for bg fit [' + str(_xbgord0) + '] ? ')
                                if not xbgord0:
                                    xbgord0 = _xbgord0
                                else:
                                    _xbgord0 = xbgord0
                                ybgord0 = raw_input(
                                    '>>> Order of function in y for bg fit ? [' + str(_ybgord0) + '] ? ')
                                if not ybgord0:
                                    ybgord0 = _ybgord0
                                else:
                                    _ybgord0 = ybgord0
                            try:
                                float(xbgord0)
                                float(ybgord0)
                                checkorder = 'no'
                            except:
                                print 'WARNING: value not valid !!'
                                checimsurfitkorder = 'yes'
                        iraf.imsurfit("original", "bg", xorder=xbgord0, yorder=ybgord0, regions="section",
                                      section="sec")
                    else:
                        if not _interactive:
                            print 'select'
                            xb1 = int(min(xxsn) - fwhm0*_fb)
                            xb2 = int(max(xxsn) + fwhm0*_fb)
                            yb1 = int(min(yysn) - fwhm0*_fb)
                            yb2 = int(max(yysn) + fwhm0*_fb)

                        else:
                            lsc.util.delete("tmplabel")
                            lsc.util.delete("tmptbl")
                            ff = open('tmplabel', 'w')
                            ff.write('')
                            ff.close()
                            print ">>>  Mark corners of bg-region with  >b<, exit  >q<"
                            iraf.tvmark(1, "tmplabel", autol='no', mark="none", inter='no', label='yes', txsize=2,
                                        color=204)
                            iraf.tvmark(1, "", logfile="tmptbl", autol='yes', mark="cross", inter='yes', color=204)
                            ff = open('tmptbl', 'r')
                            ss = ff.readlines()
                            ff.close()
                            xb1 = int(float(string.split(ss[-2])[0]))
                            yb1 = int(float(string.split(ss[-2])[1]))
                            xb2 = int(float(string.split(ss[-1])[0]))
                            yb2 = int(float(string.split(ss[-1])[1]))

                        sec = "1 " + str(xb1) + " 1 " + str(nay) + '\n'
                        sec = sec + str(xb2) + ' ' + str(nax) + " 1 " + str(nay) + '\n'
                        sec = sec + str(xb1) + ' ' + str(xb2) + " 1 " + str(yb1) + '\n'
                        sec = sec + str(xb1) + ' ' + str(xb2) + ' ' + str(yb2) + ' ' + str(nay) + '\n'
                        ff = open('sec', 'w')
                        ff.write(sec)
                        ff.close()
                        inp = "bg.fits[" + str(xb1) + ":" + str(xb2) + "," + str(yb1) + ":" + str(yb2) + "]"
                        out = "sky.fits[" + str(xb1) + ":" + str(xb2) + "," + str(yb1) + ":" + str(yb2) + "]"

                        checkorder = 'yes'
                        while checkorder == 'yes':
                            if not _interactive or _xord and _yord:
                                if _xord and _yord:
                                    xbgord0 = _xord
                                    ybgord0 = _yord
                                else:
                                    xbgord0 = _xbgord0
                                    ybgord0 = _ybgord0
                            else:
                                xbgord0 = raw_input('>>> Order of function in x for bg fit [' + str(_xbgord0) + '] ? ')
                                if not xbgord0:
                                    xbgord0 = _xbgord0
                                else:
                                    _xbgord0 = xbgord0
                                ybgord0 = raw_input('>>> Order of function in y for bg fit [' + str(_ybgord0) + '] ? ')
                                if not ybgord0:
                                    ybgord0 = _ybgord0
                                else:
                                    _ybgord0 = ybgord0
                            try:
                                float(xbgord0)
                                float(ybgord0)
                                checkorder = 'no'
                            except:
                                print 'WARNING: value not valid !!'
                                checkorder = 'yes'
                        iraf.imsurfit("original", "bg", xorder=xbgord0, yorder=ybgord0, regions="sections",
                                      sections="sec")

                    midpt = np.mean(fits.getdata('bg.fits'))
                    iraf.imcopy("original.fits", "sky.fits")
                    iraf.imcopy(inp, "bgs.fits")
                    iraf.imcopy("bgs.fits", out)
                    iraf.imarith("original.fits", "-", "sky.fits", "sn.fits")
                    iraf.imarith("sn.fits", "+", midpt, "sn.fits")
                    answ0 = 'y'
                    print answ0
                    if _show or _interactive:
                        _tmp1, _tmp2, goon = lsc.util.display_image('original.fits', 1, z11, z22, False, _xcen=.25,
                                                                    _ycen=.25, _xsize=.3, _ysize=.3)
                    s1 = 1
                    s2 = -int(fwhm0)
                    lsc.util.delete("tmptbl")
                    ff = open('tmptbl', 'w')
                    ff.write(str(s1) + ' ' + str(s2) + " ORIGINAL")
                    ff.close()
                    if _show:
                        iraf.tvmark(1, "tmptbl", autol='no', mark="none", inter='no', label='yes', txsize=2)
                        _tmp1, _tmp2, goon = lsc.util.display_image('sky.fits', 1, z11, z22, False, _xcen=.25,
                                                                    _ycen=.75, _xsize=.3, _ysize=.3, _erase='no')
                    lsc.util.delete("tmptbl")
                    ff = open('tmptbl', 'w')
                    ff.write(str(s1) + ' ' + str(s2) + " BACKGROUND_FIT")
                    ff.close()
                    if _show:
                        iraf.tvmark(1, "tmptbl", autol='no', mark="none", inter='no', label='yes', txsize=2)
                        _tmp1, _tmp2, goon = lsc.util.display_image('sn.fits', 1, z11, z22, False, _xcen=.75, _ycen=.25,
                                                                    _xsize=.3, _ysize=.3, _erase='no')
                    lsc.util.delete("tmptbl")
                    ff = open('tmptbl', 'w')
                    ff.write(str(s1) + ' ' + str(s2) + " STARS")
                    ff.close()
                    if _show:    iraf.tvmark(1, "tmptbl", autol='no', mark="none", inter='no', label='yes', txsize=2)
                    if not _interactive:
                        answ0 = 'y'
                    else:
                        answ0 = raw_input(">>> Background fit OK [y/n] [y] ?")
                        if not answ0:
                            answ0 = 'y'
                        elif answ0 == 'no':
                            answ0 = 'n'

                ####################################    FITSN        ###################################
                print img, psfimage, 'xxxxx'
                apori1, apori2, apori3, apmag1, apmag2, apmag3, fitmag, truemag, magerr, centx, centy = \
                    lsc.lscsnoopy.fitsn(img, psfimage, img + '.sn.coo', _recenter, fwhm0, 'original', 'sn',
                                        'residual', _show, _interactive, z11, z22, midpt, _size, apco0, _dmax, _dmin)
                #################       Iterate Beckground    ###################################
                if _interactive:
                    if not _numiter:
                        answ0 = raw_input(">>> Iterate on background [y/n] [y] ?")
                        if not answ0: answ0 = 'y'
                    elif _numiter >= 1:
                        answ0 = 'y'
                    else:
                        answ0 = 'n'
                else:
                    if _numiter >= 1:
                        answ0 = 'y'
                        time.sleep(1) #to prevent iraf warning
                    else:
                        answ0 = 'n'
                _count = 0
                while answ0 == 'y':
                    _count = _count + 1
                    print '######'
                    print '###### iteration number  ' + str(_count)
                    print '######'
                    lsc.util.delete("sn.fits,residual.fits,snfit.fits,tmp.fits")
                    checkorder = 'yes'
                    while checkorder == 'yes':
                        if not _interactive or _xord and _yord:
                            if _xord and _yord:
                                xbgord0 = _xord
                                ybgord0 = _yord
                            else:
                                xbgord0 = _xbgord0
                                ybgord0 = _ybgord0
                        else:
                            xbgord0 = raw_input('>>> Order of function in x for bg fit [' + str(_xbgord0) + '] ? ')
                            if not xbgord0:
                                xbgord0 = _xbgord0
                            else:
                                _xbgord0 = xbgord0
                            ybgord0 = raw_input('>>> Order of function in x for bg fit [' + str(_ybgord0) + '] ? ')
                            if not ybgord0:
                                ybgord0 = _ybgord0
                            else:
                                _ybgord0 = ybgord0
                        try:
                            float(xbgord0)
                            float(ybgord0)
                            checkorder = 'no'
                        except:
                            print 'WARNING: value not valid !!'
                            checkorder = 'yes'
                    iraf.imsurfit("skyfit", "tmp", regions="all", xorder=xbgord0, yorder=ybgord0)
                    midpt = np.mean(fits.getdata("tmp.fits"))
                    iraf.imarith("original", "-", "tmp", "sn", calctype="r", pixtype="r")
                    iraf.imarith("sn.fits", "+", midpt, "sn.fits")
                    lsc.util.delete("skyfit.fits")
                    apori1, apori2, apori3, apmag1, apmag2, apmag3, fitmag, truemag, magerr, centx, centy = \
                        lsc.lscsnoopy.fitsn( img, psfimage, img + '.sn.coo', _recenter, fwhm0, 'original', 'sn',
                                             'residual', _show, _interactive, z11, z22, midpt, _size, apco0, _dmax, _dmin)
                    print _numiter, _count
                    if _interactive:
                        if not _numiter:
                            answ0 = raw_input(">>> Iterate on background [y/n] [y] ?")
                            if not answ0: answ0 = 'y'
                        elif _count >= _numiter:
                            answ0 = 'n'
                        else:
                            answ0 = 'y'
                    else:
                        if _count >= _numiter:
                            answ0 = 'n'
                        else:
                            answ0 = 'y'

                print "***************************************************************************"
                print "#id  x_ori    y_ori      x       y      ap_ori   ap_bgsub   fit_mag   err_art err_fit"
                for i in range(len(fitmag)):
                    print "SN", i, str(centx[i] + x1 - 1), str(centy[i] + y1 - 1), str(centx[i]), str(
                        centy[i]), "  ", str(apori3[i]), "  ", str(apmag3[i]), "  ", str(truemag[i]), "  ", str(
                        arterr), "  ", str(magerr[i])
                print "**************************************************************************"
                ##########            AGGIUSTAMENTO MANUALE                     ###############
                newmag = list(array(truemag))
                if not _interactive:
                    answ0 = 'n'
                else:
                    answ0 = raw_input(">>> Not yet happy ? Do you want to adjust manually stellar peak ? [y/n] [n] ")
                    if not answ0:
                        answ0 = 'n'
                    elif answ0 == 'yes':
                        answ0 = 'y'
                dmag0 = 0
                while answ0 == 'y':
                    checkdm = 'yes'
                    while checkdm == 'yes':
                        if len(truemag) > 1: print "!!!! WARNING: all components scaled accordingly !!!!"
                        _dmag0 = raw_input(">>> D(mag) adjustment (positive=fainter) [" + str(dmag0) + "]")
                        if _dmag0: dmag0 = _dmag0
                        try:
                            float(dmag0)
                            checkdm = 'no'
                        except:
                            checkdm = 'yes'
                    apori1, apori2, apori3, apmag1, apmag2, apmag3, fitmag, truemag, magerr, centx, centy, newmag = \
                        lsc.lscsnoopy.manusn(img, psfimage, dmag0, apori1, apori2, apori3, apmag1, apmag2, apmag3,
                                             fitmag, truemag, magerr, centx, centy, z11, z22, midpt, _size, fwhm0,
                                             x1, y1, arterr)
                    try:
                        dmag0 = newmag[0] - truemag[0]
                    except:
                        dmag0 = newmag[0]
                    answ0 = raw_input(">>> again ? [y/n] [y] ")
                    if not answ0:
                        answ0 = 'y'
                    elif answ0 == 'yes':
                        answ0 = 'y'
                truemag = list(array(newmag))
                #
                #### ESPERIMENTO DI STELLE ARTIFICIALI AL VOLO ############################
                #
                if not _interactive:
                    answ0 = 'n'
                else:
                    answ0 = raw_input(">>> Errors estimate (through artificial star experiment ?) [y/n] [y] ")
                    if not answ0:
                        answ0 = 'y'
                    elif answ0 == 'yes':
                        answ0 = 'y'
                if answ0 == 'y':
                    leng0 = 4
                    try:
                        _arterr2, _arterr = lsc.lscsnoopy.errore(img, 'artlist.coo', size, truemag, fwhm0, leng0, False,
                                                                 False, _numiter, z11, z22, midpt, nax, nay, xbgord0,
                                                                 ybgord0, _recenter, apco0, _dmax, _dmin)
                    except:
                        print '\n### warningstamp size too small: artificail error = 0 '
                        _arterr2, _arterr = 0.0, 0.0

                    if _interactive:
                        arterr = raw_input("arterr ? [%6.6s] " % (str(_arterr)))
                        if not arterr: arterr = _arterr
                    else:
                        arterr = _arterr
                else:
                    arterr = 0.0
                #######################   CHIUDI TUTTO ###################################
                #
                #fine:
                if DM:
                    print 'different image with template PSF: apply DM : '+str(DM)

                print "***************************************************************************"
                print "#id  x_ori   y_ori     x     y    ap_ori ap_bgsub  fit_mag  err_art  err_fit"
                print "# id   ap_original ap_bgsub  fit_mag  err_art  err_fit"  #,  >> nome0//".ec"
                print "# SN_FIT  "  #, >> nome0//".ec"
                print "# id ap_ori ap-bg  fit_mag"  #, >> nome0//".ec"
                for i in range(len(fitmag)):
                    print "SN", i, str(centx[i] + x1 - 1), str(centy[i] + y1 - 1), str(centx[i]), str(
                        centy[i]), "  ", str(apori3[i]), "  ", str(apmag3[i]), "  ", str(truemag[i]), "  ", str(
                        arterr), "  ", str(magerr[i])
                    if truemag[i] == 'INDEF':
                        truemag[i], arterr, magerr[i] = 9999, 0.0, 0.0
                    if apmag3[i] == 'INDEF':
                        apmag3[i] = 9999

                    headers = {'PSFX' + str(i + 1): [str(centx[i] + x1 - 1), 'x pos psf mag'],
                               'PSFY' + str(i + 1): [str(centy[i] + y1 - 1), 'y pos psf mag'],
                               'PSFMAG' + str(i + 1): [str(float(truemag[i]) - DM), 'psf magnitude'],
                               'PSFDMAG' + str(i + 1): [str(max(arterr, magerr[i])), 'psf mag error'],
                               'APMAG' + str(i + 1): [str(apmag3[i]), 'ap mag after bgsub']}
                    lsc.util.updateheader(img + '.sn2.fits', 0, headers)
                lsc.util.delete("apori")
                lsc.util.delete("sec")
                lsc.util.delete("skyfit.fits")
                lsc.util.delete("sn.fits")
                lsc.util.delete("artsn.fits")
                lsc.util.delete("artsky.fits,artbgs.fits")
                lsc.util.delete("bg.fits,bgs.fits")
                lsc.util.delete("tmp*")
                lsc.util.delete(img + ".sn.*")
                os.system('mv original.fits ' + img + '.og.fits')
                os.system('mv residual.fits ' + img + '.rs.fits')
                os.chmod(img + '.og.fits', 0664)
                os.chmod(img + '.rs.fits', 0664)
                try:
                    lsc.mysqldef.updatevalue('photlco', 'psfmag', truemag[0] - DM, string.split(img, '/')[-1] + '.fits')
                    lsc.mysqldef.updatevalue('photlco', 'psfdmag', max(arterr, magerr[0]),
                                             string.split(img, '/')[-1] + '.fits')
                    lsc.mysqldef.updatevalue('photlco', 'psfx', centx[0] + x1 - 1, string.split(img, '/')[-1] + '.fits')
                    lsc.mysqldef.updatevalue('photlco', 'psfy', centy[0] + y1 - 1, string.split(img, '/')[-1] + '.fits')
                    lsc.mysqldef.updatevalue('photlco', 'apmag', apmag3[0], string.split(img, '/')[-1] + '.fits')
                except:
                    print 'module mysqldef not found'
            else:
                print 'already done'
        else:
            print '####\n#### WARNING: empty space in the list !!\n####'
