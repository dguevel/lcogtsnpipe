#!/usr/bin/env python
description = ">> New automated psf version"
usage = "%prog image [options] "

# ###############################################################
# EC 2012 Feb 20  
# modified by SV for lsc 
################################################################
import os, sys, shutil, subprocess
import time
from optparse import OptionParser
from pyraf import iraf
from astropy.io import fits
from astropy.io import fits
import lsc
import re
import string
import traceback
import numpy as np

iraf.noao(_doprint=0)
iraf.obsutil(_doprint=0)


def runsex(img, fwhm, thresh, pix_scale):  ## run_sextractor  fwhm in pixel
    import lsc

    mina = 5.
    seeing = fwhm * pix_scale

    cdef = open(lsc.__path__[0] + '/standard/sex/default2.param')
    riga = cdef.readlines()
    cparam = []
    for r in riga:
        if r[0] != '#' and len(r.strip()) > 0: \
                cparam.append(r.split()[0])

    pid = subprocess.Popen("sex '" + img + ".fits[0]' -catalog_name tmp.cat" + \
                           " -c  " + lsc.__path__[0] + '/standard/sex/default2.sex' \
                                                       " -PARAMETERS_NAME " + lsc.__path__[
                               0] + "/standard/sex/default2.param" + \
                           " -STARNNW_NAME " + lsc.__path__[0] + "/standard/sex/default2.nnw" + \
                           " -PIXEL_SCALE " + str(pix_scale) + \
                           " -DETECT_MINAREA " + str(mina) + \
                           " -DETECT_THRESH  " + str(thresh) + \
                           " -ANALYSIS_THRESH  " + str(thresh) + \
                           " -PHOT_FLUXFRAC 0.5" + \
                           " -SEEING_FWHM " + str(seeing),
                           stdout=subprocess.PIPE, shell=True)

    output, error = pid.communicate()

    csex = open("tmp.cat")
    tab = {}
    riga = csex.readlines()
    for k in cparam: tab[k] = []
    for r in riga:
        if r[0] != '#':
            for i in range(len(cparam)):
                tab[cparam[i]].append(float(r.split()[i]))
    for k in cparam: tab[k] = np.array(tab[k])

    xdim, ydim = iraf.hselect(img+'[0]', 'i_naxis1,i_naxis2', 'yes', Stdout=1) \
        [0].split()

    xcoo, ycoo, ra, dec, magbest, classstar, fluxrad, bkg = [], [], [], [], [], [], [], []
    for i in range(len(tab['X_IMAGE'])):
        x, y = tab['X_IMAGE'][i], tab['Y_IMAGE'][i]
        if 5 < x < int(xdim) - 5 and 5 < y < int(ydim) - 5:  # trim border
            xcoo.append(x)
            ycoo.append(y)
            ra.append(tab['X_WORLD'][i])
            dec.append(tab['Y_WORLD'][i])
            magbest.append(tab['MAG_BEST'][i])
            classstar.append(tab['CLASS_STAR'][i])
            fluxrad.append(tab['FLUX_RADIUS'][i])
            bkg.append(tab['BACKGROUND'][i])

    return np.array(xcoo), np.array(ycoo), np.array(ra), np.array(dec), np.array(magbest), \
           np.array(classstar), np.array(fluxrad), np.array(bkg)


