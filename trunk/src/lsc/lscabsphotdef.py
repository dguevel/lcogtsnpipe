from scipy.optimize import fsolve # root
from astropy.io import fits
import numpy as np
from scipy import stats, odr
import matplotlib.pyplot as plt
import warnings
import lsc
with warnings.catch_warnings(): # so cronic doesn't email on the "experimental" warning
    warnings.simplefilter('ignore')
    from astroquery.sdss import SDSS

def limmag(img, zeropoint=0, Nsigma_limit=3, _fwhm = 5):
    image = fits.open(img)
    hdr = image[0].header
    data = image[0].data
    #_sky = np.median(data)
    _skynoise = 1.4826 * np.median(np.abs(data - np.median(data)))
    _exptime = lsc.util.readkey3(hdr, 'exptime')
    _gain = lsc.util.readkey3(hdr, 'gain')
    _readnoise = lsc.util.readkey3(hdr, 'ron')
    _pixelscale = lsc.util.readkey3(hdr, 'pixscale')
    _radius = float(_fwhm) / float(_pixelscale)
    if _radius and _gain and _skynoise:
        print _skynoise, _gain, _radius
        #    mag = calc_limit_mag(Nsigma_limit, _sky, _gain, _readnoise, _exptime, zeropoint, _radius)
        limit_counts = fsolve(snr_helper, np.median(data), args = [Nsigma_limit, _readnoise, _gain, _skynoise,_radius])[0]
        mag = -2.5 * np.log10(limit_counts / _exptime) + zeropoint
    else:
        mag = 9999
    return mag

def snr_equation(counts, Nsigma_limit, rdnoise, gain, skynoise,radius):
    """
    Invert the signal to noise equation and compare to the limiting number of sigma.
    :param counts: Source Counts in ADU
    :param Nsigma_limit: Number of sigma limit (e.g. 5-sigma limit)
    :param rdnoise: Read noise in electrons
    :param gain: Gain (electrons / ADU)
    :param sky: Sky value in ADU (likely the median of an image)
    :return: Signal / Noise difference from the limiting sigma
    """
    area = np.pi * radius**2 
    snr = counts * gain - Nsigma_limit * (counts * gain + skynoise**2.0 * gain*area + rdnoise * rdnoise*area) ** 0.5
    return snr

def snr_helper(counts, extra):
    """
    Helper function to interface with scipy.optimize.root
    :param counts: Object counts for the S/N calculation
    :param extra: Other parameters to pass to the snr function
    :return: Signal / Noise difference from the limiting sigma
    """
    return snr_equation(counts, *extra)

#def calc_limit_mag(Nsigma_limit, sky, gain, readnoise, exptime, zeropoint,radius):
#    """
#    Calculate a limiting magnitude of an image
#    :param Nsigma_limit: Number of sigma limit (e.g. 5-sigma limit)
#    :param sky: sky value in ADU (like the median of an image)
#    :param gain: Gain (electrons / ADU)
#    :param readnoise: Read Noise in electrons
#    :param exptime: Exposure time in seconds
#    :param zeropoint: Zeropoint magnitude where mag = -2.5 log( counts / exptime) + zp
#    :return: limiting magnitude
#    """
#    limit_counts = root(snr_helper, sky, args = [Nsigma_limit, readnoise, gain, sky])
#    return mag[0]

def deg2HMS(ra='', dec='', round=False):
      import string
      RA, DEC= '', ''
      if dec:
          if string.count(str(dec),':')==2:
              dec00=string.split(dec,':')
              dec0,dec1,dec2=float(dec00[0]),float(dec00[1]),float(dec00[2])
              if '-' in str(dec0):       DEC=(-1)*((dec2/60.+dec1)/60.+((-1)*dec0))
              else:                      DEC=(dec2/60.+dec1)/60.+dec0
          else:
              if str(dec)[0]=='-':      dec0=(-1)*abs(int(dec))
              else:                     dec0=abs(int(dec))
              dec1=int((abs(dec)-abs(dec0))*(60))
              dec2=((((abs(dec))-abs(dec0))*60)-abs(dec1))*60
              DEC='00'[len(str(dec0)):]+str(dec0)+':'+'00'[len(str(dec1)):]+str(dec1)+':'+'00'[len(str(int(dec2))):]+str(dec2)
      if ra:
          if string.count(str(ra),':')==2:
              ra00=string.split(ra,':')
              ra0,ra1,ra2=float(ra00[0]),float(ra00[1]),float(ra00[2])
              RA=((ra2/60.+ra1)/60.+ra0)*15.
          else:
              ra0=int(ra/15.)
              ra1=int(((ra/15.)-ra0)*(60))
              ra2=((((ra/15.)-ra0)*60)-ra1)*60
              RA='00'[len(str(ra0)):]+str(ra0)+':'+'00'[len(str(ra1)):]+str(ra1)+':'+'00'[len(str(int(ra2))):]+str(ra2)
      if ra and dec:          return RA, DEC
      else:                   return RA or DEC

def onkeypress(event):
    import matplotlib.pyplot as plt
    from numpy import polyfit,polyval,argmin,sqrt,mean,array,std,median
    global idd,_col,_dmag,testo,lines,sss,f,fixcol,aa,bb,sigmaa,sigmab
    xdata,ydata = event.xdata,event.ydata
    dist = sqrt((xdata-_col)**2+(ydata-_dmag)**2)
    ii = argmin(dist)
    if event.key == 'd' :
        __col,__dmag = _col.tolist(),_dmag.tolist()
        plt.plot(_col[ii],_dmag[ii],'xk',ms=25)
        del __col[ii],__dmag[ii]
        _col,_dmag = array(__col),array(__dmag)

    idd = range(len(_col))
    _fixcol=fixcol
    if len(_col[idd])==1:  _fixcol=0.0
    else:   _fixcol=fixcol

    if _fixcol=='':
        pol = polyfit(_col,_dmag,1,full=True)  ###
        aa = pol[0][1]
        bb = pol[0][0]
        if len(_col[idd])>2:
            sigmae = sqrt(pol[1][0]/(len(idd)  -2))
            sigmaa = sigmae*sqrt(1./len(idd)+(mean(_col[idd])**2)/sum((_col[idd]-\
                                                                           mean(_col[idd]))**2))
            sigmab = sigmae*sqrt(1/sum((_col[idd]-mean(_col[idd]))**2))
        else:
            sigmaa=0.0
            sigmab=0.0
    else:
#        aa=mean(array(_dmag[idd])-array(_col[idd])*float(_fixcol))
        aa=median(array(_dmag[idd])-array(_col[idd])*float(_fixcol))
        bb=_fixcol
        sigmaa=std(abs(aa-(array(_dmag[idd])-array(_col[idd])*float(_fixcol))))
        sigmab=0.0

    xx = [min(_col)-.1,max(_col)+.1]
    yy = polyval([bb,aa],xx)                ###
    lines.pop(0).remove()
    lines = plt.plot(xx,yy,'r-')
    plt.ylim(min(_dmag)-.2,max(_dmag)+.2)
    plt.xlabel(sss)
    plt.title(f)

    try:
        plt.setp(testo,text='%5.3f + %s* %5.3f [%4.3f  %4.3f]'%\
                     (aa,sss,bb,sigmaa,sigmab))
    except:
        plt.setp(testo,text='%5.3f + %s* %5.3f [%4.3f  %4.3f]'%\
                     (aa,sss,bb,sigmaa,sigmab))

def onclick(event):
    import matplotlib.pyplot as plt
    from numpy import polyfit,polyval,argmin,sqrt,mean,array,std,median
    global idd,_col,_dmag,testo,lines,aa,bb,sss,f,fixcol,sigmaa,sigmab
    xdata,ydata = event.xdata,event.ydata
    dist = sqrt((xdata-_col)**2+(ydata-_dmag)**2)
    ii = argmin(dist)
    if event.button == 2:
        if ii not in idd: idd.append(ii)
    if event.button == 1:  
        if ii in idd: idd.remove(ii)

    nonincl = []
    for i in range(len(_col)):
        if i not in idd: nonincl.append(i)

#    _fixcol=fixcol
    if len(_col[idd])==1:  _fixcol=0.0
    else:   _fixcol=fixcol

    if _fixcol=='':
        pol = polyfit(_col[idd],_dmag[idd],1,full=True) ###
        aa=pol[0][1]
        bb=pol[0][0]
        if len(idd)>2:
            sigmae = sqrt(pol[1][0]/(len(idd)  -2))
            sigmaa = sigmae*sqrt(1./len(idd)+(mean(_col[idd])**2)/sum((_col[idd]-\
                                                                           mean(_col[idd]))**2))
            sigmab = sigmae*sqrt(1/sum((_col[idd]-mean(_col[idd]))**2))
        else:
            sigmaa=0.0
            sigmab=0.0
    else:
#        aa=mean(_dmag[idd]-_col[idd]*float(_fixcol))
        aa=median(_dmag[idd]-_col[idd]*float(_fixcol))
        bb=_fixcol
        sigmaa=std(abs(aa-(array(_dmag[idd])-array(_col[idd])*float(_fixcol))))
        sigmab=0.0

    xx = [min(_col)-.1,max(_col)+.1]
    yy = polyval([bb,aa],xx)                ###

    plt.plot(_col,_dmag,'ok')
    plt.plot(_col[nonincl],_dmag[nonincl],'ow')
    lines.pop(0).remove()
    lines = plt.plot(xx,yy,'r-')
    plt.ylim(min(_dmag)-.2,max(_dmag)+.2)
    plt.xlabel(sss)
    plt.title(f)
    try:
        plt.setp(testo,text='%5.3f + %s* %5.3f [%4.3f  %4.3f]'%\
                     (aa,sss,bb,sigmaa,sigmab))
    except:
        plt.setp(testo,text='%5.3f + %s* %5.3f [%4.3f  %4,3f]'%\
                     (aa,sss,bb,sigmaa,sigmab))