def psffit2(img, fwhm, psfstars, hdr, _datamax, psffun='gauss',  fixaperture=False):
    ''' 
    giving an image, a psffile,  calculate the magnitudes of strs in the file _psf.coo
    '''
    import lsc
    _ron = lsc.util.readkey3(hdr, 'ron')
    _gain = lsc.util.readkey3(hdr, 'gain')
    if not _ron:
        _ron = 1
        print 'warning ron not defined'
    if not _gain:
        _gain = 1
        print 'warning ron not defined'

    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    zmag = 0.
    varord = 0  # -1 analitic 0 - numeric

    if fixaperture:
        print 'use fix aperture 5 8 10'
        hdr = lsc.util.readhdr(img+'.fits')
        _pixelscale = lsc.util.readkey3(hdr, 'PIXSCALE')
        a1, a2, a3, a4, = float(5. / _pixelscale), float(5. / _pixelscale), float(8. / _pixelscale), float(
                    10. / _pixelscale)
    else:
        a1, a2, a3, a4, = int(fwhm + 0.5), int(fwhm * 2 + 0.5), int(fwhm * 3 + 0.5), int(fwhm * 4 + 0.5)

    iraf.fitskypars.annulus = a4
    iraf.fitskypars.salgori = 'mean'  #mode,mean,gaussian
    iraf.photpars.apertures = '%d,%d,%d' % (a2, a3, a4)
    iraf.datapars.datamin = -100
    iraf.datapars.datamax = _datamax
    iraf.datapars.readnoise = _ron
    iraf.datapars.epadu = _gain
    iraf.datapars.exposure = 'EXPTIME'  
    iraf.datapars.airmass = ''
    iraf.datapars.filter = ''
    iraf.photpars.zmag = zmag
    iraf.centerpars.calgori = 'centroid'
    iraf.centerpars.cbox = a2
    iraf.daopars.recenter = 'yes'
    iraf.delete('_psf2.ma*', verify=False)

    iraf.phot(img+'[0]', '_psf2.coo', '_psf2.mag', interac=False, verify=False, verbose=False)

    iraf.daopars.psfrad = a4
    iraf.daopars.functio = psffun
    iraf.daopars.fitrad = a1
    iraf.daopars.fitsky = 'yes'
    iraf.daopars.sannulus = a4
    iraf.daopars.recenter = 'yes'
    iraf.daopars.varorder = varord
    iraf.delete("_als2,_psf.grp,_psf.nrj", verify=False)
    iraf.group(img + '[0]', '_psf2.mag', img + '.psf', '_psf.grp', verify=False, verbose=False)
    iraf.nstar(img + '[0]', '_psf.grp', img + '.psf', '_als2', '_psf.nrj', verify=False, verbose=False)
    photmag = iraf.txdump("_psf2.mag", 'xcenter,ycenter,id,mag,merr', expr='yes', Stdout=1)
    fitmag = iraf.txdump("_als2", 'xcenter,ycenter,id,mag,merr', expr='yes', Stdout=1)
    return photmag, fitmag