def absphot(img,_field,_catalogue,_fix,_color,rejection,_interactive,_type='fit',redo=False,show=False,cutmag=-1,database='photlco',_calib='sloan',zcatnew=False):
    from astropy.io import fits
    import math
    import sys,re,string,os
    from lsc.util import readkey3, readhdr
    from numpy import array, compress, zeros, median, std, asarray, isfinite,mean
    from pyraf import iraf

    iraf.noao(_doprint=0)
    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    iraf.images(_doprint=0)
    iraf.imcoords(_doprint=0)
    iraf.proto(_doprint=0)
    t = fits.open(img)
    tbdata = t[1].data
    hdr2=t[1].header
    hdr=lsc.util.readhdr(img)
    _cat=readkey3(hdr,'catalog')
    _telescope=lsc.util.readkey3(hdr,'telescop')
    _instrume=lsc.util.readkey3(hdr,'instrume')
    _filter=lsc.util.readkey3(hdr,'filter')
    _airmass=lsc.util.readkey3(hdr,'airmass')
    _exptime=lsc.util.readkey3(hdr,'exptime')
    _date=lsc.util.readkey3(hdr,'date-obs')
    _object=lsc.util.readkey3(hdr,'object')
    _fwhm = lsc.util.readkey3(hdr,'PSF_FWHM')
    _ra=lsc.util.readkey3(hdr,'RA')
    _dec=lsc.util.readkey3(hdr,'DEC')
    _siteid = hdr['SITEID']
    if _siteid in lsc.sites.extinction:
        kk = lsc.sites.extinction[_siteid]
    else:
        print _siteid
        sys.exit('siteid not in lsc.sites.extinction')

    if _calib=='apass': _field='apass'
    if _field=='apass': _calib='apass'
    if _calib=='apass' and not _catalogue: sys.exit('ERROR: apass option for field or calib is valid only when apass catalogue is also provided')

    if _calib == 'sloanprime' and ('fs' in _instrume or 'em' in _instrume):
        colorefisso = {'UUB':0.0,'uug':0.0,'BUB':0.0,'BBV':0.0,'VBV':0.0,'VVR':0.0,\
                      'gug':0.0,'ggr':0.0,'RVR':0.0,'RRI':0.0,'rrz':0.0,'zrz':0.0,\
                      'rgr':0.0,'rri':0.0,'iri':0.027,'iiz':0.0,'IRI':0.0,'ziz':0.0}
    elif _calib == 'sloanprime':
        colorefisso = {'UUB':0.059,'uug':0.0,'BUB':-0.095,'BBV':0.06,'VBV':0.03,'VVR':-0.059,\
                      'gug':0.13,'ggr':0.054,'RVR':-0.028,'RRI':-0.033,'rrz':0.0,'zrz':0.0,'ggi':0.0,'igi':0.0,\
                      'rgr':0.003,'rri':-0.007,'iri':0.028,'iiz':0.110,'IRI':0.013,'ziz':-0.16}
    elif _calib == 'natural':
        colorefisso = {'UUB':0.0,'uug':0.0,'BUB':0.0,'BBV':0.0,'VBV':0.0,'VVR':0.0,\
                      'gug':0.0,'ggr':0.0,'RVR':0.0,'RRI':0.0,'rrz':0.0,'zrz':0.0,\
                      'rgr':0.0,'rri':0.0,'iri':0.0,'iiz':0.0,'IRI':0.0,'ziz':0.0}
    elif 'fs' in _instrume or 'em' in _instrume:
        colorefisso = {'UUB':0.0,'uug':0.0,'BUB':0.0,'BBV':0.0,'VBV':0.0,'VVR':0.0,\
                      'gug':0.0,'ggr':0.105,'RVR':0.0,'RRI':0.0,'rrz':0.0,'zrz':0.0,\
                      'rgr':0.013,'rri':0.029,'iri':0.0874,'iiz':0.0,'IRI':0.0,'ziz':-0.15}
    # BVgri color terms from Valenti et al. 2016, MNRAS, 459, 3939
    elif 'fl' in _instrume:
        colorefisso = {'uug': 0.0, 'ggr': 0.109, 'rri': 0.027, 'iri': 0.036, 'BBV': -0.024, 'VBV': -0.014,
                       'UUB': 0.059, 'BUB': -0.095, 'VVR': -0.059, 'RVR': -0.028, 'RRI': -0.033, 'IRI': 0.013, 'ziz': -0.04}
    elif _siteid == 'coj':
        colorefisso = {'uug': 0.0, 'ggr': 0.137, 'rri': -0.005, 'iri': 0.007, 'BBV': -0.025, 'VBV': 0.017, 'UUB':0.059,
                       'UUB': 0.059, 'BUB': -0.095, 'VVR': -0.059, 'RVR': -0.028, 'RRI': -0.033, 'IRI': 0.013, 'ziz': -0.04}
    elif _siteid == 'lsc':
        colorefisso = {'uug': 0.0, 'ggr': 0.120, 'rri': -0.002, 'iri': 0.019, 'BBV': -0.035, 'VBV': 0.000, 'UUB':0.059,
                       'UUB': 0.059, 'BUB': -0.095, 'VVR': -0.059, 'RVR': -0.028, 'RRI': -0.033, 'IRI': 0.013, 'ziz': -0.04}
    elif _siteid == 'elp':
        colorefisso = {'uug': 0.0, 'ggr': 0.114, 'rri': -0.004, 'iri': 0.024, 'BBV': -0.039, 'VBV': -0.005, 'UUB':0.059,
                       'UUB': 0.059, 'BUB': -0.095, 'VVR': -0.059, 'RVR': -0.028, 'RRI': -0.033, 'IRI': 0.013, 'ziz': -0.04}
    elif _siteid == 'cpt':
        colorefisso = {'uug': 0.0, 'ggr': 0.112, 'rri': -0.001, 'iri': 0.013, 'BBV': -0.030, 'VBV': -0.019, 'UUB':0.059,
                       'UUB': 0.059, 'BUB': -0.095, 'VVR': -0.059, 'RVR': -0.028, 'RRI': -0.033, 'IRI': 0.013, 'ziz': -0.04}
    elif _siteid == 'tfn': # average of other SBIGs
        colorefisso = {'uug': 0.0, 'ggr': 0.121, 'rri': -0.003, 'iri': 0.016, 'BBV': -0.032, 'VBV': -0.002, 'UUB':0.059,
                       'UUB': 0.059, 'BUB': -0.095, 'VVR': -0.059, 'RVR': -0.028, 'RRI': -0.033, 'IRI': 0.013, 'ziz': -0.04}
    else: # don't know where these came from
        colorefisso = {'uug': 0.0, 'gug': 0.13, 'ggr': -0.02, 'rgr': 0.034, 'rri': 0.025, 'iri': 0.071, 'iiz': 0.110, 'ziz': -0.04,
                       'UUB': 0.059, 'BUB': -0.095, 'BBV': 0.06, 'VBV': 0.03, 'VVR': -0.059, 'RVR': -0.028, 'RRI': -0.033, 'IRI': 0.013}

    if _cat and not redo:
        print 'already calibrated'
    else:
     try:
           lsc.mysqldef.updatevalue(database,'zcat','X',string.split(re.sub('.sn2.fits','.fits',img),'/')[-1])
           if os.path.isfile(string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1]):
                 lsc.mysqldef.updatevalue(database,'zcat','X',string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1])
     except: print 'module mysqldef not found'

     column=makecatalogue([img])[_filter][img]

     rasex=array(column['ra0'],float)
     decsex=array(column['dec0'],float)
     if _type=='fit':
        magsex=array(column['smagf'],float)
        magerrsex=array(column['smagerrf'],float)
     elif _type=='ph':
        magsex=array(column['magp3'],float)
        magerrsex=array(column['merrp3'],float)
     else: sys.exit(_type+' not valid (ph or fit)')
     

     if not cutmag: 
         cutmag=99

     if len(compress( array(magsex) < float(cutmag) , magsex)) < 5 : cutmag=99  # not cut if only few object
     rasex     = compress(array(magsex,float)<=cutmag,rasex)
     decsex    = compress(array(magsex,float)<=cutmag,decsex)
     magerrsex = compress(array(magsex,float)<=cutmag,magerrsex)
     magsex    = compress(array(magsex,float)<=cutmag,array(magsex))

     if _interactive:
        iraf.set(stdimage='imt1024')
        iraf.display(re.sub('.sn2','',img) + '[0]',1,fill=True,Stdout=1)
        vector=[]
        for i in range(0,len(rasex)):
            vector.append(str(rasex[i])+' '+str(decsex[i]))
        xy = iraf.wcsctran('STDIN',output="STDOUT",Stdin=vector,Stdout=1,image=img + '[0]',inwcs='world',units='degrees degrees',outwcs='logical',\
                               formats='%10.1f %10.1f',verbose='yes')[3:]
        iraf.tvmark(1,'STDIN',Stdin=list(xy),mark="circle",number='yes',label='no',radii=10,nxoffse=5,nyoffse=5,color=207,txsize=2)
        print 'yelow circles sextractor'
        
     if _catalogue:
        ######## use external catalogue
        if _catalogue[0]=='/':   stdcooC=lsc.lscastrodef.readtxt(_catalogue)
        else:                   stdcooC=lsc.lscastrodef.readtxt(lsc.__path__[0]+'/standard/cat/'+_catalogue)
        rastdC,decstdL=array(stdcooC['ra'],float),array(stdcooC['dec'],float)
        lsc.util.delete('tmp.stdL.pix')
        colonne=str(stdcooC['rapos'])+'   '+str(stdcooC['decpos'])
        if _catalogue[0]=='/': 
            iraf.wcsctran(_catalogue,'tmp.stdL.pix',img + '[0]',inwcs='world',units='degrees degrees',outwcs='logical',\
                          columns=colonne,formats='%10.1f %10.1f',verbose='no')
        else:
            iraf.wcsctran(lsc.__path__[0]+'/standard/cat/'+_catalogue,'tmp.stdL.pix',img + '[0]',inwcs='world',units='degrees degrees',outwcs='logical',\
                          columns=colonne,formats='%10.1f %10.1f',verbose='no')
        standardpixC=lsc.lscastrodef.readtxt('tmp.stdL.pix')
        if _interactive:
              vector=[k+' '+v for k,v in  zip(standardpixC['ra'],standardpixC['dec'])]
              iraf.tvmark(1,'STDIN',Stdin=list(vector),mark="circle",number='yes',label='no',radii=10,nxoffse=5,nyoffse=5,color=204,txsize=2)
              print 'yelow circles sextractor'

        xstdC=standardpixC['ra']
        ystdC=standardpixC['dec']
        idstdC=standardpixC['id']
        xstdC=compress((array(xstdC,float)<readkey3(hdr,'XDIM'))&(array(xstdC,float)>0)&(array(ystdC,float)>0)&(array(ystdC,float)<readkey3(hdr,'YDIM')),xstdC)
        xstdL=xstdLL=xstdS=xstdC
        standardpixL=standardpixLL=standardpixS=standardpixC
        stdcooL=stdcooLL=stdcooS=stdcooC
     else:
        ######## check if it is landolt field
        stdcooL=lsc.lscastrodef.readtxt(lsc.__path__[0]+'/standard/cat/landolt.cat')
        rastdL,decstdL=array(stdcooL['ra'],float),array(stdcooL['dec'],float)
        lsc.util.delete('tmp.stdL.pix')
        iraf.wcsctran(lsc.__path__[0]+'/standard/cat/landolt.cat','tmp.stdL.pix',img + '[0]',inwcs='world',units='degrees degrees',outwcs='logical',\
                          columns='1 2',formats='%10.1f %10.1f',verbose='no')
        standardpixL=lsc.lscastrodef.readtxt('tmp.stdL.pix')
        if _interactive:
              vector=[k+' '+v for k,v in  zip(standardpixL['ra'],standardpixL['dec'])]
              iraf.tvmark(1,'STDIN',Stdin=list(vector),mark="circle",number='yes',label='no',radii=10,nxoffse=5,nyoffse=5,color=204,txsize=2)
              #iraf.tvmark(1,'tmp.stdL.pix',mark="circle",number='yes',label='no',radii=8,nxoffse=5,nyoffse=5,color=204,txsize=2)
              print 'yelow circles sextractor'

        xstdL=standardpixL['ra']
        ystdL=standardpixL['dec']
        idstdL=standardpixL['id']
        xstdL=compress((array(xstdL,float)<readkey3(hdr,'XDIM'))&(array(xstdL,float)>0)&(array(ystdL,float)>0)&(array(ystdL,float)<readkey3(hdr,'YDIM')),xstdL)

        ######## check if it is Stetson field
        stdcooLL=lsc.lscastrodef.readtxt(lsc.__path__[0]+'/standard/cat/StetsonCat.dat')
        ww=asarray([i for i in range(len(stdcooLL['ra'])) if ( abs(float(stdcooLL['ra'][i])-float(_ra))<.2 and  abs(float(stdcooLL['dec'][i])-_dec)<.2    )])
        if len(ww)>0:
            for hh in stdcooLL.keys(): 
                if type(stdcooLL[hh])!=int:
                    if hh not in ['id','ra','dec']:
                        stdcooLL[hh]=array(array(stdcooLL[hh])[ww],float)
                    else:
                        stdcooLL[hh]=array(stdcooLL[hh])[ww]
        lll=[]
        for i in range(0,len(stdcooLL['ra'])): lll.append(stdcooLL['ra'][i]+' '+stdcooLL['dec'][i])

        rastdLL,decstdLL=array(stdcooLL['ra'],float),array(stdcooLL['dec'],float)
        lsc.util.delete('tmp.stdLL.pix')
        iraf.wcsctran('STDIN','tmp.stdLL.pix',img + '[0]',inwcs='world',Stdin=lll,units='degrees degrees',outwcs='logical',\
                          columns='1 2',formats='%10.1f %10.1f',verbose='no')

        standardpixLL={}
        for ii in stdcooLL.keys(): standardpixLL[ii]=stdcooLL[ii]
        standardpixLL['ra']=array(iraf.proto.fields('tmp.stdLL.pix',fields='1',Stdout=1),float) #standardpixLL['ra']
        standardpixLL['dec']=array(iraf.proto.fields('tmp.stdLL.pix',fields='2',Stdout=1),float) #standardpixLL['dec']
        xstdLL=array(iraf.proto.fields('tmp.stdLL.pix',fields='1',Stdout=1),float) #standardpixLL['ra']
        ystdLL=array(iraf.proto.fields('tmp.stdLL.pix',fields='2',Stdout=1),float) #standardpixLL['dec']
        idstdLL=standardpixLL['id']

        if _interactive:
              vector=[k+' '+v for k,v in  zip(standardpixLL['ra'],standardpixLL['dec'])]
              iraf.tvmark(1,'STDIN',Stdin=list(vector),mark="circle",number='yes',label='no',radii=10,nxoffse=5,nyoffse=5,color=204,txsize=2)
              #iraf.tvmark(1,'tmp.stdLL.pix',mark="cross",number='yes',label='no',radii=8,nxoffse=5,nyoffse=5,color=204,txsize=2)
              print 'red crosses Stetson'

        xstdLL=compress((array(xstdLL,float)<readkey3(hdr,'XDIM'))&(array(xstdLL,float)>0)&(array(ystdLL,float)>0)&(array(ystdLL,float)<readkey3(hdr,'YDIM')),xstdLL)
        ######## check if it is sloan field
        magsel0,magsel1=12,18
        _ids=lsc.lscastrodef.sloan2file(_ra,_dec,20,float(magsel0),float(magsel1),'_tmpsloan.cat')
        ascifile='_tmpsloan.cat'
        stdcooS=lsc.lscastrodef.readtxt(ascifile)
        rastdS,decstdS=array(stdcooS['ra'],float),array(stdcooS['dec'],float)
        lsc.util.delete('tmp.stdS.pix')
        iraf.wcsctran(ascifile,'tmp.stdS.pix',img + '[0]',inwcs='world',units='degrees degrees',outwcs='logical',columns='1 2',formats='%10.1f %10.1f',verbose='no')
        standardpixS=lsc.lscastrodef.readtxt('tmp.stdS.pix')
        if _interactive:
              vector=[k+' '+v for k,v in  zip(standardpixS['ra'],standardpixS['dec'])]
              iraf.tvmark(1,'STDIN',Stdin=list(vector),mark="circle",number='yes',label='no',radii=10,nxoffse=5,nyoffse=5,color=204,txsize=2)
              print 'green cross sloan'

        xstdS=standardpixS['ra']
        ystdS=standardpixS['dec']
        idstdS=standardpixS['id']
        xstdS=compress((array(xstdS,float)<readkey3(hdr,'XDIM'))&(array(xstdS,float)>0)&(array(ystdS,float)>0)&(array(ystdS,float)<readkey3(hdr,'YDIM')),xstdS)
        ##############################################3
     if not _catalogue and len(xstdLL)>0:
             xstdL=xstdLL
             standardpixL=standardpixLL
             stdcooL=stdcooLL

     if _calib=='apass':
           filters={'ip':'i','gp':'g','rp':'r','SDSS-G':'g','SDSS-R':'r','SDSS-I':'i','B':'B', 'V':'V', 'R':'R', 'I':'I','Bessell-B':'B','Bessell-V':'V'}
           if _color:
                 colors=lsc.myloopdef.chosecolor(_color,False,'apass')
                 if not colors:             colors={'B':['BV'],'V':['BV','Vg'],'g':['Vg','gr'],'r':['gr','ri'],'i':['ri']}
           else:
                 colors={'B':['BV'],'V':['BV','Vg'],'g':['Vg','gr'],'r':['gr','ri'],'i':['ri']}
           standardpix=standardpixL
           stdcoo=stdcooL
     else:
       if _filter in ['U', 'B', 'V', 'R','I','Bessell-B','Bessell-V','Bessell-R','Bessell-I']:
        filters={'U':'U', 'B':'B', 'V':'V', 'R':'R', 'I':'I','Bessell-B':'B','Bessell-V':'V','Bessell-R':'R','Bessell-I':'I'}
        if _color:
            colors=lsc.myloopdef.chosecolor(_color,False)
            if not colors:             colors={'U':['UB'],'B':['UB','BV'],'V':['BV','VR'],'R':['VR','RI'],'I':['RI']}
        else:
            colors={'U':['UB'],'B':['UB','BV'],'V':['BV','VR'],'R':['VR','RI'],'I':['RI']}
        if _field=='sloan':
                standardpix,stdcoo={'ra':[9999],'dec':[9999],'id':[1]},{'ra':[9999],'dec':[9999]}
                print 'filters and field selected do not match'
        else:
            _field='landolt'
            if len(xstdL)>=1:
                    standardpix=standardpixL
                    stdcoo=stdcooL
                    if not _catalogue:
                          if len(xstdLL)>0: _catalogue='StetsonCat.dat'
                          else:             _catalogue='landolt.dat'
            elif len(xstdS)>=1:
                if not _catalogue:  _catalogue='sdss8'  
                standardpix=standardpixS
                stdcoo=stdcooS
                stdcoo=lsc.lscastrodef.transformsloanlandolt(stdcoo)
                if not _catalogue:  _catalogue='sdss8' 
                print '\n### transform sloan in landolt'
            else:
                print 'landolt, but catalogue not found'
                standardpix,stdcoo={'ra':[9999],'dec':[9999],'id':[1]},{'ra':[9999],'dec':[9999]}
       elif _filter in  ['up','gp','rp','ip','zs','SDSS-G','SDSS-R','SDSS-I','Pan-Starrs-Z']: 
        filters={'up':'u','ip':'i','gp':'g','rp':'r','zs':'z','SDSS-G':'g','SDSS-R':'r','SDSS-I':'i','Pan-Starrs-Z':'z'}
        if _color:
            colors=lsc.myloopdef.chosecolor(_color,False)
            if not colors:             colors={'i':['ri','iz'],'r':['gr','ri'],'g':['ug','gr'],'z':['iz'],'u':['ug']}
        else:
#            colors={'i':['ri','iz'],'r':['gr','ri'],'g':['ug','gr'],'z':['iz'],'u':['ug']}
            colors={'i':['ri'],'r':['gr','ri'],'g':['ug','gr'],'z':['iz'],'u':['ug']}
        if _field=='landolt':   
                standardpix,stdcoo={'ra':[9999],'dec':[9999],'id':[1]},{'ra':[9999],'dec':[9999]}
                print 'filters and field selected do not match'
        else:
            _field='sloan'
            if len(xstdS)>=1:
                if not _catalogue:  _catalogue='sdss8' 
                standardpix=standardpixS
                stdcoo=stdcooS
            elif len(xstdL)>=1:
                standardpix=standardpixL
                stdcoo=stdcooL
                stdcoo=lsc.lscastrodef.transformlandoltsloan(stdcoo)
                if not _catalogue:  _catalogue='landolt.dat' 
                print '\n### transform landolt to sloan'
            else:
                print 'sloan, but not in the sdss footprint'
                standardpix,stdcoo={'ra':[9999],'dec':[9999],'id':[1]},{'ra':[9999],'dec':[9999]}        

     xstd=standardpix['ra']
     ystd=standardpix['dec']
     idstd=standardpix['id']
     rastd,decstd=array(stdcoo['ra'],float),array(stdcoo['dec'],float)
     xstd0=compress((array(xstd,float)<readkey3(hdr,'XDIM'))&(array(xstd,float)>0)&(array(ystd,float)>0)&(array(ystd,float)<readkey3(hdr,'YDIM')),xstd)

     if len(xstd0)>1:  ########   go only if standard stars are in the field  ##########
        magstd0={}
        errstd0={}
        airmass0={}
        result={}
        fileph={}
        print '\n###  standard field: '+str(_field)
        ystd0=compress((array(xstd,float)<readkey3(hdr,'XDIM'))&(array(xstd,float)>0)&(array(ystd,float)>0)\
                               &(array(ystd,float)<readkey3(hdr,'YDIM')),ystd)
        rastd0=compress((array(xstd,float)<readkey3(hdr,'XDIM'))&(array(xstd,float)>0)&(array(ystd,float)>0)\
                                &(array(ystd,float)<readkey3(hdr,'YDIM')),rastd)
        decstd0=compress((array(xstd,float)<readkey3(hdr,'XDIM'))&(array(xstd,float)>0)&(array(ystd,float)>0)\
                                 &(array(ystd,float)<readkey3(hdr,'YDIM')),decstd)
        idstd0=compress((array(xstd,float)<readkey3(hdr,'XDIM'))&(array(xstd,float)>0)&(array(ystd,float)>0)\
                                 &(array(ystd,float)<readkey3(hdr,'YDIM')),idstd)
        stdcoo0={}
        for key in stdcoo.keys():
#              if key in 'ugrizUBVRI':
              if 'pos' not in key:
                    stdcoo0[key]=compress((array(xstd,float)<readkey3(hdr,'XDIM'))&(array(xstd,float)>0)&(array(ystd,float)>0)\
                                                &(array(ystd,float)<readkey3(hdr,'YDIM')),stdcoo[key])
        ###############################################################
        #               pos0 = standard                          pos1 = sextractor
        distvec,pos0,pos1=lsc.lscastrodef.crossmatch(array(rastd0),array(decstd0),array(rasex),array(decsex),5)
        for key in stdcoo0.keys():            stdcoo0[key]=stdcoo0[key][pos0]
        rastd0=rastd0[pos0]
        decstd0=decstd0[pos0]
        idstd0=idstd0[pos0]
        rasex=rasex[pos1]
        decsex=decsex[pos1]
        # after change in may 2013 mag in sn2.fits file are already at 1s
        magsex=magsex[pos1]-kk[filters[_filter]]*float(_airmass)  #   - K x airmass
        magerrsex = magerrsex[pos1]
#        magsex=magsex[pos1]+2.5*math.log10(float(_exptime))-kk[filters[_filter]]*float(_airmass)  #  mag    exptime      - K x airmass
#################################################################################
        if _field=='landolt':
            print '\n###  landolt system'
            for _filtlandolt in 'UBVRI':
                if _filtlandolt==filters[_filter]:  airmass0[_filtlandolt]=  0 #_airmass
                else: airmass0[_filtlandolt]= 0
                magstd0[_filtlandolt]=stdcoo0[_filtlandolt]
                errstd0[_filtlandolt]=stdcoo0[_filtlandolt+'err']
            fileph['mU']=zeros(len(rastd0))+999
            fileph['mB']=zeros(len(rastd0))+999
            fileph['mV']=zeros(len(rastd0))+999
            fileph['mR']=zeros(len(rastd0))+999
            fileph['mI']=zeros(len(rastd0))+999
            fileph['V']=magstd0['V']
            fileph['BV']=array(array(magstd0['B'],float)-array(magstd0['V'],float),str)
            fileph['UB']=array(array(magstd0['U'],float)-array(magstd0['B'],float),str)
            fileph['VR']=array(array(magstd0['V'],float)-array(magstd0['R'],float),str)
            fileph['RI']=array(array(magstd0['R'],float)-array(magstd0['I'],float),str)
        elif _field=='sloan':
            for _filtsloan in 'ugriz':
                if _filtsloan==filters[_filter]:  airmass0[_filtsloan]= 0   # _airmass
                else: airmass0[_filtsloan]=0
                magstd0[_filtsloan]=stdcoo0[_filtsloan]
                errstd0[_filtsloan]=stdcoo0[_filtsloan+'err']
            fileph['mu']=zeros(len(rastd0))+999
            fileph['mg']=zeros(len(rastd0))+999
            fileph['mr']=zeros(len(rastd0))+999
            fileph['mi']=zeros(len(rastd0))+999
            fileph['mz']=zeros(len(rastd0))+999
            fileph['r']=magstd0['r']
            fileph['gr']=array(array(magstd0['g'],float)-array(magstd0['r'],float),str)
            fileph['ri']=array(array(magstd0['r'],float)-array(magstd0['i'],float),str)
            fileph['ug']=array(array(magstd0['u'],float)-array(magstd0['g'],float),str)
            fileph['iz']=array(array(magstd0['i'],float)-array(magstd0['z'],float),str)
        elif _field=='apass':
            for _filtsloan in 'BVgri':
                if _filtsloan==filters[_filter]:  airmass0[_filtsloan]= 0   # _airmass
                else: airmass0[_filtsloan]=0
                magstd0[_filtsloan]=stdcoo0[_filtsloan]
                errstd0[_filtsloan]=stdcoo0[_filtsloan+'err']
            fileph['mB']=zeros(len(rastd0))+999
            fileph['mV']=zeros(len(rastd0))+999
            fileph['mg']=zeros(len(rastd0))+999
            fileph['mr']=zeros(len(rastd0))+999
            fileph['mi']=zeros(len(rastd0))+999
            fileph['V']=magstd0['V']
            fileph['BV']=array(array(magstd0['B'],float)-array(magstd0['V'],float),str)
            fileph['gr']=array(array(magstd0['g'],float)-array(magstd0['r'],float),str)
            fileph['ri']=array(array(magstd0['r'],float)-array(magstd0['i'],float),str)
            fileph['Vg']=array(array(magstd0['V'],float)-array(magstd0['g'],float),str)