def psffit(img, fwhm, psfstars, hdr, interactive, _datamax, psffun='gauss', fixaperture=False):
    ''' 
    giving an image, a psffile compute the psf using the file _psf.coo
    '''
    import lsc
    _ron = lsc.util.readkey3(hdr, 'ron')
    _gain = lsc.util.readkey3(hdr, 'gain')
    if not _ron:
        _ron = 1
        print 'warning ron not defined'
    if not _gain:
        _gain = 1
        print 'warning ron not defined'

    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    zmag = 0.
    varord = 0  # -1 analitic 0 - numeric

    if fixaperture:
        print 'use fix aperture 5 8 10'
        hdr = lsc.util.readhdr(img+'.fits')
        _pixelscale = lsc.util.readkey3(hdr, 'PIXSCALE')
        a1, a2, a3, a4, = float(5. / _pixelscale), float(5. / _pixelscale), float(8. / _pixelscale), float(
                    10. / _pixelscale)
    else:
        a1, a2, a3, a4, = int(fwhm + 0.5), int(fwhm * 2 + 0.5), int(fwhm * 3 + 0.5), int(fwhm * 4 + 0.5)

    iraf.fitskypars.annulus = a4
    iraf.fitskypars.salgori = 'mean'  #mode,mean,gaussian
    iraf.photpars.apertures = '%d,%d,%d' % (a2, a3, a4)
    iraf.datapars.datamin = -100
    iraf.datapars.datamax = _datamax
    iraf.datapars.readnoise = _ron
    iraf.datapars.epadu = _gain
    iraf.datapars.exposure = 'EXPTIME'
    iraf.datapars.airmass = ''
    iraf.datapars.filter = ''
    iraf.centerpars.calgori = 'centroid'
    iraf.centerpars.cbox = a2
    iraf.daopars.recenter = 'yes'
    iraf.photpars.zmag = zmag

    iraf.delete('_psf.ma*,' + img + '.psf.fit?,_psf.ps*,_psf.gr?,_psf.n*,_psf.sub.fit?', verify=False)
    iraf.phot(img+'[0]', '_psf.coo', '_psf.mag', interac=False, verify=False, verbose=False)

    # removes saturated stars from the list (IRAF just issues a warning)
    with open('_psf.mag') as f:
        text = f.read()
    text = re.sub('(.*\n){6}.*BadPixels\* \n', '', text)
    with open('_psf.mag', 'w') as f:
        f.write(text)

    iraf.daopars.psfrad = a4
    iraf.daopars.functio = psffun
    iraf.daopars.fitrad = a1
    iraf.daopars.fitsky = 'yes'
    iraf.daopars.sannulus = a4
    iraf.daopars.recenter = 'yes'
    iraf.daopars.varorder = varord

    if interactive: # not possible to run pstselect or psf interactively on 64-bit linux (Error 851)
        shutil.copyfile('_psf.mag', '_psf.pst')
        print '_' * 80
        print '>>> Mark good stars with "a" or "d"-elete. Then "f"-it,' + \
              ' "w"-write and "q"-uit (cursor on ds9)'
        print '-' * 80
    else:
        iraf.pstselect(img+'[0]', '_psf.mag', '_psf.pst', psfstars, interac=False, verify=False)

    iraf.psf(img + '[0]', '_psf.mag', '_psf.pst', img + '.psf', '_psf.psto', '_psf.psg', interac=interactive,
             verify=False, verbose=False)
    iraf.group(img + '[0]', '_psf.mag', img + '.psf', '_psf.grp', verify=False, verbose=False)
    iraf.nstar(img + '[0]', '_psf.grp', img + '.psf', '_psf.nst', '_psf.nrj', verify=False, verbose=False)

    photmag = iraf.txdump("_psf.mag", 'xcenter,ycenter,id,mag,merr', expr='yes', Stdout=1)
    pst = iraf.txdump("_psf.pst", 'xcenter,ycenter,id', expr='yes', Stdout=1)
    fitmag = iraf.txdump("_psf.nst", 'xcenter,ycenter,id,mag,merr', expr='yes', Stdout=1)
    return photmag, pst, fitmag