########################################################################################
        zero=[]
        zeroerr = []
        magcor=[]
        fil = open(re.sub('.fits','.ph',img),'w')
        fil.write(str(_instrume)+' '+str(_date)+'\n')
        fil.write('*** '+_object+' '+str(len(magsex))+'\n')
        if _field=='landolt':
            fil.write('%6.6s\t%6.6s\t%6.6s\t%6.6s\t%6.6s\n' % (str(1),str(1),str(1),str(1),str(1)))  # exptime
            fil.write('%6.6s\t%6.6s\t%6.6s\t%6.6s\t%6.6s\n' % (str(airmass0['U']),str(airmass0['B']),str(airmass0['V']),str(airmass0['R']),str(airmass0['I'])))
        elif _field=='sloan':
            fil.write('%6.6s\t%6.6s\t%6.6s\t%6.6s\t%6.6s\n' % (str(1),str(1),str(1),str(1),str(1)))  # exptime
            fil.write('%6.6s\t%6.6s\t%6.6s\t%6.6s\t%6.6s\n' % (str(airmass0['u']),str(airmass0['g']),str(airmass0['r']),str(airmass0['i']),str(airmass0['z'])))
        elif _field=='apass':
            fil.write('%6.6s\t%6.6s\t%6.6s\t%6.6s\t%6.6s\n' % (str(1),str(1),str(1),str(1),str(1)))  # exptime
            fil.write('%6.6s\t%6.6s\t%6.6s\t%6.6s\t%6.6s\n' % (str(airmass0['B']),str(airmass0['V']),str(airmass0['g']),str(airmass0['r']),str(airmass0['i'])))
        for i in range(0,len(magsex)): 
            fileph['m'+filters[_filter]][i]=magsex[i]    #  instrumental mangitude of std in pos0[i]
            if _field=='landolt':
                stringastandard='%12.12s\t%7.7s\t%7.7s\t%7.7s\t%7.7s\t%7.7s' % (idstd0[i],fileph['V'][i],fileph['BV'][i],fileph['UB'][i],\
                                                                                fileph['VR'][i],fileph['RI'][i])
                fil.write('%7.7s\t%7.7s\t%7.7s\t%7.7s\t%7.7s\t%60.60s\n' \
                              % (str(fileph['mU'][i]),str(fileph['mB'][i]),str(fileph['mV'][i]),str(fileph['mR'][i]),str(fileph['mI'][i]),str(stringastandard)))
            elif _field=='sloan':
                stringastandard='%12.12s\t%7.7s\t%7.7s\t%7.7s\t%7.7s\t%7.7s' % (idstd0[i],fileph['r'][i],fileph['gr'][i],fileph['ug'][i],\
                                                                                fileph['ri'][i],fileph['iz'][i])
                fil.write('%7.7s\t%7.7s\t%7.7s\t%7.7s\t%7.7s\t%60.60s\n' \
                              % (str(fileph['mu'][i]),str(fileph['mg'][i]),str(fileph['mr'][i]),str(fileph['mi'][i]),str(fileph['mz'][i]),str(stringastandard)))
            elif _field=='apass':
                stringastandard='%12.12s\t%7.7s\t%7.7s\t%7.7s\t%7.7s\t%7.7s' % (idstd0[i],fileph['V'][i],fileph['BV'][i],fileph['Vg'][i],\
                                                                                fileph['gr'][i],fileph['ri'][i])
                fil.write('%7.7s\t%7.7s\t%7.7s\t%7.7s\t%7.7s\t%60.60s\n' \
                              % (str(fileph['mB'][i]),str(fileph['mV'][i]),str(fileph['mg'][i]),str(fileph['mr'][i]),str(fileph['mi'][i]),str(stringastandard)))
            zero.append(float(float(magstd0[filters[_filter]][i]))-float(magsex[i]))
            zeroerr.append((float(errstd0[filters[_filter]][i])**2 + magerrsex[i]**2)**0.5)
            magcor.append(magsex[i])
        fil.close()
        magstdn=lsc.lscabsphotdef.transform2natural(_instrume,magstd0,colorefisso,_field)

        magsex1=magsex+kk[filters[_filter]]*float(_airmass)  #   add again extinction for natural zero point comparison

        media,mediaerr,mag2,data2=lsc.lscabsphotdef.zeropoint2(array(magstdn[filters[_filter]],float),array(magsex1,float),10,2,show)

        if media!=9999: 
              _limmag = limmag(re.sub('.sn2.fits','.fits',img), media, 3, _fwhm)     #   compute limiting magnitude at 3 sigma
              print '#####  ',str(_limmag)
              lsc.mysqldef.updatevalue('photlco','limmag',_limmag,string.split(re.sub('.sn2.fits','.fits',img),'/')[-1],'lcogt2','filename')
              lsc.mysqldef.updatevalue('photlco','zn',media,string.split(re.sub('.sn2.fits','.fits',img),'/')[-1],'lcogt2','filename')
              lsc.mysqldef.updatevalue('photlco','dzn',mediaerr,string.split(re.sub('.sn2.fits','.fits',img),'/')[-1],'lcogt2','filename')
              lsc.mysqldef.updatevalue('photlco','znnum',len(data2),string.split(re.sub('.sn2.fits','.fits',img),'/')[-1],'lcogt2','filename')


        colorvec=colors[filters[_filter]]
        zero = array(zero)
        zeroerr = array(zeroerr)
        print 'attempting these colors:', colorvec
        if not colorvec:
            colorvec.append(2*filters[_filter])
        if zcatnew and show and not _interactive:
            fig, axarr = plt.subplots(ncols=len(colorvec), figsize=(8*len(colorvec), 6), squeeze=False)
        for i, col in enumerate(colorvec):
            col0=magstd0[col[0]] 
            col1=magstd0[col[1]]
            colstd0=array(col0,float)-array(col1,float)
            colerr0 = errstd0[col[0]]
            colerr1 = errstd0[col[1]]
            colerrstd0 = (array(colerr0, float)**2 + array(colerr1, float)**2)**0.5

#            colore=[]
#            for i in range(0,len(pos1)):   colore.append(colstd0[i])
            # cut stars with crazy magnitude and color
#            colore1=compress(abs(array(zero))<50,array(colore))
#            zero1=compress(abs(array(zero))<50,array(zero))
            if _filter in ['up', 'zs']: maxcolor = 10
            else:                       maxcolor = 2
#            zero2=compress(abs(array(colore1)) < maxcolor,array(zero1))
#            colore2=compress(abs(array(colore1)) < maxcolor,array(colore1))

            good = (abs(zero) < 50) & (abs(colstd0) < maxcolor) & (zeroerr != 0) & (colerrstd0 != 0)
            zero2 = zero[good]
            colore2 = colstd0[good]
            zeroerr2 = zeroerr[good]
            coloreerr2 = colerrstd0[good]

            if _fix and filters[_filter]+col in colorefisso:
                fisso = colorefisso[filters[_filter]+col]
            elif col == 2*filters[_filter]:
                fisso = 0.
            else:
                fisso = None

            if len(colore2)==0:
                print 'no calibration:', filters[_filter], col, _field
                continue
#                b,a,sa,sb=9999,9999,0,0
            else:
                if zcatnew:
                    if show and not _interactive:
                        plt.axes(axarr[0, i])
                    a, sa, b, sb = fitcol3(colore2, zero2, coloreerr2, zeroerr2, fisso, _filter, ' - '.join(col), show, _interactive, rejection)
                else:
                    if _interactive:    a,sa,b,sb=fitcol(colore2,zero2,_filter,col,fisso)
                    else:               a,sa,b,sb=fitcol2(colore2,zero2,_filter,col,fisso,show,rejection)
            result[filters[_filter]+col]=[a,sa,b,sb]
        if result:
            print '### zeropoint ..... done at airmass 0'
            if _catalogue:
                lsc.util.updateheader(img,0,{'CATALOG':[str(string.split(_catalogue,'/')[-1]),'catalogue source']})
            stringa=''
            for ll in result:
                for kk in range(0,len(result[ll])):
                                    if not isfinite(result[ll][kk]): result[ll][kk]=0.0 
                valore='%3.3s %6.6s %6.6s  %6.6s  %6.6s' %  (str(ll),str(result[ll][0]),str(result[ll][2]),str(result[ll][1]),str(result[ll][3]))
                lsc.util.updateheader(img,0,{'zp'+ll:[str(valore),'a b sa sb in y=a+bx']})
                print '### added to header:', valore
                if ll[0]==ll[2]: num=2
                elif ll[0]==ll[1]: num=1
                else: sys.exit('somthing wrong with color '+ll)
                try:
                    print 'zcol'+str(num),ll[1:],string.split(re.sub('.sn2.fits','.fits',img),'/')[-1]
                    lsc.mysqldef.updatevalue(database,'zcol'+str(num),ll[1:],string.split(re.sub('.sn2.fits','.fits',img),'/')[-1])
                    lsc.mysqldef.updatevalue(database,'z'+str(num),result[ll][0],string.split(re.sub('.sn2.fits','.fits',img),'/')[-1])
                    lsc.mysqldef.updatevalue(database,'c'+str(num),result[ll][2],string.split(re.sub('.sn2.fits','.fits',img),'/')[-1])
                    lsc.mysqldef.updatevalue(database,'dz'+str(num),result[ll][1],string.split(re.sub('.sn2.fits','.fits',img),'/')[-1])
                    lsc.mysqldef.updatevalue(database,'dc'+str(num),result[ll][3],string.split(re.sub('.sn2.fits','.fits',img),'/')[-1])
                    if os.path.isfile(string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1]):
                          lsc.mysqldef.updatevalue(database,'zcol'+str(num),ll[1:],string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1])
                          lsc.mysqldef.updatevalue(database,'z'+str(num),result[ll][0],string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1])
                          lsc.mysqldef.updatevalue(database,'c'+str(num),result[ll][2],string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1])
                          lsc.mysqldef.updatevalue(database,'dz'+str(num),result[ll][1],string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1])
                          lsc.mysqldef.updatevalue(database,'dc'+str(num),result[ll][3],string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1])
                    if result[ll][0]!=9999:
                          lsc.mysqldef.updatevalue(database,'zcat',string.split(_catalogue,'/')[-1],string.split(re.sub('.sn2.fits','.fits',img),'/')[-1])
                          if os.path.isfile(string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1]):
                                lsc.mysqldef.updatevalue(database,'zcat',string.split(_catalogue,'/')[-1],string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1])
                    else:
                        lsc.mysqldef.updatevalue(database,'zcat','X',string.split(re.sub('.sn2.fits','.fits',img),'/')[-1])
                        if os.path.isfile(string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1]):
                              lsc.mysqldef.updatevalue(database,'zcat','X',string.split(re.sub('.diff.sn2.fits','.fits',img),'/')[-1])
                except: print 'module mysqldef not found'
                
#################################################################
#################### new zero point calculation #################
def fitcol3(colors, deltas, dcolors=None, ddeltas=None, fixedC=None, filt='', col='Color', show=False, interactive=False, clipsig=2, extra=False):
    if interactive:
        global keep, Z, dZ, C, dC
        plt.cla()
    if fixedC is None:
        # fit Theil-Sen line and find outliers
        C, Z, _, _ = stats.theilslopes(deltas, colors) # delta = calibrated mag - instrumental mag
        zeros = deltas - C*colors # zeros are the "zero points" for individual stars
        dzeros = (ddeltas**2 + (C*dcolors)**2)**0.5
        resids = zeros - Z
        keep = abs(resids) <= clipsig*dzeros
        if sum(keep) <= 5: # if there aren't very many points, use fixed color term
            if filt=='g': fixedC = 0.1
            else:         fixedC = 0
            print 'Not enough points (after rejection). Defaulting to C = {:.2f}.'.format(fixedC)
    if fixedC is not None:
        C = fixedC
        zeros = deltas - C*colors
        dzeros = (ddeltas**2 + (C*dcolors)**2)**0.5
        Z = np.median(zeros)
        resids = zeros - Z
        keep = abs(resids) <= clipsig*dzeros
    Z, dZ, C, dC = calcZC(colors, deltas, dcolors, ddeltas, fixedC, filt, col, (show or interactive), guess=[Z, C])
    if interactive:
        def onpick(event):
            global keep, Z, dZ, C, dC
            i = event.ind[0] # find closest point
            keep[i] = not keep[i] # toggle rejection
            print
            Z, dZ, C, dC = calcZC(colors, deltas, dcolors, ddeltas, fixedC, filt, col, show=True, guess=[Z, C])
        cid = plt.gcf().canvas.mpl_connect('pick_event', onpick)
        raw_input('Press enter to continue.')
        plt.gcf().canvas.mpl_disconnect(cid)
    elif fixedC is None and C > 0.3: # if the color term is too crazy, use fixed color term
        if filt=='g': fixedC = 0.1
        else:         fixedC = 0
        print 'C = {:.2f} is too crazy. Redoing with C = {:.2f}.'.format(C, fixedC)
        C = fixedC
        zeros = deltas - C*colors
        dzeros = (ddeltas**2 + (C*dcolors)**2)**0.5
        Z = np.median(zeros)
        resids = zeros - Z
        keep = abs(resids) <= clipsig*dzeros
        Z, dZ, C, dC = calcZC(colors, deltas, dcolors, ddeltas, fixedC, filt, col, show, guess=[Z, C])
    if extra: return Z, dZ, C, dC, keep
    else: return Z, dZ, C, dC