def ecpsf(img, ofwhm, threshold, psfstars, distance, interactive, psffun='gauss', fixaperture=False, _catalog='', _datamax=None, show=False):
    try:
        import lsc, string

        hdr = lsc.util.readhdr(img + '.fits')
        instrument = lsc.util.readkey3(hdr, 'instrume')
        print 'INSTRUMENT:', instrument

        if 'PIXSCALE' in hdr:
            scale = lsc.util.readkey3(hdr, 'PIXSCALE')
        elif 'CCDSCALE' in hdr:
            if 'CCDXBIN' in hdr:
                scale = lsc.util.readkey3(hdr, 'CCDSCALE') * lsc.util.readkey3(hdr, 'CCDXBIN')
            elif 'CCDSUM' in hdr:
                scale = lsc.util.readkey3(hdr, 'CCDSCALE') * int(string.split(lsc.util.readkey3(hdr, 'CCDSUM'))[0])

        if _datamax is None:
            _datamax = lsc.util.readkey3(hdr, 'datamax')
        _wcserr = lsc.util.readkey3(hdr, 'wcserr')
        print _wcserr
        if float(_wcserr) == 0:
            if 'L1FWHM' in hdr:
                seeing = float(lsc.util.readkey3(hdr, 'L1FWHM'))
            elif 'L1SEEING' in hdr:
                seeing = float(lsc.util.readkey3(hdr, 'L1SEEING')) * scale
            else:
                seeing = 3
        else:
            seeing = 3
            if 'PSF_FWHM' in hdr:
                seeing = float(lsc.util.readkey3(hdr, 'PSF_FWHM'))
            else:
                sys.exit('astrometry not good')
        #except:  sys.exit('astrometry not good')

        fwhm = seeing / scale
        print 'FWHM[header]  ', fwhm, '   in pixel'
        if ofwhm: fwhm = float(ofwhm)
        print '    FWHM[input]  ', fwhm, ' in pixel'

        xdim, ydim = iraf.hselect(img+'[0]', 'i_naxis1,i_naxis2', 'yes', Stdout=1)[0].split()
        print img, fwhm, threshold, scale,xdim

        #################################################################################
        ###################        write file to compute psf     _psf.coo    ############
        #################################################################################
        if _catalog:
            print '\n#### use catalog to measure the psf'
            ddd=iraf.wcsctran(input=_catalog,output='STDOUT',Stdout=1,image=img + '[0]',inwcs='world',outwcs='logical',
                              units='degrees degrees',columns='1 2',formats='%10.1f %10.1f',verbose='no')
            ddd=[i for i in ddd if i[0]!='#']
            ddd=['  '.join(i.split()[0:3]) for i in ddd]
            line=''
            for i in ddd:
                a,b,c = string.split(i)
                if float(a) < float(xdim) and  float(b) < float(ydim) and float(b) > 0:
                    line = line + '%10s %10s %10s \n' % (a, b, c)
            if line:
                ff = open('_psf.coo', 'w')
                ff.write(line)
                ff.close()
            else:
                sys.exit('error: no catalog objects are in the field')
        elif interactive:
            iraf.display(img + '[0]', 1, fill=True)
            iraf.delete('tmp.lo?', verify=False)
            print '_' * 80
            print '>>> Mark reference stars with "a". Then "q"'
            print '-' * 80
            iraf.imexamine(img, 1, wcs='logical', logfile='tmp.log', keeplog=True)
            xyrefer = iraf.fields('tmp.log', '1,2,6,15', Stdout=1)
            xns, yns, _fws = [], [], []
            #############      write    file for PSF                           #########################
            ff = open('_psf.coo', 'w')
            for i in range(len(xyrefer)):
                xns.append(float(xyrefer[i].split()[0]))
                yns.append(float(xyrefer[i].split()[1]))
                _fws.append(float(xyrefer[i].split()[3]))
                ff.write('%10.3f %10.3f %7.2f \n' % (xns[i], yns[i], float(_fws[i])))
            ff.close()
            fwhm = np.median(_fws)
        else:
            ############              run  sextractor                #####################################
            xs, ys, ran, decn, magbest, classstar, fluxrad, bkg = runsex(img, fwhm, threshold, scale)
            tot = np.compress(abs(np.array(fluxrad) * 1.6 - fwhm) / fwhm < .5, fluxrad)
            if len(tot) < 5:
                print 'warning: fwhm from sexractor different from fwhm computed during pre-reduction'
                print 'try using option --fwhm xxx'

            ff = open('tmp.cursor', 'w')
            image_hdu = fits.open(img + '.fits')
            for i in range(len(xs)):
                _xs = np.delete(xs, i)
                _ys = np.delete(ys, i)
                dist2 = np.sqrt((_xs - xs[i]) ** 2 + (_ys - ys[i]) ** 2)
                ###########           cut  star, not near other object    ##########################
                if abs(fluxrad[i] * 1.6 - fwhm) / fwhm < .5 and min(dist2) > distance * fwhm:
                    x1, x2 = int(xs[i] - fwhm * 3), int(xs[i] + fwhm * 3)
                    y1, y2 = int(ys[i] - fwhm * 3), int(ys[i] + fwhm * 3)
                    if x1 < 1: x1 = 1
                    if y1 < 1: y1 = 1
                    if x2 > int(xdim):
                        x2 = int(xdim)
                    if y2 > int(ydim):
                        y2 = int(ydim)
                    fmax = np.max(image_hdu[0].data[y1-1:y2, x1-1:x2])
                ##########       cut saturated object               ########################
                    if float(fmax) < _datamax:  # not saturated
                        ff.write('%10.3f %10.3f 1 m \n' % (xs[i], ys[i]))
            ff.close()
            image_hdu.close()

            iraf.delete('tmp.lo?,tmp.sta?,tmp.gk?', verify=False)
            iraf.psfmeasure(img+'[0]', imagecur='tmp.cursor', logfile='tmp.log', radius=int(fwhm), iter=3,
                            display=False, StdoutG='tmp.gki')

            ff = open('tmp.log')
            righe = ff.readlines()
            xn = [float(righe[3].split()[1])]
            yn = [float(righe[3].split()[2])]
            _fw = [float(righe[3].split()[4])]
            for r in righe[4:-2]:
                if len(r) > 0:
                    xn.append(float(r.split()[0]))
                    yn.append(float(r.split()[1]))
                    _fw.append(float(r.split()[3]))
            print 'FWHM: ', righe[-1].split()[-1]
            print 80 * "#"
            ######
            ##############            eliminate double object identification         ###########################
            xns, yns, _fws = [xn[0]], [yn[0]], [_fw[0]]
            for i in range(1, len(xn)):
                if abs(xn[i] - xn[i - 1]) > .2 and abs(yn[i] - yn[i - 1]) > .2:
                    xns.append(xn[i])
                    yns.append(yn[i])
                    _fws.append(_fw[i])
            #########      write clean   file for PSF                           #########################
            fw = []
            ff = open('_psf.coo', 'w')
            for i in range(len(xns)):
                if abs(_fws[i] - fwhm) / fwhm < .3:
                    ff.write('%10.3f %10.3f %7.2f \n' % (xns[i], yns[i], float(_fws[i])))
                    fw.append(_fws[i])
            ff.close()  ## End automatic selection
        ######################################################################################
        ###################        write file of object to store in  fits table  #############
        ######################################################################################
        if _catalog:
            ddd=iraf.wcsctran(input=_catalog,output='STDOUT',Stdout=1,image=img + '[0]',inwcs='world',outwcs='logical',
                              units='degrees degrees',columns='1 2',formats='%10.1f %10.1f',verbose='no')
            ddd=[i for i in ddd if i[0]!='#']
            ddd=['  '.join(i.split()[0:3]) for i in ddd]
            ff = open('_psf2.coo', 'w')
            for i in ddd:
                a,b,c = string.split(i)
                ff.write('%10s %10s %10s \n' % (a, b, c))
            ff.close()
        elif interactive:
            xs, ys, ran, decn, magbest, classstar, fluxrad, bkg = runsex(img, fwhm, threshold, scale)
            ff = open('_psf2.coo', 'w')
            for i in range(len(xs)):
                ff.write('%10s %10s %10s \n' % (xs[i], ys[i], fluxrad[i]))
            ff.close()
        else:
            os.system('cp _psf.coo _psf2.coo')
#            dflux = fluxrad - np.median(fluxrad)
#            fstar = np.compress(dflux < np.std(fluxrad), fluxrad)
#################################################################################################################

        print 80 * "#"
        photmag, pst, fitmag = psffit(img, fwhm, psfstars, hdr, interactive, _datamax, psffun, fixaperture)

        photmag2, fitmag2 = psffit2(img, fwhm, psfstars, hdr, _datamax, psffun, fixaperture)

        radec = iraf.wcsctran(input='STDIN', output='STDOUT', Stdin=photmag,
                              Stdout=1, image=img + '[0]', inwcs='logical', outwcs='world', columns="1 2",
                              format='%13.3H %12.2h', min_sig=9, mode='h')[3:]

        radec2 = iraf.wcsctran(input='STDIN', output='STDOUT', Stdin=photmag2,
                               Stdout=1, image=img + '[0]', inwcs='logical', outwcs='world', columns="1 2",
                               format='%13.3H %12.2h', min_sig=9, mode='h')[3:]

        if interactive or show:
            iraf.set(stdimage='imt1024')
            iraf.display(img + '[0]', 1, fill=True, Stdout=1)
            iraf.tvmark(1, coords='STDIN', mark='circle', radii=15, label=True, Stdin=photmag, nxoffset=5, nyoffset=5, txsize=2)
            iraf.tvmark(1, coords='STDIN', mark='circle', radii=35, label=False, Stdin=pst, color=208)