def calcZC(colors, deltas, dcolors=None, ddeltas=None, #keep=None,
           fixedC=None, filt='', col='Color', show=False, guess=[23., 0.03], extra=False):
    if fixedC is None:
        def f(B, x): return B[0] + B[1]*x
        linear = odr.Model(f)
        mydata = odr.Data(colors[keep], deltas[keep], wd=dcolors[keep]**-2, we=ddeltas[keep]**-2)
        myodr = odr.ODR(mydata, linear, beta0=guess) # start from typical values
        myoutput = myodr.run()
        Z, C = myoutput.beta
        dZ, dC = myoutput.sd_beta
        x_reg = myoutput.xplus
        y_reg = myoutput.y
    elif np.any(keep):
        Z, sum_of_weights = np.average(deltas[keep] - fixedC * colors[keep], weights=1/(ddeltas[keep]**2 + dcolors[keep]**2), returned=True)
        dZ = sum_of_weights**-0.5
        C, dC = fixedC, 0
    else:
        Z, C = guess
        dZ, dC = 0, 0
    print 'zero point = {:5.2f} +/- {:4.2f}'.format(Z, dZ)
    print 'color term = {:5.2f} +/- {:4.2f}'.format(C, dC)
    if show:
        if not plt.gca().get_autoscale_on():
            lims = plt.axis()
        else:
            lims = [None, None, None, None]
        plt.cla()
        plt.scatter(colors, deltas, marker='.', picker=5)
        plt.errorbar(colors[keep], deltas[keep], xerr=dcolors[keep], yerr=ddeltas[keep], color='g', marker='o', linestyle='none')
        plt.errorbar(colors[~keep], deltas[~keep], xerr=dcolors[~keep], yerr=ddeltas[~keep], color='r', marker='o', linestyle='none')
        plt.axis(lims)
        plt.autoscale(False)
        xx = np.array(plt.axis()[0:2])
        yy = Z + C*xx
        plt.plot(xx, yy, '--')
        plt.xlabel(col)
        plt.ylabel('Calibrated Mag - Instrumental Mag')
        plt.title(filt)
        plt.pause(0.1)
    if fixedC is None and extra: return Z, dZ, C, dC, x_reg, y_reg
    else: return Z, dZ, C, dC
#################################################################
#################################################################
def fitcol(col,dmag,band,color,fissa=''):
    import matplotlib.pyplot as plt 
    from numpy import polyfit,polyval,argmin,sqrt,mean,array,std,median
    global idd,_col,_dmag,testo,lines,pol,sss,f,fixcol,sigmaa,sigmab,aa,bb
    plt.ion()
    fig = plt.figure()
    _dmag = dmag[:]
    _col  = col[:]
    sss=band
    f=color
    fixcol=fissa
    _col = array(_col)
    _dmag = array(_dmag)
    idd = range(len(_col))
    plt.plot(_col,_dmag,'ok')

    _fixcol=fixcol
    if len(_col[idd])==1:  _fixcol=0.0
    else:   _fixcol=fixcol

    if _fixcol=='':
        pol = polyfit(_col[idd],_dmag[idd],1,full=True) ###
        aa=pol[0][1]
        bb=pol[0][0]

        if len(idd)>2:
            sigmae = sqrt(pol[1][0]/(len(idd)  -2))
            sigmaa = sigmae*sqrt(1./len(idd)+(mean(_col[idd])**2)/sum((_col[idd]-\
                                                                           mean(_col[idd]))**2))
            sigmab = sigmae*sqrt(1/sum((_col[idd]-mean(_col[idd]))**2))
        else:
            sigmaa=0.0
            sigmab=0.0
    else:
#            aa=mean(array(_dmag)[idd]-array(_col)[idd]*fixcol)
            aa=median(array(_dmag)[idd]-array(_col)[idd]*fixcol)
            bb=fixcol
            sigmaa=std(abs(aa-(array(_dmag)-array(_col)*float(_fixcol))))
            sigmab=0.0

    xx = [min(_col)-.1,max(_col)+.1]
    yy = polyval([bb,aa],xx)                ###
    lines = plt.plot(xx,yy,'r-')
    plt.ylim(min(_dmag)-.2,max(_dmag)+.2)
    plt.xlim(min(xx),max(xx))
    plt.xlabel(sss)
    plt.title(f)
    try:
        testo = plt.figtext(.2,.85,'%5.3f + %s* %5.3f [%4.3f  %4.3f]'%\
                             (aa,sss,bb,sigmaa,sigmab))
    except:
        testo = plt.figtext(.2,.85,'%5.3f + %s* %5.3f [%4.3f  %4.3f]'%\
                             (aa,sss,bb,sigmaa,sigmab))

    kid = fig.canvas.mpl_connect('key_press_event',onkeypress)
    cid = fig.canvas.mpl_connect('button_press_event',onclick)
    plt.draw()
    raw_input('left-click mark bad, right-click unmark, <d> remove. Return to exit ...')
    plt.close()
    print '####'
    print sigmaa,sigmab, aa,bb
    return aa,sigmaa,bb,sigmab

#################################################################

def fitcol2(_col,_dmag,band,col,fixcol='',show=False,rejection=2):
    from numpy import polyfit,polyval,argmin,sqrt,mean,array,std,compress
    sss=band
    f=col
    if len(_col)>1:
        if fixcol:
            slope=fixcol
            mean0,sig0,yy0,xx0=lsc.lscabsphotdef.meanclip2(_col,_dmag,fixcol, clipsig=rejection, maxiter=5, converge_num=.99, verbose=0)
            xx = [min(_col)-.1,max(_col)+.1]
            yy = polyval([fixcol,mean0],_col)                ###
            try:      sigmae = sqrt(sig0/(len(xx0)  -2))
            except:   sigmae=0
            sigmaa = sigmae*sqrt(1./len(xx0)+(mean(xx0)**2)/sum((xx0-mean(xx0))**2))
            sigmab=0.0
        else:
            mean0,sig0,slope,yy0,xx0=lsc.lscabsphotdef.meanclip3(_col,_dmag,fixcol, clipsig=rejection, maxiter=5, converge_num=.99, verbose=0)
            xx = [min(_col)-.1,max(_col)+.1]
            yy = polyval([slope,mean0],_col)                ###
            try:      sigmae = sqrt(sig0/(len(xx0)  -2))
            except:   sigmae=0
            sigmaa = sigmae*sqrt(1./len(xx0)+(mean(xx0)**2)/sum((xx0-mean(xx0))**2))
            sigmab = sigmae*sqrt(1/sum((xx0-mean(xx0))**2))
        if show:
            import time
            import matplotlib.pyplot as plt
            plt.ion()
            plt.clf()
            plt.plot(_col,_dmag,'ob')
            plt.plot(xx0,yy0,'xr')
            plt.plot(_col,yy,'-g')
            plt.ylabel('zeropoint')
            plt.xlabel(f)
            plt.title(sss)
            plt.draw()
            time.sleep(1)
    try:
        print '###', mean0, sigmaa, slope, sigmab
    except:
        print '\n### zeropoint not computed'
        mean0,sigmaa,slope,sigmab=9999,9999,9999,9999
    return mean0,sigmaa,slope,sigmab

def meanclip2(xx,yy,slope, clipsig=3.0, maxiter=5, converge_num=0.1, verbose=0):
    from numpy import array
    import numpy
    xx=array(xx)
    yy=array(yy)
    xx0=array(xx[:])
    yy0=array(yy[:])
    ct=len(yy)
    slope=float(slope)
    iter = 0; c1 = 1.0 ; c2 = 0.0
    while (c1 >= c2) and (iter < maxiter):
        lastct = ct
        sig=numpy.std(yy0-xx0*slope)
#        mean=numpy.mean(array(yy0)-array(xx0)*slope)
        mean=numpy.median(array(yy0)-array(xx0)*slope)
        wsm = numpy.where( abs(yy0-xx0*slope) < mean+clipsig*sig )
        ct = len(wsm[0])
        if ct > 0:
            xx0=xx0[wsm]
            yy0=yy0[wsm]
        c1 = abs(ct - lastct)
        c2 = converge_num * lastct
        iter += 1
# End of while loop
#    mean=numpy.mean(array(yy0)-array(xx0)*slope)
    mean=numpy.median(array(yy0)-array(xx0)*slope)
    sig=numpy.std(array(yy0)-array(xx0)*float(slope))
    if verbose: pass
    return mean, sig,yy0,xx0

def meanclip3(xx,yy,slope, clipsig=3.0, maxiter=5, converge_num=0.1, verbose=0):
    from numpy import array, polyfit
    import numpy
    xx=array(xx)
    yy=array(yy)
    xx0=array(xx[:])
    yy0=array(yy[:])
    ct=len(yy)
    iter = 0; c1 = 1.0 ; c2 = 0.0
    while (c1 >= c2) and (iter < maxiter):
        lastct = ct
        pol = polyfit(xx0,yy0,1,full=True) ###
        mean0=pol[0][1]
        slope=pol[0][0]
        sig=numpy.std(yy0-mean0-slope*xx0)
        wsm = numpy.where( abs(yy0-xx0*slope) < mean0+clipsig*sig )
        ct = len(wsm[0])
        if ct > 0:
            xx0=xx0[wsm]
            yy0=yy0[wsm]
        c1 = abs(ct - lastct)
        c2 = converge_num * lastct
        iter += 1