#            iraf.tvmark(1, coords='STDIN', mark='cross', length=35, label=False, Stdin=fitmag2, color=204)

        idpsf = []
        for i in range(len(pst)):
            idpsf.append(pst[i].split()[2])
        dmag = []
        for i in range(len(radec)):
            ra, dec, idph, magp2, magp3, magp4, merrp2, merrp3, merrp4 = radec[i].split()
            dmag.append(9.99)
            for j in range(len(fitmag)):
                raf, decf, idf, magf, magerrf = fitmag[j].split()
                if idph == idf and idph in idpsf and \
                                magp3 != 'INDEF' and magf != 'INDEF':
                    dmag[i] = float(magp3) - float(magf)
                    break

        _dmag = np.compress(np.array(dmag) < 9.99, np.array(dmag))

        print '>>> Aperture correction (phot)   %6.3f +/- %5.3f %3d ' % \
              (np.mean(_dmag), np.std(_dmag), len(_dmag))
        if len(_dmag) > 3:
            _dmag = np.compress(np.abs(_dmag - np.median(_dmag)) < 2 * np.std(_dmag), _dmag)
            print '>>>         2 sigma rejection)   %6.3f +/- %5.3f %3d  [default]' \
                  % (np.mean(_dmag), np.std(_dmag), len(_dmag))
            print '>>>     fwhm   %s  ' % (str(fwhm))
        for i in range(len(dmag)):
            if dmag[i] == 9.99:
                dmag[i] = ''
            else:
                dmag[i] = '%6.3f' % (dmag[i])

        exptime = lsc.util.readkey3(hdr, 'exptime')
        object = lsc.util.readkey3(hdr, 'object').replace(' ', '')
        filtro = lsc.util.readkey3(hdr, 'filter')

        #######################################
        rap, decp, magp2, magp3, magp4, smagf, merrp3, smagerrf = [], [], [], [], [], [], [], []
        rap0, decp0 = [], []
        for i in range(len(radec2)):
            aa = radec2[i].split()
            rap.append(aa[0])
            decp.append(aa[1])
            rap0.append(lsc.lscabsphotdef.deg2HMS(ra=aa[0]))
            decp0.append(lsc.lscabsphotdef.deg2HMS(dec=aa[1]))
            idp = aa[2]
            magp2.append(aa[3])
            magp3.append(aa[4])
            magp4.append(aa[5])
            merrp3.append(aa[7])
            _smagf, _smagerrf = 9999, 9999
            for j in range(len(fitmag2)):
                raf, decf, idf, magf, magerrf = fitmag2[j].split()
                if idf == idp:
                    _smagf = magf
                    _smagerrf = magerrf
                    break
            smagf.append(_smagf)
            smagerrf.append(_smagerrf)
        tbhdu = fits.BinTableHDU.from_columns(fits.ColDefs([fits.Column(name='ra', format='20A', array=np.array(rap)),
                                               fits.Column(name='dec', format='20A', array=np.array(decp)),
                                               fits.Column(name='ra0', format='E', array=np.array(rap0)),
                                               fits.Column(name='dec0', format='E', array=np.array(decp0)),
                                               fits.Column(name='magp2', format='E',
                                                           array=np.array(np.where((np.array(magp2) != 'INDEF'),
                                                                                   np.array(magp2), 9999), float)),
                                               fits.Column(name='magp3', format='E',
                                                               array=np.array(np.where((np.array(magp3) != 'INDEF'),
                                                                                       np.array(magp3), 9999), float)),
                                               fits.Column(name='merrp3', format='E',
                                                               array=np.array(np.where((np.array(merrp3) != 'INDEF'),
                                                                                       np.array(merrp3), 9999), float)),
                                               fits.Column(name='magp4', format='E',
                                                               array=np.array(np.where((np.array(magp4) != 'INDEF'),
                                                                                       np.array(magp4), 9999), float)),
                                               fits.Column(name='smagf', format='E',
                                                               array=np.array(np.where((np.array(smagf) != 'INDEF'),
                                                                                       np.array(smagf), 9999), float)),
                                               fits.Column(name='smagerrf', format='E',
                                                               array=np.array(np.where((np.array(smagerrf) != 'INDEF'),
                                                                                       np.array(smagerrf), 9999),
                                                                              float)),
        ]))

        hdu = fits.PrimaryHDU(header=hdr)
        thdulist = fits.HDUList([hdu, tbhdu])
        lsc.util.delete(img + '.sn2.fits')
        thdulist.writeto(img + '.sn2.fits')
        lsc.util.updateheader(img + '.sn2.fits', 0, {'APCO': [np.mean(_dmag), 'Aperture correction']})
        lsc.util.updateheader(img + '.sn2.fits', 0, {'APCOERR': [np.std(_dmag), 'Aperture correction error']})
        lsc.util.updateheader(img + '.sn2.fits', 0, {'XDIM': [lsc.util.readkey3(hdr, 'naxis1'), 'x number of pixels']})
        lsc.util.updateheader(img + '.sn2.fits', 0, {'YDIM': [lsc.util.readkey3(hdr, 'naxis2'), 'y number of pixels']})
        lsc.util.updateheader(img + '.sn2.fits', 0,
                              {'PSF_FWHM': [fwhm * scale, 'FWHM (arcsec) - computed with daophot']})
        os.chmod(img + '.sn2.fits', 0664)
        os.chmod(img + '.psf.fits', 0664)
        result = 1

    except:
        result = 0
        fwhm = 0.0
        traceback.print_exc()
    return result, fwhm * scale