# End of while loop
    pol = polyfit(xx0,yy0,1,full=True) ###
    mean0=pol[0][1]
    slope=pol[0][0]
    sig=numpy.std(yy0-mean0-slope*xx0)
    if verbose: pass
    return mean0, sig,slope,yy0,xx0

########################################################################

def makecatalogue(imglist):
    from astropy.io import fits
    from numpy import array, zeros
    filters={}
    dicti={}
    for img in imglist:
        t = fits.open(img)
        tbdata = t[1].data
        hdr1=t[0].header
        _filter=lsc.util.readkey3(hdr1,'filter')
        if _filter not in dicti: dicti[_filter]={}
        if img not in dicti[_filter]: dicti[_filter][img]={}
        for jj in hdr1:
            if jj[0:2]=='ZP':
                dicti[_filter][img][jj]=lsc.util.readkey3(hdr1,jj)

#######################
#       early data may have JD instead of mjd in the fits table
#
        if 'MJD' in hdr1.keys():
              dicti[_filter][img]['mjd']=lsc.util.readkey3(hdr1,'MJD')
        else:
              dicti[_filter][img]['mjd']=lsc.util.readkey3(hdr1,'JD')
        dicti[_filter][img]['JD']=dicti[_filter][img]['mjd']
#######################

        dicti[_filter][img]['exptime']=lsc.util.readkey3(hdr1,'exptime')
        dicti[_filter][img]['airmass']=lsc.util.readkey3(hdr1,'airmass')
        dicti[_filter][img]['telescope']=lsc.util.readkey3(hdr1,'telescop')
        dicti[_filter][img]['siteid']=hdr1['SITEID']
        
        for col in tbdata.columns.names:
            dicti[_filter][img][col]=tbdata.field(col)
        if 'ra0' not in tbdata.columns.names:
            dicti[_filter][img]['ra0']=array(zeros(len(dicti[_filter][img]['ra'])),float)
            dicti[_filter][img]['dec0']=array(zeros(len(dicti[_filter][img]['ra'])),float)
            for i in range(0,len(dicti[_filter][img]['ra'])):
#                dicti[_filter][img]['ra0'][i]=float(iraf.real(dicti[_filter][img]['ra'][i]))*15
#                dicti[_filter][img]['dec0'][i]=float(iraf.real(dicti[_filter][img]['dec'][i]))
                dicti[_filter][img]['ra0'][i],dicti[_filter][img]['dec0'][i]=lsc.lscabsphotdef.deg2HMS(dicti[_filter][img]['ra'][i],dicti[_filter][img]['dec'][i])
    return dicti

######################################################################################################
def finalmag(Z1,Z2,C1,C2,m1,m2):
    color=(Z1-Z2+m1-m2)/(1-(C1-C2))
    print 'color ',color
    print Z1,C1,m1
    print Z2,C2,m2
    M1=Z1+C1*color+m1
    M2=Z2+C2*color+m2
    return M1,M2

def erroremag(z0,z1,m0,m1,c0,c1,position): #  z=zeropoint,m=magnitude,colorterm  
    if position==0:   #    error for first band in the color: (e.g.  V in VR) 
        dm0=1+(c0/(1-(c0-c1)))
        dz0=1+(c0/(1-(c0-c1)))
        dm1=(-1)*(c0/(1-(c0-c1)))
        dz1=(-1)*(c0/(1-(c0-c1)))
        dc0=(z0+m0-z1-m1)*(1+c1)*(1/(1-(c0-c1))**2)
        dc1=(-1)*(z0+m0-z1-m1)*(c0)*(1/(1-(c0-c1))**2)
    elif position==1:   #    error for second band in the color: (e.g.  R in VR) 
        dm0=1-(c1/(1-(c0-c1)))
        dz0=1-(c1/(1-(c0-c1)))
        dm1=(-1)*(c1/(1-(c0-c1)))
        dz1=(-1)*(c1/(1-(c0-c1)))
        dc0=(z0+m0-z1-m1)*(1-c0)*(1/(1-(c0-c1))**2)
        dc1=(z0+m0-z1-m1)*(c1)*(1/(1-(c0-c1))**2) 
    else:
        # added to make the pipeline working, but error not good
        dm0=1
        dz0=0
        dm1=1
        dz1=0
        dc0=0
        dc1=0
    return dc0,dc1,dz0,dz1,dm0,dm1

#################################################################

def zeropoint(data,mag,maxiter=10,nn=2,show=False):
    import numpy as np
    z0=np.mean(data)
    std0=np.std(data)
    data1=data[:]
    mag1=mag[:]
    data2=np.compress((data < (z0+std0)) & (data>(z0-std0)),data)
    mag2=np.compress((data < (z0+std0)) & (data>(z0-std0)),mag)
    z2=np.mean(data2)
    std2=np.std(data2)
    iter=0; 
    if show:  
        import matplotlib.pyplot as pl
        pl.ion()

    while iter < maxiter and len(data2)>5:
        z1=np.mean(data1)
        std1=np.std(data1)
        z2=np.mean(data2)
        std2=np.std(data2)
        if show:
            print 'rejected '+str(len(data1)-len(data2))+' point'
            print z1,std1,len(data1)
            print z2,std2,len(data2)

        if np.abs(z2-z1)<std2/np.sqrt(len(data2)):
            if show:
                print 'zero points are within std2 '
                pl.clf()
                pl.plot(mag1,data1,'or')
                pl.plot(mag2,data2,'xg')
            break
        else:
            data1=np.compress((data < (z1+nn*std1)) & (data>(z1-nn*std1)),data)
            data2=np.compress((data < (z2+nn*std2)) & (data>(z2-nn*std2)),data)
            mag1=np.compress((data < (z1+nn*std1)) & (data>(z1-nn*std1)),mag)
            mag2=np.compress((data < (z2+nn*std2)) & (data>(z2-nn*std2)),mag)
            z1=np.mean(data1)
            std1=np.std(data1)
            z2=np.mean(data2)
            std2=np.std(data2)
        iter += 1
        if show:
            print 'iteration '+str(iter)
            print z1,std1,len(data1)
            print z2,std2,len(data2)
            pl.clf()
            pl.plot(mag,data,'or')
            pl.plot(mag2,data2,'*g')
    return z2,std2,mag2,data2

#############################################

def zeropoint2(xx,mag,maxiter=10,nn=2,show=False,_cutmag=99):
   if len(xx):
      import numpy as np
      if float(_cutmag)!=99:
         print 'cut mag '+str(_cutmag)
         xx=np.compress(mag<_cutmag,xx)
         mag=np.compress(mag<_cutmag,mag)
      data=np.array(xx-mag)
      z0=np.median(data)
      std0=np.std(data)
      data1=data[:]
      mag1=mag[:]
      data2=np.compress((data < (z0+std0)) & (data>(z0-std0)),data)
      mag2=np.compress((data < (z0+std0)) & (data>(z0-std0)),mag)
      z2, std2 = 9999, 9999
      iter=0; 
      if show:  
            print len(data2)
            import matplotlib.pyplot as pl
            pl.ion()
            pl.clf()
            pl.plot(mag,data,'or')
            pl.plot(mag2,data2,'*g')
      while iter < maxiter and len(data2)>5:
          z1=np.mean(data1)
          std1=np.std(data1)
          z2=np.mean(data2)
          std2=np.std(data2)
          if show:
              print 'rejected '+str(len(data1)-len(data2))+' point'
              print z1,std1,len(data1)
              print z2,std2,len(data2)
          if np.abs(z2-z1)<std2/np.sqrt(len(data2)):
              if show:
                  print 'zero points are within std2 '
                  pl.clf()
                  pl.plot(mag1,data1,'or')
                  pl.plot(mag2,data2,'xg')
              break
          else:
              data1=np.compress((data < (z1+nn*std1)) & (data>(z1-nn*std1)),data)
              data2=np.compress((data < (z2+nn*std2)) & (data>(z2-nn*std2)),data)
              mag1=np.compress((data < (z1+nn*std1)) & (data>(z1-nn*std1)),mag)
              mag2=np.compress((data < (z2+nn*std2)) & (data>(z2-nn*std2)),mag)
              z1=np.mean(data1)
              std1=np.std(data1)
              z2=np.mean(data2)
              std2=np.std(data2)
          iter += 1
          if show:
              print 'iteration '+str(iter)
              print z1,std1,len(data1)
              print z2,std2,len(data2)
              pl.clf()
              pl.plot(mag,data,'or')
              pl.plot(mag2,data2,'*g')
      if np.isnan(z2): z2,std2= 9999, 9999
   else:
      z2,std2,mag2,data2=9999,9999,9999,9999
   return z2,std2,mag2,data2

########################################################################

def transform2natural(_instrument,_catalogue,colorefisso,_inputsystem='sloan'):
   import numpy as np
   _catalogue2={}
   for i in _catalogue.keys():
      _catalogue2[i]=np.array(_catalogue[i][:],float)
   if _inputsystem in ['sloan','sloanprime']:
      col={}
      col['ug']=[(_catalogue2['u'][i]-_catalogue2['g'][i]) if (_catalogue2['u'][i]<99 and _catalogue2['g'][i]<99) else  (_catalogue2['u'][i]-_catalogue2['u'][i]) for i in range(0,len(_catalogue2['u']))]
      col['gr']=[(_catalogue2['g'][i]-_catalogue2['r'][i]) if (_catalogue2['g'][i]<99 and _catalogue2['r'][i]<99) else  (_catalogue2['g'][i]-_catalogue2['g'][i]) for i in range(0,len(_catalogue2['g']))]
      col['ri']=[(_catalogue2['r'][i]-_catalogue2['i'][i]) if (_catalogue2['r'][i]<99 and _catalogue2['i'][i]<99) else  (_catalogue2['r'][i]-_catalogue2['r'][i]) for i in range(0,len(_catalogue2['r']))]
      col['iz']=[(_catalogue2['i'][i]-_catalogue2['z'][i]) if (_catalogue2['i'][i]<99 and _catalogue2['z'][i]<99) else  (_catalogue2['i'][i]-_catalogue2['i'][i]) for i in range(0,len(_catalogue2['i']))]
      _catalogue2['u']=_catalogue2['u']-colorefisso['uug']*np.array(col['ug'])#(_catalogue['u']-_catalogue['g'])
      _catalogue2['g']=_catalogue2['g']-colorefisso['ggr']*np.array(col['gr'])#(_catalogue['g']-_catalogue['r'])
      _catalogue2['r']=_catalogue2['r']-colorefisso['rri']*np.array(col['ri'])#(_catalogue['r']-_catalogue['i'])
      _catalogue2['i']=_catalogue2['i']-colorefisso['iri']*np.array(col['ri'])#(_catalogue['r']-_catalogue['i'])
      _catalogue2['z']=_catalogue2['z']-colorefisso['ziz']*np.array(col['iz'])#(_catalogue['i']-_catalogue['z'])
      print 'transform '+str(_inputsystem)+' to natural system'
      print 'un = u - '+str(colorefisso['uug'])+' * (u-g)'
      print 'gn = g - '+str(colorefisso['ggr'])+' * (g-r)'
      print 'rn = r - '+str(colorefisso['rri'])+' * (r-i)'
      print 'in = i - '+str(colorefisso['iri'])+' * (r-i)'
      print 'zn = z - '+str(colorefisso['ziz'])+' * (i-z)'
   elif _inputsystem in ['landolt']:
      col={}
      col['UB']=[(_catalogue2['U'][i]-_catalogue2['B'][i]) if (_catalogue2['U'][i]<99 and _catalogue2['B'][i]<99) else  (_catalogue2['B'][i]-_catalogue2['B'][i]) for i in range(0,len(_catalogue2['U']))]
      col['BV']=[(_catalogue2['B'][i]-_catalogue2['V'][i]) if (_catalogue2['B'][i]<99 and _catalogue2['V'][i]<99) else  (_catalogue2['B'][i]-_catalogue2['B'][i]) for i in range(0,len(_catalogue2['B']))]
      col['VR']=[(_catalogue2['V'][i]-_catalogue2['R'][i]) if (_catalogue2['V'][i]<99 and _catalogue2['R'][i]<99) else  (_catalogue2['V'][i]-_catalogue2['V'][i]) for i in range(0,len(_catalogue2['V']))]
      col['RI']=[(_catalogue2['R'][i]-_catalogue2['I'][i]) if (_catalogue2['R'][i]<99 and _catalogue2['I'][i]<99) else  (_catalogue2['R'][i]-_catalogue2['R'][i]) for i in range(0,len(_catalogue2['R']))]
      _catalogue2['U']=_catalogue2['U']-colorefisso['UUB']*np.array(col['UB'])#(_catalogue['U']-_catalogue['B'])
      _catalogue2['B']=_catalogue2['B']-colorefisso['BBV']*np.array(col['BV'])#(_catalogue['B']-_catalogue['V'])
      _catalogue2['V']=_catalogue2['V']-colorefisso['VVR']*np.array(col['VR'])#(_catalogue['V']-_catalogue['R'])
      _catalogue2['R']=_catalogue2['R']-colorefisso['RVR']*np.array(col['VR'])#(_catalogue['V']-_catalogue['R'])
      _catalogue2['I']=_catalogue2['I']-colorefisso['IRI']*np.array(col['RI'])#(_catalogue['R']-_catalogue['I'])
      print 'transform '+str(_inputsystem)+' to natural system'
      print "Un = U - "+str(colorefisso['UUB'])+" * (U-B)"
      print "Bn = B - "+str(colorefisso['BBV'])+" * (B-V)"
      print "Vn = V - "+str(colorefisso['VVR'])+" * (V-R)"
      print "Rn = R - "+str(colorefisso['RVR'])+" * (V-R)"
      print "In = I - "+str(colorefisso['IRI'])+" * (R-I)"
   elif _inputsystem in ['apass']:
      col={}
      col['BV']=[(_catalogue2['B'][i]-_catalogue2['V'][i]) if (_catalogue2['B'][i]<99 and _catalogue2['V'][i]<99) else  (_catalogue2['B'][i]-_catalogue2['B'][i]) for i in range(0,len(_catalogue2['V']))]
      col['gr']=[(_catalogue2['g'][i]-_catalogue2['r'][i]) if (_catalogue2['g'][i]<99 and _catalogue2['r'][i]<99) else  (_catalogue2['g'][i]-_catalogue2['g'][i]) for i in range(0,len(_catalogue2['g']))]
      col['ri']=[(_catalogue2['r'][i]-_catalogue2['i'][i]) if (_catalogue2['r'][i]<99 and _catalogue2['i'][i]<99) else  (_catalogue2['r'][i]-_catalogue2['r'][i]) for i in range(0,len(_catalogue2['r']))]
      _catalogue2['B']=_catalogue2['B']-colorefisso['BBV']*np.array(col['BV']) #(_catalogue['B']-_catalogue['V'])
      _catalogue2['V']=_catalogue2['V']-colorefisso['BBV']*np.array(col['BV']) #(_catalogue['B']-_catalogue['V'])
      _catalogue2['g']=_catalogue2['g']-colorefisso['ggr']*np.array(col['gr']) #(_catalogue['g']-_catalogue['r'])
      _catalogue2['r']=_catalogue2['r']-colorefisso['rri']*np.array(col['ri']) #(_catalogue['r']-_catalogue['i'])
      _catalogue2['i']=_catalogue2['i']-colorefisso['iri']*np.array(col['ri']) #(_catalogue['r']-_catalogue['i'])
      print 'transform '+str(_inputsystem)+' to natural system'
      print "Bn = B - "+str(colorefisso['BBV'])+" * (B-V)"
      print "Vn = V - "+str(colorefisso['BBV'])+" * (B-V)"
      print "gn = g' - "+str(colorefisso['ggr'])+" * (g'-g')"
      print "rn = r' - "+str(colorefisso['rri'])+" * (r'-i')"
      print "in = i' - "+str(colorefisso['iri'])+" * (r'-i')"
   return _catalogue2

##################################################################################

def zeronew(ZZ,maxiter=10,nn=5,verbose=False,show=False):
     #         compute first median and error
     import numpy as np
     median=np.median(ZZ)                    
     sigma=(np.percentile(ZZ,75)-np.percentile(ZZ,25))*1.349
     # cut around median and new median
     ZZcut=np.compress((ZZ < (median+nn*sigma)) & (ZZ>(median-nn*sigma)),ZZ)
     xx=np.arange(len(ZZ))
     mediancut=np.median(ZZcut)      
     sigmacut=(np.percentile(ZZcut,75)-np.percentile(ZZcut,25))*1.349
     cut=len(ZZ)-len(ZZcut)
     iter=0
     while iter < maxiter and len(ZZcut)>5 and cut>0:
          iter+=1
          if verbose:
               print iter
               print 'reject  '+str(cut)+' objects'  
               print 'number of object= '+str(len(ZZcut))
               print 'median=  '+str(mediancut)
               print 'sigma= '+str(sigmacut)
          # new cut around new median after rejection 
          ZZcut2=np.compress((ZZ < (mediancut+nn*sigmacut)) & (ZZ>(mediancut-nn*sigmacut)),ZZ)  

          median2=np.median(ZZcut2)
          sigma2=(np.percentile(ZZcut2,75)-np.percentile(ZZcut2,25))*1.349
          cut=len(ZZcut)-len(ZZcut2)
          if len(ZZcut2)>=5:
               ZZcut=ZZcut2
               sigmacut=sigma2
               mediancut=np.median(ZZcut2)
          if verbose:   
              print len(ZZcut2),sigmacut,mediancut
     if show:
          import matplotlib.pyplot as pl
          pl.ion()
          xxc=np.arange(len(ZZcut))
          pl.plot(xx,ZZ,'or')
          pl.plot(xxc,ZZcut,'b*')
          pl.draw()
          import time
          time.sleep(1)

     return ZZcut,sigmacut,mediancut

#######################################################################
def sloan2file(ra, dec, radius=10., mag1=13., mag2=20., output='sloan.cat'):
    '''download an SDSS catalog'''
    t = SDSS.query_sql('''select P.ra, P.dec, P.objID, P.u, P.err_u, P.g, P.err_g, P.r, P.err_r, P.i, P.err_i, P.z, P.err_z
                          from PhotoPrimary as P, dbo.fGetNearbyObjEq({}, {}, {}) as N
                          where P.objID=N.objID and P.type=6 and P.r >= {} and P.r <= {}'''.format(ra, dec, radius, mag1, mag2))
    if t is not None:
        t['ra'].format ='%16.12f'
        t['dec'].format = '%16.13f'
        t['objID'].format = '%19d'
        for filt in 'ugriz':
            t[filt].format = '%8.5f'
            t['err_'+filt].format = '%11.9f'
        t.meta['comments'] = [
        'BEGIN CATALOG HEADER',
        '   type btext',
        '   nheader 1',
        '       csystem J2000',
        '   nfields 13',
        '       ra     1 0 d degrees ' + t['ra'].format,
        '       dec    2 0 d degrees ' + t['dec'].format,
        '       id     3 0 c INDEF   ' + t['objID'].format,
        '       u      4 0 r INDEF   ' + t['u'].format,
        '       uerr   5 0 r INDEF   ' + t['err_u'].format,
        '       g      6 0 r INDEF   ' + t['g'].format,
        '       gerr   7 0 r INDEF   ' + t['err_g'].format,
        '       r      8 0 r INDEF   ' + t['r'].format,
        '       rerr   9 0 r INDEF   ' + t['err_r'].format,
        '       i     10 0 r INDEF   ' + t['i'].format,
        '       ierr  11 0 r INDEF   ' + t['err_i'].format,
        '       z     12 0 r INDEF   ' + t['z'].format,
        '       zerr  13 0 r INDEF   ' + t['err_z'].format,
        'END CATALOG HEADER'
        ]
        t.write(output, format='ascii.no_header')
        print len(t), 'matching objects. Catalog saved to', output
    else:
        print 'No matching objects.'