###########################################################################
if __name__ == "__main__":
    start_time = time.time()
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-f", "--fwhm", dest="fwhm", default='', help='starting FWHM  \t\t\t %default')
    parser.add_option("-t", "--threshold", dest="threshold", default=10., type='float',
                      help='Source detection threshold \t\t\t %default')
    parser.add_option("-p", "--psfstars", dest="psfstars", default=6, type='int',
                      help='Maximum number of psf stars \t\t\t %default')
    parser.add_option("-d", "--distance", dest="distance", default=5,
                      type='int', help='Minimum star separation (in unit of FWHM) \t\t %default')
    parser.add_option("--function", dest="psffun", default='gauss', type='str',
                      help='psf function (gauss,auto,moffat15,moffat25,penny1,penny2,lorentz) \t\t %default')
    parser.add_option("-r", "--redo", action="store_true", dest='redo', default=False,
                      help='Re-do \t\t\t\t [%default]')
    parser.add_option("-i", "--interactive", action="store_true", dest='interactive', default=False,
                      help='Interactive \t\t\t [%default]')
    parser.add_option("-s", "--show", dest="show", action='store_true',
                      default=False, help='Show PSF output \t\t [%default]')
    parser.add_option("-X", "--xwindow", action="store_true", dest='xwindow', default=False,
                      help='xwindow \t\t\t [%default]')
    parser.add_option("--use-sextractor", action="store_true", help="use souces from sextractor instead of catalog")
    parser.add_option("-c", "--catalog", dest="catalog", default='', type='str',
                      help='use input catalog  \t\t %default')
    parser.add_option("--fix", action="store_true", dest='fixaperture', default=False,
                      help='fixaperture \t\t\t [%default]')
    parser.add_option("--datamax", type=int,
                      help="value above which pixels are considered saturated (default = SATURATE in header)")

    option, args = parser.parse_args()
    if len(args) < 1: 
        sys.argv.append('--help')
    option, args = parser.parse_args()
    imglist = lsc.util.readlist(args[0])
    _xwindow = option.xwindow
    _catalog = option.catalog
    fixaperture = option.fixaperture
    psffun = option.psffun
    if psffun not in ['gauss', 'auto', 'lorentz', 'moffat15', 'moffat25', 'penny1', 'penny2']:
        sys.argv.append('--help')
    option, args = parser.parse_args()

    if _xwindow:
        from stsci.tools import capable

        capable.OF_GRAPHICS = False

    for img in imglist:
        if not option.use_sextractor and not _catalog:
            for system in ['sloan', 'apass', 'landolt']:
                _catalog = lsc.util.getcatalog(img, system)
                if _catalog:
                    break
        if '.fits' in img: img = img[:-5]
        if os.path.exists(img + '.sn2.fits') and not option.redo:
            print img + ': psf already calculated'
        else:
            fwhm0 = option.fwhm
            while True:
                result, fwhm = ecpsf(img, fwhm0, option.threshold, option.psfstars,
                                     option.distance, option.interactive, psffun,
                                     fixaperture, _catalog, option.datamax, option.show)
                print '\n### ' + str(result)
                if option.show:
#                    lsc.util.marksn2(img + '.fits', img + '.sn2.fits', 1, '')
                    iraf.delete('tmp.psf.fit?', verify=False)
                    iraf.seepsf(img + '.psf', '_psf.psf')
                    iraf.surface('_psf.psf')
                    aa = raw_input('>>>good psf [[y]/n] ? ')
                    if not aa or aa.lower()[0] == 'y':
                        break
                    if aa.lower()[0] == 'n':
                        result = 0
                        bb = raw_input('If you want to try again, type the new FWHM to try here. Otherwise press enter to continue. ')
                        if bb: fwhm0 = float(bb)
                        else: break
                else: 
                    break

            iraf.delete("tmp.*", verify="no")
            iraf.delete("_psf.*", verify="no")
            print  "********** Completed in ", int(time.time() - start_time), "sec"
            print result
            try:
                if result == 1:
                    lsc.mysqldef.updatevalue('photlco', 'psf', string.split(img, '/')[-1] + '.psf.fits',
                                             string.split(img, '/')[-1] + '.fits')
                    lsc.mysqldef.updatevalue('photlco', 'fwhm', fwhm, string.split(img, '/')[-1] + '.fits')
                    lsc.mysqldef.updatevalue('photlco', 'mag', 9999, string.split(img, '/')[-1] + '.fits')
                    lsc.mysqldef.updatevalue('photlco', 'psfmag', 9999, string.split(img, '/')[-1] + '.fits')
                    lsc.mysqldef.updatevalue('photlco', 'apmag', 9999, string.split(img, '/')[-1] + '.fits')
                    if os.path.isfile(img + '.diff.fits') and os.path.isfile(img + '.sn2.fits'):
                        # update diff info is file available
                        os.system('cp ' + img + '.sn2.fits ' + img + '.diff.sn2.fits')
                        lsc.mysqldef.updatevalue('photlco', 'psf', string.split(img, '/')[-1] + '.psf.fits',
                                                 string.split(img, '/')[-1] + '.diff.fits')
                        lsc.mysqldef.updatevalue('photlco', 'fwhm', fwhm, string.split(img, '/')[-1] + '.diff.fits')
                        lsc.mysqldef.updatevalue('photlco', 'mag', 9999, string.split(img, '/')[-1] + '.diff.fits')
                        lsc.mysqldef.updatevalue('photlco', 'psfmag', 9999, string.split(img, '/')[-1] + '.diff.fits')
                        lsc.mysqldef.updatevalue('photlco', 'apmag', 9999, string.split(img, '/')[-1] + '.diff.fits')
                else:
                    print 'psf not good, database not updated '
                    lsc.mysqldef.updatevalue('photlco', 'psf', 'X', string.split(img, '/')[-1] + '.fits')
                    if os.path.isfile(img + '.diff.fits'):
                        lsc.mysqldef.updatevalue('photlco', 'psf', 'X', string.split(img, '/')[-1] + '.diff.fits')
            except:
                print 'module mysqldef not found'

