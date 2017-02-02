def xpa(arg):
    import subprocess
    subproc = subprocess.Popen('xpaset -p ds9 '+arg,shell=True)
    subproc.communicate()

def vizq(_ra,_dec,catalogue,radius):
    import os,string,re
    _site='vizier.u-strasbg.fr'
#    _site='vizier.cfa.harvard.edu'
    cat={'usnoa2':['I/252/out','USNO-A2.0','Rmag'],\
         '2mass':['II/246/out','2MASS','Jmag'],\
         'usnob1':['I/284/out','USNO-B1.0','R2mag'],\
         'apass':['I/322A/out','UCAC4','rmag,UCAC4'],\
         'sdss7':['II/294/sdss7','rmag','rmag']}
    a=os.popen('vizquery -mime=tsv  -site='+_site+' -source='+cat[catalogue][0]+\
                   ' -c.ra='+str(_ra)+' -c.dec='+str(_dec)+' -c.eq=J2000 -c.rm='+str(radius)+\
                   ' -c.geom=b -oc.form=h -sort=_RA*-c.eq -out.add=_RAJ2000,_DEJ2000 -out.max=10000 -out='+\
                   cat[catalogue][1]+' -out='+cat[catalogue][2]+'').read()
    aa=a.split('\n')
    bb=[]
    for i in aa:
        if i and i[0]!='#':   bb.append(i)
    _ra,_dec,_name,_mag=[],[],[],[]
    for ii in bb[3:]:
        aa=ii.split('\t')
        _ra.append(re.sub(' ',':',aa[0]))
        _dec.append(re.sub(' ',':',aa[1]))
        _name.append(aa[2])
        try:       _mag.append(float(aa[3]))
        except:    _mag.append(float(9999))
    return {'ra':_ra,'dec':_dec,'id':_name,'mag':_mag}

def wcsstart(img,CRPIX1='',CRPIX2=''):
    from numpy import pi, sin, cos 
    import lsc
    from lsc.util import updateheader,readhdr,readkey3
    hdr=readhdr(img)
    _instrume=readkey3(hdr,'instrume')
    _RA=readkey3(hdr,'RA')
    _DEC=readkey3(hdr,'DEC')
    _xdimen=readkey3(hdr,'NAXIS1')
    _ydimen=readkey3(hdr,'NAXIS2')
    _CCDXBIN=readkey3(hdr,'CCDXBIN')
    if _instrume in ['kb74','kb76']:
        angle=readkey3(hdr,'ROLLERDR')#posang)
        theta=(angle*pi/180.)
        CDELT0=0.000129722   # 1.3042840792028E-4   8.43604528922325E-5  #6.6888889999999995e-05
        CD1_1=(-1)*CDELT0*cos(theta)
        CD2_2=(-1)*CDELT0*cos(theta)
        CD1_2=abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
        CD2_1=(-1)*abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
        if not CRPIX1:        CRPIX1= readkey3(hdr,'ROTCENTX')
        else: CRPIX1= 1000.+CRPIX1
        if not CRPIX2:        CRPIX2= readkey3(hdr,'ROTCENTY')
        else: CRPIX2= 1000.+CRPIX2
        CDELT1=2
        CDELT2=2
    elif 'kb' in _instrume:
        angle=readkey3(hdr,'ROLLERDR')#posang)
        theta=(angle*pi/180.)
        CDELT0=0.000129722   # 1.3042840792028E-4   8.43604528922325E-5  #6.6888889999999995e-05
        CD1_1=(-1)*CDELT0*cos(theta)
        CD2_2=(-1)*CDELT0*cos(theta)
        CD1_2=abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
        CD2_1=(-1)*abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
        if not CRPIX1:        CRPIX1= 1000.
        else: CRPIX1= 1000.+CRPIX1
        if not CRPIX2:        CRPIX2= 1000.
        else: CRPIX2= 1000.+CRPIX2
        CDELT1=2
        CDELT2=2
    elif 'fl' in _instrume:
        angle=readkey3(hdr,'ROLLERDR')#posang)
        theta=(angle*pi/180.)
        pixscale=float(readkey3(hdr,'PIXSCALE'))
        CDELT0=pixscale/3600.
        CD1_1=CDELT0*cos(theta)
        CD1_2=CDELT0*sin(theta)
        CD2_1=CDELT0*sin(theta)
        CD2_2=(-1)*CDELT0*cos(theta)
        if 'SITEID' in hdr:
            if hdr['SITEID'] in ['elp']:
                CD1_1 = (-1) * CD1_1
                CD2_2 = (-1) * CD2_2
#        CD1_1=(-1)*CDELT0*cos(theta)
#        CD2_2=(-1)*CDELT0*cos(theta)
#        CD1_2=abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
#        CD2_1=(-1)*abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
        if not CRPIX1:        
            CRPIX1 = _xdimen/2
        else: 
            CRPIX1 = (_xdimen/2)+CRPIX1
        if not CRPIX2:        
            CRPIX2 = _ydimen/2
        else: CRPIX2 = (_ydimen/2)+CRPIX2
        CDELT1 = 2
        CDELT2 = 2
    elif _instrume in ['fs03']:
        angle=readkey3(hdr,'ROTSKYPA')#posang)
        theta=(angle*pi/180.)
 #       pixscale=0.30*_CCDXBIN
 #       CDELT0=pixscale/3600.
        CDELT0=0.000083705976   #8.43604528922325E-5  #6.6888889999999995e-05
        CD1_1=(-1)*CDELT0*cos(theta)
        CD2_2=CDELT0*cos(theta)
        CD1_2=abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
        CD2_1=abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
        if not CRPIX1:        CRPIX1= 1024.
        else: CRPIX1= 1024.+CRPIX1
        if not CRPIX2:        CRPIX2= 1024.
        else: CRPIX2= 1024.+CRPIX2
        CDELT1=0.000083705976*(-1)
        CDELT2=0.000083705976
    elif 'fs' in _instrume:
        angle=readkey3(hdr,'ROTSKYPA')#posang)
        theta=(angle*pi/180.)
 #       pixscale=0.30*_CCDXBIN
 #       CDELT0=pixscale/3600.
        CDELT0=0.000083568667  # 8.43604528922325E-5  #6.6888889999999995e-05
        CD1_1=(-1)*CDELT0*cos(theta)
        CD2_2=CDELT0*cos(theta)
        CD1_2=abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
        CD2_1=abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
        if not CRPIX1:        CRPIX1= 1024.
        else: CRPIX1= 1024.+CRPIX1
        if not CRPIX2:        CRPIX2= 1024.
        else: CRPIX2= 1024.+CRPIX2
        CDELT1=0.000083568694*(-1)
        CDELT2=0.000083568694
    elif 'em' in _instrume.lower():
        theta=(angle*pi/180.)
        CDELT0=7.63077724258886e-05 #7.7361111111111123e-05 
        CD1_1=(-1)*CDELT0*cos(theta)
        CD2_2=CDELT0*cos(theta)
        CD1_2=abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
        CD2_1=abs(CDELT0)*(abs(CDELT0)/CDELT0)*sin(theta)
        if not CRPIX1:        CRPIX1= readkey3(hdr,'ROTCENTX')
        if not CRPIX2:        CRPIX2= readkey3(hdr,'ROTCENTY')-100
        CDELT1=2
        CDELT2=2
    else:  print '\n### ERROR: instument not found !!!'

    CTYPE1  = 'RA---TAN'  
    CTYPE2  = 'DEC--TAN' 
    CRVAL1=_RA
    CRVAL2=_DEC
    WCSDIM  =                   2  
    LTM1_1  =                   1. 
    LTM2_2  =                   1.
    WAT0_001= 'system=image'
    WAT1_001= 'wtype=tan axtype=ra'
    WAT2_001= 'wtype=tan axtype=dec'
    lsc.util.updateheader(img,0,{'CTYPE1':[CTYPE1,''], 'CTYPE2':[CTYPE2,''], 'CRVAL1':[CRVAL1,''], 'CRVAL2':[CRVAL2,''],\
                'CRPIX1':[CRPIX1,''], 'CRPIX2':[CRPIX2,''], 'CDELT1':[CDELT1,''], 'CDELT2':[CDELT2,''],\
                'CD1_1':[CD1_1,''], 'CD2_2':[CD2_2,''], 'CD1_2':[CD1_2,''], 'CD2_1':[CD2_1,''],\
                'WCSDIM':[WCSDIM,'']})

##########################################################
###vizq(_ra,_dec,catalogue,radius):

def querycatalogue(catalogue,img,method='iraf'):
        from pyraf import iraf
        from numpy import array, compress
        import string,re,sys,os
        import lsc
        from lsc.util import delete
        from lsc.util import readhdr,readkey3
        hdr=readhdr(img)
        _ra=readkey3(hdr,'RA')
        _dec=readkey3(hdr,'DEC')
        _instrume=hdr.get('instrume')
        iraf.imcoords(_doprint=0)
        iraf.astcat(_doprint=0)
        if 'fl' in _instrume: # sinistro
            _size=40
        else:
            _size=20
        toforget = ['imcoords','astcat','tv']
        iraf.noao.astcat.aregpars.rcrauni=''
        iraf.noao.astcat.aregpars.rcdecuni=''
        iraf.noao.astcat.catdb=lsc.__path__[0]+'/standard/cat/catalogue.dat'
        iraf.noao.astcat.aregpars.rcra=_ra/15
        iraf.noao.astcat.aregpars.rcdec=_dec
        iraf.noao.astcat.aregpars.rrawidt=_size
        iraf.noao.astcat.aregpars.rdecwid=_size
        delete('tmp.catalogue')
        delete('tmp.catalogue.pix')
        if catalogue not in ['usnoa2','usnob1','2mass','apass']:
            if os.path.isfile(catalogue):
                stdcoo=lsc.lscastrodef.readtxt(catalogue)
                if len(stdcoo['ra']) == 0:
                    sys.exit('\n####  ERROR catalog empty: '+catalogue)

                for jj in ['V','R','I','r','g','i','z','U','B']:
                    if jj in stdcoo.keys():
                        colonne4={catalogue:jj}
                        if min(array(stdcoo[jj],float)) != 9999:
                            break
                        else:
                            print 'no magnitudes in this filter, try a different filter '+jj

                lll=['# END CATALOG HEADER','#']
                for ff in range(0,len(stdcoo['ra'])):
                    lll.append(str(stdcoo['ra'][ff])+'  '+str(stdcoo['dec'][ff])+'  '+str(stdcoo[jj][ff]))
                #colonne4={'usnoa2':'mag','usnob1':'mag','2mass':'mag','gsc1':'mag'}
                colonne3=' 1   2 '
                column={'ra':1,'dec':2,'r':3}
                print 'catalogue from user'
            else:
                sys.exit('Error: catalogue '+str(catalogue)+' not in the list [usnob1,usnoa2,2mass]')
        else:
          if method=='iraf':
            if catalogue=='usnoa2':    lll=iraf.noao.astcat.agetcat('pars','STDOUT',catalog='usno2@noao',verbose='no',Stdout=1)
            elif catalogue=='usnob1':  lll=iraf.noao.astcat.agetcat('pars','STDOUT',catalog='usnob1@noao',verbose='no',Stdout=1)
            elif catalogue=='2mass':   lll=iraf.noao.astcat.agetcat('pars','STDOUT',catalog='twomass@noao',verbose='no',Stdout=1)
#            elif catalogue=='gsc1':    lll=iraf.noao.astcat.agetcat('pars','STDOUT',catalog='gsc1@cadc',verbose='no',Stdout=1)
            else:
                sys.exit('Error: catalogue '+str(catalogue)+' not in the list [usnob1,usnoa2,2mass]')
########
            indfield=[i for i in range(0,len(lll)) if 'nfields' in lll[i]]
            fields=int(lll[indfield[0]].split()[-1])
            stdcoo={}
            column={}
            for j in range(indfield[0]+1,indfield[0]+fields+1):
                if lll[j].split()[1] not in column: column[lll[j].split()[1]]=int(lll[j].split()[2])
                if lll[j].split()[1] not in stdcoo: stdcoo[lll[j].split()[1]]=[]
            for i in lll[lll.index('# END CATALOG HEADER')+2:]:
                for j in stdcoo.keys():
                    stdcoo[j].append(i.split()[column[j]-1])
            colonne3=str(int(column['ra']))+' '+str(int(column['dec']))

            if catalogue in ['usnoa2','usnob1','2mass','gsc1','apass']:
                   colonne4={'usnoa2':'mag1','usnob1':'R2mag','2mass':'mag1','gsc1':'mag','apass':'mag'}
            else:  sys.exit('Error: catalogue '+str(catalogue)+' not in the list [usnob1,usnoa2,2mass,apass]')

          elif method=='vizir':
            stdcoo=lsc.lscastrodef.vizq(_ra,_dec,catalogue,_size)
            
            lll=['# END CATALOG HEADER','#']
            for ff in range(0,len(stdcoo['ra'])):
                lll.append(str(stdcoo['ra'][ff])+'  '+str(stdcoo['dec'][ff])+'  '+str(stdcoo['mag'][ff]))
            colonne4={'usnoa2':'mag','usnob1':'mag','2mass':'mag','gsc1':'mag','apass':'mag'}
            colonne3=' 1   2 '
            column={'ra':1,'dec':2,'r':3}

        if  string.count(stdcoo['ra'][0],':'):
            ddd2=iraf.wcsctran('STDIN','STDOUT',img + '[0]',Stdin=lll,Stdout=1,inwcs='world',units='hour degrees',outwcs='logical',columns=colonne3,formats='%10.1f %10.1f')
        else:
            ddd2=iraf.wcsctran('STDIN','STDOUT',img + '[0]',Stdin=lll,Stdout=1,inwcs='world',units='degree degrees',outwcs='logical',columns=colonne3,formats='%10.1f %10.1f')
        xx,yy=[],[]
        for i in ddd2[ddd2.index('# END CATALOG HEADER')+2:]:
            xx.append(float(i.split()[column['ra']-1]))
            yy.append(float(i.split()[column['dec']-1]))
#######
        acoo1=[]
        apixx1,apixy1,am1,apix1=[],[],[],[]
        for i in range(0,len(stdcoo['ra'])):
            acoo1.append(str(stdcoo['ra'][i])+' '+str(stdcoo['dec'][i]))
            apix1.append(str(xx[i])+' '+str(yy[i]))
            am1.append(stdcoo[colonne4[catalogue]][i])
            if  string.count(stdcoo['ra'][i],':'):
                stdcoo['ra'][i]=(int(string.split(stdcoo['ra'][i],':')[0])+float(string.split(stdcoo['ra'][i],':')[1])/60+float(string.split(stdcoo['ra'][i],':')[2])/3600.)*15
                if string.count(str(stdcoo['dec'][i]),'-')==0:   
                    stdcoo['dec'][i]=int(string.split(stdcoo['dec'][i],':')[0])+float(string.split(stdcoo['dec'][i],':')[1])/60+float(string.split(stdcoo['dec'][i],':')[2])/3600.
                else:
                    stdcoo['dec'][i]=(-1)*(abs(int(string.split(stdcoo['dec'][i],':')[0]))+float(string.split(stdcoo['dec'][i],':')[1])/60+float(string.split(stdcoo['dec'][i],':')[2])/3600.)


        stdcoo['ra']=array(stdcoo['ra'],float)
        stdcoo['dec']=array(stdcoo['dec'],float)

        if catalogue=='2mass':
            for jj in range(0,len(am1)):
                    try: am1[jj]=float(re.sub('L','',str(am1[jj])))
                    except: am1[jj]=999

        for key in stdcoo.keys():
            try:
                stdcoo[key]=compress((array(xx)<int(int(hdr['NAXIS1'])+100))&(array(xx)>-100)&(array(yy)<int(int(hdr['NAXIS2'])+100))&(array(yy)>-100),array(stdcoo[key]))
            except:  pass
        stdcoo['coo']=compress((array(xx)<int(int(hdr['NAXIS1'])+100))&(array(xx)>-100)&(array(yy)<int(int(hdr['NAXIS2'])+100))&(array(yy)>-100),array(acoo1))
        stdcoo['pix']=compress((array(xx)<int(int(hdr['NAXIS1'])+100))&(array(xx)>-100)&(array(yy)<int(int(hdr['NAXIS2'])+100))&(array(yy)>-100),array(apix1))
        stdcoo['mag']=compress((array(xx)<int(int(hdr['NAXIS1'])+100))&(array(xx)>-100)&(array(yy)<int(int(hdr['NAXIS2'])+100))&(array(yy)>-100),array(am1,float))
        stdcoo['x']=compress((array(xx)<int(int(hdr['NAXIS1'])+100))&(array(xx)>-100)&(array(yy)<int(int(hdr['NAXIS2'])+100))&(array(yy)>-100),array(xx,float))
        stdcoo['y']=compress((array(xx)<int(int(hdr['NAXIS1'])+100))&(array(xx)>-100)&(array(yy)<int(int(hdr['NAXIS2'])+100))&(array(yy)>-100),array(yy,float))

        return stdcoo
#############################################################

def lscastroloop(imglist,catalogue,_interactive,number1,number2,number3,_fitgeo,_tollerance1,_tollerance2,sexvec='',_guess=False,_numin=4,method='iraf',xshift=0,yshift=0):
    import lsc
    from lsc.util import delete,readkey3,readhdr
    from lsc.lscastrodef import lscastrometry2
    from numpy import median, array
    import math
    import datetime
    import time
    import sys
#    from datetime import datetime
    _imex=False
    for img in imglist:
        hdr=readhdr(img)
        _instrume=readkey3(hdr,'instrume')
        if not sexvec:
            sexvec=lsc.lscastrodef.sextractor(img)
###################
        print xshift,yshift
        if xshift!=0 and yshift!=0:
            print 'guess astrometry before starting '
            lsc.lscastrodef.wcsstart(img,xshift,yshift)
#        ss=datetime.datetime.now()
#        time.sleep(1)
        catvec=lsc.lscastrodef.querycatalogue(catalogue,img,method)
        if len(catvec['ra']) == 0:
            print 'cazzo'
            sys.exit('ERROR: catalog empty '+catalogue)
        rmsx1,rmsy1,num1,fwhm1,ell1,ccc,bkg1,rasys1,decsys1=lscastrometry2([img],catalogue,_interactive,number1,sexvec,catvec,guess=False,fitgeo=_fitgeo,\
                                                                                 tollerance1=_tollerance1, tollerance2=_tollerance2,_update='yes',imex=_imex,nummin=_numin)
        if rmsx1>1 or rmsy1>1:
            catvec=lsc.lscastrodef.querycatalogue(catalogue,img,method)
            rmsx2,rmsy2,num2,fwhm2,ell2,ccc,bkg2,rasys2,decsys2=lscastrometry2([img],catalogue,_interactive,number2,sexvec,catvec,guess=False,fitgeo=_fitgeo,\
                                                                                     tollerance1=_tollerance1, tollerance2=_tollerance2,_update='yes',imex=_imex,nummin=_numin)
            if rmsx2>1 or rmsy2>1:
                catvec=lsc.lscastrodef.querycatalogue(catalogue,img,method)
                rmsx3,rmsy3,num3,fwhm3,ell3,ccc,bkg3,rasys3,decsys3=lscastrometry2([img],catalogue,_interactive,number3,sexvec,catvec,guess=False,fitgeo=_fitgeo,\
                                                                                         tollerance1=_tollerance1, tollerance2=_tollerance2,_update='yes',imex=_imex,nummin=_numin)
            else:  rmsx3,rmsy3,num3,fwhm3,ell3,ccc,bkg3,rasys3,decsys3=rmsx2,rmsy2,num2,fwhm2,ell2,ccc,bkg2,rasys2,decsys2
        else:  rmsx3,rmsy3,num3,fwhm3,ell3,ccc,bkg3,rasys3,decsys3=rmsx1,rmsy1,num1,fwhm1,ell1,ccc,bkg1,rasys1,decsys1
######################################## 
        if rmsx3 < 10 and rmsy3 < 10: 
            if 'kb' in _instrume:
                fwhmgess3=median(array(fwhm3))*.68*2.35*0.467
                if _imex:  fwhmgessime = median(array(ccc))*0.467
                else:     fwhmgessime = 9999
            elif 'fl' in _instrume:
                fwhmgess3=median(array(fwhm3))*.68*2.35*0.467          #  need to check
                if _imex:  fwhmgessime = median(array(ccc))*0.467
                else:     fwhmgessime = 9999
            elif 'fs' in _instrume:
                fwhmgess3=median(array(fwhm3))*.68*2.35*0.30
                if _imex:  fwhmgessime = median(array(ccc))*0.30
                else:     fwhmgessime = 9999
            elif 'em' in _instrume:
                fwhmgess3=median(array(fwhm3))*.68*2.35*0.278
                if _imex:  fwhmgessime = median(array(ccc))*0.278  
                else:     fwhmgessime = 9999
            ellgess3=median(array(ell3))
        else:
            fwhmgess3=9999
            fwhmgessime=9999
            ellgess3=9999
        if _instrume[:2] in ['kb', 'fl', 'fs', 'em']:
            mbkg3=median(bkg3)
            lsc.util.updateheader(img,0,{'MBKG':[mbkg3,'background level']})
        else:
            mbkg3=readkey3(hdr,'MBKG')
        if fwhmgess3:
            if _instrume[:2] in ['kb', 'fl', 'fs', 'em']:
                V=(math.pi/(4*math.log(2)))*(45000-float(mbkg3))*(float(fwhmgess3)**2)
            else:                     
                V=(math.pi/(4*math.log(2)))*(32000-float(mbkg3))*(float(fwhmgess3)**2)
            magsat=-2.5*math.log10(V)
        else:        magsat=9999
    print rmsx3,rmsy3,num3,fwhmgess3,ellgess3,fwhmgessime,rasys3,decsys3,magsat
    return  rmsx3,rmsy3,num3,fwhmgess3,ellgess3,fwhmgessime,rasys3,decsys3,magsat

#################################################################################################
############################################################################################################
def lscastrometry2(lista,catalogue,_interactive,number,sexvec,catvec,guess=False,fitgeo='xyscale', tollerance1=100, tollerance2=30, _update='yes',imex=False,nummin=4):
    import os,string,re,sys
    import numpy
    import math
    from numpy import array, compress, argsort, sort, asarray
    from numpy import round, mean, std, sqrt, median
    from numpy import argmin, isnan, abs, genfromtxt
    import lsc
    import time
    import datetime
    from lsc.lscastrodef import wcsstart
    from lsc.util import delete, readhdr,readkey3, display_image, defsex
    from pyraf import iraf
    xpix,ypix,fw,cl,cm,ell,bkg,fl=sexvec
    acoo1,apix1,am1=catvec['coo'],catvec['pix'],catvec['mag']
########################   catalogue
    iraf.noao(_doprint=0)
    iraf.imcoords(_doprint=0)
    iraf.tv(_doprint=0)
    iraf.tv.rimexam.backgrou = 'yes'
    iraf.astcat(_doprint=0)
    toforget = ['imcoords','astcat','tv']
    for t in toforget: iraf.unlearn(t)
    verbose=False
    if _interactive: verbose=True
    img=lista[0]
    hdr=readhdr(img)
    _instrume=readkey3(hdr,'instrume')
    magsel0 = 7.
    magsel1 = 21.
    _CRPIX1=readkey3(hdr,'CRPIX1')
    _CRPIX2=readkey3(hdr,'CRPIX2')
    if verbose:            display_image(img,1,'','',False)
    if verbose:
            iraf.tvmark(1,'STDIN',Stdin=list(apix1),mark="circle",number='no',label='no',radii=10,nxoffse=5,nyoffse=5,color=205,txsize=4)
            raw_input('mark catalogue '+str(len(apix1)))
    else:  
#        ss=datetime.datetime.now()
        time.sleep(.7)
    answ='yes'
    magsel11=magsel1
    mlim=0
    while answ=='yes':
        amcut1=compress((array(am1)>=magsel0) &(array(am1)<=magsel11), am1)
        if len(amcut1)<=number:    
            answ='no'
            magsel11=magsel1+mlim+.5   
        else:
            mlim=mlim-.5
            magsel11=magsel1+mlim

    amcut=compress((array(am1)>magsel0) &(array(am1)<magsel11), am1)
    apixcut=compress((array(am1)>magsel0) &(array(am1)<magsel11), apix1)      #   usno x y  cut_list
    acoocut=compress((array(am1)>magsel0) &(array(am1)<magsel11), acoo1)  #   usno ra dec  cut_list

    rausno=compress((array(am1)>magsel0) &(array(am1)<magsel11), array(catvec['ra'],float)) 
    decusno=compress((array(am1)>magsel0) &(array(am1)<magsel11), array(catvec['dec'],float)) 
    xusno,yusno=[],[]
    for i in apixcut:
            xusno.append(float(string.split(i)[0]))
            yusno.append(float(string.split(i)[1]))
    xusno,yusno=array(xusno),array(yusno)
    
#################################################################
    if verbose:
            iraf.tvmark(1,'STDIN',Stdin=list(apixcut),mark="circle",number='yes',label='no',radii=12,nxoffse=5,nyoffse=5,color=204,txsize=3)
            raw_input('brightest '+str(number)+' objects')

##############    sextractor   ##################
    if len(xpix)>=number:
            cm=array(cm,float)
            xpix=xpix[argsort(cm)][0:number]
            ypix=ypix[argsort(cm)][0:number]
            fw=fw[argsort(cm)][0:number]
            ell=ell[argsort(cm)][0:number]
            cm=cm[argsort(cm)][0:number]
    if verbose:
            sexpix=[]
            for i in range(0,len(xpix)):
                sexpix.append(str(xpix[i])+' '+str(ypix[i]))
            iraf.tvmark(1,'STDIN',Stdin=list(sexpix),mark="circle",number='no',label='no',radii=8,nxoffse=5,nyoffse=5,color=206,txsize=2)
            raw_input('print sex '+str(len(sexpix)))

    xsex,ysex=array(xpix),array(ypix)
    fwsex=array(fw)
    ellsex=array(ell)
#####################################################################
    max_sep=tollerance1
    xdist,ydist=[],[]
    for i in range(len(xusno)):
            dist = sqrt((xusno[i]-xsex)**2+(yusno[i]-ysex)**2)
            idist = argmin(dist)
            if dist[idist]<max_sep:
                xdist.append(xusno[i]-xsex[idist])
                ydist.append(yusno[i]-ysex[idist])
    xoff,xstd = round(median(xdist),2),round(std(xdist),2)
    yoff,ystd = round(median(ydist),2),round(std(ydist),2)
    _xdist,_ydist = array(xdist),array(ydist)
    __xdist = compress((abs(_xdist-xoff)<3*xstd)&(abs(_ydist-yoff)<3*ystd),_xdist)
    __ydist = compress((abs(_xdist-xoff)<3*xstd)&(abs(_ydist-yoff)<3*ystd),_ydist)
    xoff,xstd = round(median(__xdist),2),round(std(__xdist),2)
    yoff,ystd = round(median(__ydist),2),round(std(__ydist),2)
    if isnan(xoff): xoff=0
    if isnan(yoff): yoff=0
    _CRPIX1=readkey3(hdr,'CRPIX1')
    _CRPIX2=readkey3(hdr,'CRPIX2')
    lsc.util.updateheader(img,0,{'CRPIX1':[_CRPIX1-xoff,'']})
    lsc.util.updateheader(img,0,{'CRPIX2':[_CRPIX2-yoff,'']})
    xusno2_new=xusno-xoff
    yusno2_new=yusno-yoff
#####################################################################
    max_sep=tollerance2
    fwhm=[]
    fwhm2=[]
    ell=[]
    xref=[]
    iraf.tv(_doprint=0)
    iraf.tv.rimexam.backgrou = 'yes'
    vettoretran=[]
    for i in range(len(xusno2_new)):
            dist = sqrt((xusno2_new[i]-xsex)**2+(yusno2_new[i]-ysex)**2)
            idist = argmin(dist)
            if dist[idist]<max_sep:
                xref.append(xsex[idist])
                vettoretran.append(str(rausno[i])+' '+str(decusno[i])+' '+str(xsex[idist])+' '+str(ysex[idist])+' \n')
                fwhm.append(fwsex[idist])
                ell.append(ellsex[idist])
                if imex:
                    gg=open('tmp.one','w')
                    gg.write(str(xsex[idist])+' '+str(ysex[idist])+'\n')
                    gg.close()
                    ime=iraf.imexam(input=img, frame=1, logfile='', keeplog='yes', imagecur='tmp.one', wcs='logical', use_disp='no',Stdout=1)
                    try:
                        _fwhm2=median(compress(array(string.split(ime[3])[-3:],float)<99,(array(string.split(ime[3])[-3:],float))))
                        fwhm2.append(_fwhm2)
                    except: pass
    if len(xref)>=nummin:
            _ccmap1=iraf.ccmap('STDIN','STDOUT',images=img,Stdin=vettoretran,fitgeome=fitgeo,xcolum=3, xxorder=2,\
                               yyorder=2, ycolum=4,lngcolum=1,latcolumn=2,lngunit='degrees',update='No',interact='No',maxiter=3,Stdout=1)
            if 'rms' in _ccmap1[_ccmap1.index('Wcs mapping status')+1]:
                try:           rmsx,rmsy=array(string.split(string.split(_ccmap1[_ccmap1.index('Wcs mapping status')+1],':')[-1])[0:2],float)
                except:        rmsx,rmsy=array(string.split(string.split(_ccmap1[_ccmap1.index('Wcs mapping status')+1],':')[-1])[0:2])
                if rmsx<2 and rmsy<2:
                    print '\n### update astrometry with non linear order' 
#                    raw_input('go on ')
                    _ccmap1=iraf.ccmap('STDIN','STDOUT',images=img,Stdin=vettoretran,fitgeome=fitgeo,xcolum=3, xxorder=2,\
                                       yyorder=2, ycolum=4,lngcolum=1,latcolumn=2,lngunit='degrees',update='Yes',interact='No',maxiter=3,Stdout=1)
                    xy = iraf.wcsctran('STDIN',output="STDOUT",Stdin=vettoretran,Stdout=1,image=img + '[0]',inwcs='physical', outwcs='world',column="3 4",formats='%10.6f %10.6f',verbose='yes')[3:]
                    rasys=median(array([float(xy[i].split()[2])-float(xy[i].split()[0]) for i in range(0, len(xy)) ]))
                    decsys=median(array([float(xy[i].split()[3])-float(xy[i].split()[1]) for i in range(0, len(xy)) ]))
                else:
                    rasys,decsys=999,999
            else:      rmsx,rmsy,rasys,decsys=999,999,999,999
    else:
            rmsx,rmsy=990,999
            rasys,decsys=999,999
    return rmsx,rmsy,len(xref),fwhm,ell,fwhm2,bkg,rasys,decsys
##########################################################################

def readtxt(ascifile):
    import string
    f=open(ascifile,'r')
    ss=f.readlines()
    f.close()
    columnname=[]
    for i in range(0,len(ss)):
        if  ss[i][0]=='#' and 'nfields' in ss[i] :
            num=int(string.split(ss[i])[-1])
            for g in range(1,num+1):
                columnname.append(string.split(ss[i+g])[1])
            break
    ascidic={}
    try:
        from numpy import genfromtxt
        data=genfromtxt(ascifile,str,unpack=True)
        for i in range(0,len(columnname)):
            ascidic[columnname[i]]=data[i]
            ascidic[columnname[i]+'pos']=i+1
    except:
        for j in columnname:     ascidic[j]=[]
        for j in range(0,len(columnname)):
            ascidic[columnname[j]+'pos']=j+1
            for i in range(0,len(ss)):
                if  ss[i][0]!='#':
                    ascidic[columnname[j]].append(string.split(ss[i])[j])     
    return ascidic

#########################################################################

def zeropoint(img,_field,verbose=False,catalogue=''):
    import string,os,re,sys
    from numpy import compress, array, median, zeros, abs
    import math
    import lsc
    from lsc.util import delete,readhdr,readkey3
    from lsc import sqlcl
    from pyraf import iraf
    iraf.noao(_doprint=0)
    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    iraf.images(_doprint=0)
    iraf.imcoords(_doprint=0)
    iraf.proto(_doprint=0)
    hdr=readhdr(img)
    _airmass=readkey3(hdr,'AIRMASS')
    if not _airmass: 
        print '\n### warning: airmass at starting exposure'
        _airmass=readkey3(hdr,'airmass')
    _exptime=readkey3(hdr,'exptime')
    _filter=readkey3(hdr,'filter')
    _instrume=readkey3(hdr,'instrume')
    _date=readkey3(hdr,'date-night')
    _object=readkey3(hdr,'object')
    _siteid = hdr['SITEID']
    if _siteid in lsc.sites.extinction:
        kk = lsc.sites.extinction[_siteid]
    else:
        print _siteid
        sys.exit('siteid not in lsc.sites.extinction')
    if 1==1:
        if catalogue:
            stdcooC=lsc.lscastrodef.readtxt(lsc.__path__[0]+'/standard/cat/'+catalogue+'.cat')
            rastdC,decstdC=array(stdcooC['ra'],float),array(stdcooC['dec'],float)
            delete('tmp.stdC.pix')
            iraf.wcsctran(lsc.__path__[0]+'/standard/cat/'+catalogue+'.cat','tmp.stdC.pix',img + '[0]',inwcs='world',units='degrees degrees',outwcs='logical',\
                              columns='1 2',formats='%10.1f %10.1f',verbose='no')
            standardpixC=lsc.lscastrodef.readtxt('tmp.stdC.pix')
            xstdC=standardpixC['ra']
            ystdC=standardpixC['dec']
            idstdC=standardpixC['id']
            xstdC=compress((array(xstdC,float)<readkey3(hdr,'naxis1'))&(array(xstdC,float)>0)&(array(ystdC,float)>0)&(array(ystdC,float)<readkey3(hdr,'naxis2')),xstdC)
        else:   xstdC,ystdC,idstdC=[],[],[]
        ######## check if it is landolt field
        stdcooL=lsc.lscastrodef.readtxt(lsc.__path__[0]+'/standard/cat/landolt.cat')
        rastdL,decstdL=array(stdcooL['ra'],float),array(stdcooL['dec'],float)
        delete('tmp.stdL.pix')
        iraf.wcsctran(lsc.__path__[0]+'/standard/cat/landolt.cat','tmp.stdL.pix',img + '[0]',inwcs='world',units='degrees degrees',outwcs='logical',\
                          columns='1 2',formats='%10.1f %10.1f',verbose='no')
        standardpixL=lsc.lscastrodef.readtxt('tmp.stdL.pix')
        xstdL=standardpixL['ra']
        ystdL=standardpixL['dec']
        idstdL=standardpixL['id']
        xstdL=compress((array(xstdL,float)<readkey3(hdr,'naxis1'))&(array(xstdL,float)>0)&(array(ystdL,float)>0)&(array(ystdL,float)<readkey3(hdr,'naxis2')),xstdL)
###############################################
        ######## check if it is sloan field
        _ra=readkey3(hdr,'RA')
        _dec=readkey3(hdr,'DEC')
        magsel0,magsel1=12,18
        print _ra,_dec
        print 'sloan to file take degree degree'
        _ids=lsc.lscastrodef.sloan2file(_ra,_dec,20,float(magsel0),float(magsel1),'_tmpsloan.cat')
        ascifile='_tmpsloan.cat'
        stdcooS=lsc.lscastrodef.readtxt(ascifile)
        rastdS,decstdS=array(stdcooS['ra'],float),array(stdcooS['dec'],float)
        delete('tmp.stdS.pix')
        iraf.wcsctran(ascifile,'tmp.stdS.pix',img + '[0]',inwcs='world',units='degrees degrees',outwcs='logical',columns='1 2',formats='%10.1f %10.1f',verbose='no')
        standardpixS=lsc.lscastrodef.readtxt('tmp.stdS.pix')
        xstdS=standardpixS['ra']
        ystdS=standardpixS['dec']
        idstdS=standardpixS['id']
        xstdS=compress((array(xstdS,float)<readkey3(hdr,'naxis1'))&(array(xstdS,float)>0)&(array(ystdS,float)>0)&(array(ystdS,float)<readkey3(hdr,'naxis2')),xstdS)
       ##############
        print _filter
        if _filter in ['B', 'V', 'R', 'I']:
            if _field=='sloan':   standardpix,stdcoo={'ra':[9999],'dec':[9999],'id':[1]},{'ra':[9999],'dec':[9999]}
            else:
                _field='landolt'
                filters={'U':'U', 'B':'B', 'V':'V', 'R':'R', 'I':'I'}
                colors={'U':['UB'],'B':['BV'],'V':['BV','VR'],'R':['VR','RI'],'I':['VI','RI']}
                if catalogue:
                    standardpix=standardpixC
                    stdcoo=stdcooC
                else:
                    if len(xstdL)>=1:
                        standardpix=standardpixL
                        stdcoo=stdcooL
                    elif len(xstdS)>=1:    
                        standardpix=standardpixS
                        stdcoo=stdcooS
                        stdcoo=lsc.lscastrodef.transformsloanlandolt(stdcoo)
                        print '\n### transform sloan in landolt'
                    else:    standardpix,stdcoo={'ra':[9999],'dec':[9999],'id':[1]},{'ra':[9999],'dec':[9999]}
        elif _filter in  ['SDSS-U','SDSS-G','SDSS-R','SDSS-I','Pan-Starrs-Z']: 
            if _field=='landolt':   standardpix,stdcoo={'ra':[9999],'dec':[9999],'id':[1]},{'ra':[9999],'dec':[9999]}
            else:
                _field='sloan'
                filters={'u':'u','i':'i','g':'g','r':'r','z':'z'}
                colors={'u':['ug'],'i':['iz','ri'],'r':['gr','ri'],'g':['gr'],'z':['rz','iz']}
                if catalogue:
                    standardpix=standardpixC
                    stdcoo=stdcooC
                else:
                    if len(xstdS)>=1:
                        standardpix=standardpixS
                        stdcoo=stdcooS
                    elif len(xstdL)>=1:
                        standardpix=standardpixL
                        stdcoo=stdcooL
                        stdcoo=lsc.lscastrodef.transformlandoltsloan(stdcoo)
                        print '\n### transform landolt to sloan'
                    else:   standardpix,stdcoo={'ra':[9999],'dec':[9999],'id':[1]},{'ra':[9999],'dec':[9999]}

    xstd=standardpix['ra']
    ystd=standardpix['dec']
    idstd=standardpix['id']
    rastd,decstd=array(stdcoo['ra'],float),array(stdcoo['dec'],float)

    xstd0=compress((array(xstd,float)<readkey3(hdr,'naxis1'))&(array(xstd,float)>0)&(array(ystd,float)>0)&(array(ystd,float)<readkey3(hdr,'naxis2')),xstd)
    if len(xstd0)>1:  ########   go only if standard stars are in the field  ##########
        magstd0={}
        airmass0={}
        print '\n###  standard field: '+str(_field)
        ###############  sextractor on standard field
        namesex=lsc.util.defsex('default.sex')
        os.system("sex '"+img+"[0]' -c "+namesex+" > _logsex")
        delete(namesex)
        delete('_logsex')
        xsex=iraf.proto.fields('detections.cat',fields='2',Stdout=1)
        ysex=iraf.proto.fields('detections.cat',fields='3',Stdout=1)
        fw=iraf.proto.fields('detections.cat',fields='8',Stdout=1)
        flags=iraf.proto.fields('detections.cat',fields='6',Stdout=1)

        xsex=compress(array(flags)==0,array(xsex))
        ysex=compress(array(flags)==0,array(ysex))
        fw=compress(array(flags)==0,array(fw))

        f=open('detection_sex.pix','w')
        for i in range(0,len(xsex)):
            f.write(str(xsex[i])+' '+str(ysex[i])+'\n')
        f.close()
        delete('detection_sex.coo')
        iraf.wcsctran('detection_sex.pix','detection_sex.coo',img + '[0]',inwcs='logical',units='degrees degrees',outwcs='world',columns='1 2',formats='%10.8f %10.8f')
        rasex=compress(array(iraf.proto.fields('detection_sex.coo',fields='1',Stdout=1))!='',array(iraf.proto.fields('detection_sex.coo',fields='1',Stdout=1)))
        decsex=compress(array(iraf.proto.fields('detection_sex.coo',fields='2',Stdout=1))!='',array(iraf.proto.fields('detection_sex.coo',fields='2',Stdout=1)))
        rasex=array(rasex,float)
        decsex=array(decsex,float)
        result={}
        fileph={}
        ystd0=compress((array(xstd,float)<readkey3(hdr,'naxis1'))&(array(xstd,float)>0)&(array(ystd,float)>0)\
                               &(array(ystd,float)<readkey3(hdr,'naxis2')),ystd)
        rastd0=compress((array(xstd,float)<readkey3(hdr,'naxis1'))&(array(xstd,float)>0)&(array(ystd,float)>0)\
                                &(array(ystd,float)<readkey3(hdr,'naxis2')),rastd)
        decstd0=compress((array(xstd,float)<readkey3(hdr,'naxis1'))&(array(xstd,float)>0)&(array(ystd,float)>0)\
                                 &(array(ystd,float)<readkey3(hdr,'naxis2')),decstd)
        idstd0=compress((array(xstd,float)<readkey3(hdr,'naxis1'))&(array(xstd,float)>0)&(array(ystd,float)>0)\
                                 &(array(ystd,float)<readkey3(hdr,'naxis2')),idstd)
        ###################
        colorvec=colors[filters[_filter]]
        if _field=='landolt':
            print '\n###  landolt system'
            for _filtlandolt in 'UBVRI':
                if _filtlandolt==filters[_filter]: airmass0[_filtlandolt]=_airmass
                else: airmass0[_filtlandolt]=1
                magstd0[_filtlandolt]=compress((array(xstd,float)<readkey3(hdr,'naxis1'))&(array(xstd,float)>0)&(array(ystd,float)>0)\
                                 &(array(ystd,float)<readkey3(hdr,'naxis2')),stdcoo[_filtlandolt])
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
            print _filter
            for _filtsloan in 'ugriz':
                if _filtsloan==filters[_filter]: airmass0[_filtsloan]=_airmass
                else: airmass0[_filtsloan]=1
                magstd0[_filtsloan]=compress((array(xstd,float)<readkey3(hdr,'naxis1'))&(array(xstd,float)>0)&(array(ystd,float)>0)\
                                 &(array(ystd,float)<readkey3(hdr,'naxis2')),stdcoo[_filtsloan])
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
        distvec,pos0,pos1=lsc.lscastrodef.crossmatch(array(rastd0),array(decstd0),array(rasex),array(decsex),10) 
        fwhm0=(median(array(fw,float)[pos1]))*.68*2.35
        print '\n fwhm = '+str(fwhm0)
        iraf.noao.digiphot.mode='h'
        iraf.noao.digiphot.daophot.photpars.zmag = 0
        iraf.noao.digiphot.daophot.daopars.psfrad = fwhm0*4
        iraf.noao.digiphot.daophot.daopars.fitrad = fwhm0
        iraf.noao.digiphot.daophot.daopars.sannulus = fwhm0*4
        iraf.noao.digiphot.daophot.fitskypars.annulus = fwhm0*4
        iraf.noao.digiphot.daophot.photpars.apertures = fwhm0*3
        iraf.noao.digiphot.daophot.datapars.readnoi = readkey3(hdr,'ron')
        iraf.noao.digiphot.daophot.datapars.epadu = readkey3(hdr,'gain')
        iraf.noao.digiphot.daophot.datapars.datamin = -1000
        iraf.noao.digiphot.daophot.datapars.datamax = 45000
        iraf.noao.digiphot.daophot.datapars.exposure = 'EXPTIME'
        iraf.noao.digiphot.daophot.datapars.airmass =  'AIRMASS'
        iraf.noao.digiphot.daophot.datapars.filter =   'filter2'
        iraf.noao.digiphot.daophot.daopars.function = 'gauss'
        iraf.noao.digiphot.daophot.daopars.varord = 0
        iraf.noao.digiphot.daophot.daopars.fitsky = 'yes'
        iraf.noao.digiphot.daophot.daopars.recenter = 'yes'
        zero=[]

        fil = open(re.sub('.fits','.ph',img),'w')
        fil.write(str(_instrume)+' '+str(_date)+'\n')
        fil.write('*** '+_object+' '+str(len(pos1))+'\n')
        if _field=='landolt':
            fil.write('%6.6s\t%6.6s\t%6.6s\t%6.6s\t%6.6s\n' % (str(1),str(1),str(1),str(1),str(1)))  # exptime
            fil.write('%6.6s\t%6.6s\t%6.6s\t%6.6s\t%6.6s\n' % (str(airmass0['U']),str(airmass0['B']),str(airmass0['V']),str(airmass0['R']),str(airmass0['I'])))
        elif _field=='sloan':
            fil.write('%6.6s\t%6.6s\t%6.6s\t%6.6s\t%6.6s\n' % (str(1),str(1),str(1),str(1),str(1)))  # exptime
            fil.write('%6.6s\t%6.6s\t%6.6s\t%6.6s\t%6.6s\n' % (str(airmass0['u']),str(airmass0['g']),str(airmass0['r']),str(airmass0['i']),str(airmass0['z'])))
        elif _field=='2mass':
            fil.write('%6.6s\t%6.6s\t%6.6s\n' % (str(1),str(1),str(1)))  # exptime
            fil.write('%6.6s\t%6.6s\t%6.6s\n' % (str(airmass0['J']),str(airmass0['H']),str(airmass0['K'])))

        print '\n KK   filter airmass \n '
        print str(kk[filters[_filter]]),str(filters[_filter]),str(_airmass)
        for i in range(0,len(pos1)): 
            gg=open('tmp.one','w')
            gg.write(str(xsex[pos1[i]])+' '+str(ysex[pos1[i]])+'\n')
            gg.close()               
            try:
                phot=iraf.noao.digiphot.daophot.phot(image=img, output='', coords='tmp.one', verify='no', interactive='no',Stdout=1)
                mag0=float(string.split(phot[0])[4])
                mag=mag0-kk[filters[_filter]]*float(_airmass)#+2.5*math.log10(float(_exptime))
            except:
                mag0=999
                mag=999

            jj=pos0[i]
            fileph['m'+filters[_filter]][jj]=mag0    #  instrumental mangitude of std in pos0[i]
            if _field=='landolt':
                stringastandard='%12.12s\t%7.7s\t%7.7s\t%7.7s\t%7.7s\t%7.7s' % (idstd0[jj],fileph['V'][jj],fileph['BV'][jj],fileph['UB'][jj],\
                                                                                fileph['VR'][jj],fileph['RI'][jj])
                fil.write('%7.7s\t%7.7s\t%7.7s\t%7.7s\t%7.7s\t%60.60s\n' \
                              % (str(fileph['mU'][jj]),str(fileph['mB'][jj]),str(fileph['mV'][jj]),str(fileph['mR'][jj]),str(fileph['mI'][jj]),str(stringastandard)))
            elif _field=='sloan':
                stringastandard='%12.12s\t%7.7s\t%7.7s\t%7.7s\t%7.7s\t%7.7s' % (idstd0[jj],fileph['r'][jj],fileph['gr'][jj],fileph['ug'][jj],\
                                                                                fileph['ri'][jj],fileph['iz'][jj])
                fil.write('%7.7s\t%7.7s\t%7.7s\t%7.7s\t%7.7s\t%60.60s\n' \
                              % (str(fileph['mu'][jj]),str(fileph['mg'][jj]),str(fileph['mr'][jj]),str(fileph['mi'][jj]),str(fileph['mz'][jj]),str(stringastandard)))
#            elif _field=='2mass':
#                stringastandard='%12.12s\t%7.7s\t%7.7s\t%7.7s' % (idstd0[jj],fileph['J'][jj],fileph['JH'][jj],fileph['HK'][jj])
#                fil.write('%7.7s\t%7.7s\t%7.7s\t%60.60s\n' \
#                              % (str(fileph['mJ'][jj]),str(fileph['mH'][jj]),str(fileph['mK'][jj]),str(stringastandard)))
            zero.append(float(float(magstd0[filters[_filter]][jj]))-float(mag))

        fil.close()

        for col in colorvec:
            col0=compress((array(xstd,float)<readkey3(hdr,'naxis1'))&(array(xstd,float)>0)&(array(ystd,float)>0)&(array(ystd,float)<readkey3(hdr,'naxis2')),stdcoo[col[0]]) 
            col1=compress((array(xstd,float)<readkey3(hdr,'naxis1'))&(array(xstd,float)>0)&(array(ystd,float)>0)&(array(ystd,float)<readkey3(hdr,'naxis2')),stdcoo[col[1]])
            colstd0=array(col0,float)-array(col1,float)
            ################## sex  ######################
            colore=[]
            for i in range(0,len(pos1)):   colore.append(colstd0[pos0[i]])
            colore=compress(abs(array(zero))<50,array(colore))
            zero=compress(abs(array(zero))<50,array(zero))
            if len(colore)==0:
                    b,a,RR=9999,9999,9999
                    result=''
                    print 'no calibration, '+_filter+' '+_field
            elif len(colore)>1:
                lsc.util.updateheader(img,0,{'PHOTZP':[median(zero),'MAG=-2.5*log(data)+PHOTZP ']})
                if _field=='landolt':      a, b, RR=lsc.lscastrodef.linreg(colore, zero)
#                elif _field=='sloan':      b,a,RR=median(zero),0,0
                elif _field=='sloan':      a, b, RR=lsc.lscastrodef.linreg(colore, zero)
                xx=[min(array(colore)),max(array(colore))]
                yy=lsc.lscastrodef.pval(array(xx),[b,a])
                result[filters[_filter]+col]=[a,b,RR]
            else: 
                lsc.util.updateheader(img,0,{'PHOTZP':[zero[0],'MAG=-2.5*log(data)+PHOTZP']})
                b,a,RR=zero[0],0,0
                xx=colore
                yy=zero
                result[filters[_filter]+col]=[0,zero[0],0]                    
            if len(colore)>=1:
                if _field=='landolt':     lsc.util.updateheader(img,0,{'PHOTSYS':['VEGA','mags (landolt catalogue)']})
                elif _field=='sloan':     lsc.util.updateheader(img,0,{'PHOTSYS':['AB','mags (sloan catalogue)']})
            if verbose and len(colore)>0:
                from pylab import plot,show,ion,xlim,ylim,legend,setp,gca, draw, clf
                clf()
                ion()
                _label='%2s   %2s   %5.5s  %5.5s' % (filters[_filter],col,str(b),str(a))
                plot(xx,yy,'-',label='fit')
                plot(colore,zero,'o',label=_label)
                if len(colore)>1:
                    xlim(min(array(colore))-.2,max(array(colore))+.2)
                    ylim(min(array(zero))-1,max(array(zero)+1))
                legend(numpoints=1,markerscale=1.5)
                show()
    else: 
        print 'no calibration, '+_filter+' '+_field
        result=''
    delete('tmp.*,detection*')
    return result

#####################################################################
def pval(_xx, p):
    _y=+p[0]+p[1]*_xx
    return _y

def crossmatch(_ra0,_dec0,_ra1,_dec1,tollerance):  #   degree,degree,degree,degree,arcsec
    from numpy import pi, cos, sin, array, argmin, min,arccos, array
    scal=pi/180.
    distvec=[]
    pos0=[]
    pos1=[]
    i=0
    _ra0,_dec0,_ra1,_dec1=array(_ra0,float),array(_dec0,float),array(_ra1,float),array(_dec1,float)
    for jj in range(0,len(_ra0)):
        try:
            distance=arccos(array(sin(array(_dec1)*scal)*sin(_dec0[jj]*scal))+array(cos(array(_dec1)*scal)*cos(_dec0[jj]*scal)*cos((array(_ra1)-_ra0[jj])*scal)))
            if min(distance)<=tollerance*pi/(180*3600):
                distvec.append(min(distance))
                pos0.append(jj)
                pos1.append(argmin(distance))
        except: pass
    return  distvec,pos0,pos1  #  

###################################################################

def linreg(X, Y):
    from math import sqrt
    """
    Summary
        Linear regression of y = ax + b
    Usage
        real, real, real = linreg(list, list)
    Returns coefficients to the regression line "y=ax+b" from x[] and y[], and R^2 Value
    """
    if len(X) != len(Y):  raise ValueError, 'unequal length'
    N = len(X)
    Sx = Sy = Sxx = Syy = Sxy = 0.0
    for x, y in map(None, X, Y):
        Sx = Sx + x
        Sy = Sy + y
        Sxx = Sxx + x*x
        Syy = Syy + y*y
        Sxy = Sxy + x*y
    det = Sxx * N - Sx * Sx
    a, b = (Sxy * N - Sy * Sx)/det, (Sxx * Sy - Sx * Sxy)/det
    meanerror = residual = 0.0
    for x, y in map(None, X, Y):
        meanerror = meanerror + (y - Sy/N)**2
        residual = residual + (y - a * x - b)**2
    RR = 1 - residual/meanerror
    ss = residual / (N-2)
    Var_a, Var_b = ss * N / det, ss * Sxx / det
    return a, b, RR

#########################################################################################################################################
##########################################
def querysloan(ra1,dec1,radius,mr1,mr2):
    import lsc
    from lsc import sqlcl
    import os,sys,shutil,string
    righe = sqlcl.query('select P.objID, P.ra, P.dec , P.u, P.g, P.r, P.i, P.z, P.err_u, P.err_g, P.err_r, P.err_i, P.err_z, P.type '+\
                            'from PhotoPrimary as P , dbo.fGetNearbyObjEq('+\
                            str(ra1)+', '+str(dec1)+', '+str(radius)+' ) N'+' where P.objID = N.objID').readlines()
    _id,_ra,_dec,_u,_g,_r,_i,_z,_type=[],[],[],[],[],[],[],[],[]
    _du,_dg,_dr,_di,_dz=[],[],[],[],[]
    for i in righe[1:]:
        if len(string.split(i,','))==14:
            _id0,_ra0,_dec0,_u0,_g0,_r0,_i0,_z0,_du0,_dg0,_dr0,_di0,_dz0,_type0=string.split(i,',')
            if mr1 and mr2:
                if mr1<=float(_r0)<=mr2:
                    _id.append(_id0)
                    _ra.append(float(_ra0))
                    _dec.append(float(_dec0))
                    try:    _u.append(float(_u0))
                    except: _u.append(float(9999.))
                    try:    _g.append(float(_g0))
                    except: _g.append(float(9999.))
                    try:    _r.append(float(_r0))
                    except: _r.append(float(9999.))
                    try:    _i.append(float(_i0))
                    except: _i.append(float(9999.))
                    try:    _z.append(float(_z0))
                    except: _z.append(float(9999.))
                    try:    _du.append(float(_du0))
                    except: _du.append(float(9999.))
                    try:    _dg.append(float(_dg0))
                    except: _dg.append(float(9999.))
                    try:    _dr.append(float(_dr0))
                    except: _dr.append(float(9999.))
                    try:    _di.append(float(_di0))
                    except: _di.append(float(9999.))
                    try:    _dz.append(float(_dz0))
                    except: _dz.append(float(9999.))
                    _type.append(_type0[:-1])
            else:
                _id.append(_id0)
                _ra.append(float(_ra0))
                _dec.append(float(_dec0))
                try:    _u.append(float(_du0))
                except: _u.append(float(9999.))
                try:    _g.append(float(_dg0))
                except: _g.append(float(9999.))
                try:    _r.append(float(_dr0))
                except: _r.append(float(9999.))
                try:    _i.append(float(_di0))
                except: _i.append(float(9999.))
                try:    _z.append(float(_dz0))
                except: _z.append(float(9999.))
                try:    _du.append(float(_du0))
                except: _du.append(float(9999.))
                try:    _dg.append(float(_dg0))
                except: _dg.append(float(9999.))
                try:    _dr.append(float(_dr0))
                except: _dr.append(float(9999.))
                try:    _di.append(float(_di0))
                except: _di.append(float(9999.))
                try:    _dz.append(float(_dz0))
                except: _dz.append(float(9999.))
                _type.append(_type0[:-1])
    return _id,_ra,_dec,_u,_g,_r,_i,_z,_type,_du,_dg,_dr,_di,_dz

#################################################################
def sloan2file(ra1, dec1, radius, magsel0, magsel1,_output):     #  ra in degree  and dec in degree
    import os,re,string
    import lsc
    from numpy import array, compress
    ra2=float(ra1)#*15   #  degree
    _ids,_ras,_decs,_us,_gs,_rs,_is,_zs,_type,_dus,_dgs,_drs,_dis,_dzs=lsc.lscastrodef.querysloan(ra1,dec1,float(radius),magsel0,magsel1)
    headersloan='# BEGIN CATALOG HEADER \n\
# catdb sqlcl.query \n# catname dss1@cadc \n# nquery 4 \n#     ra '+str(ra2)+' hours \n\
#     dec '+str(dec1)+' degrees \n#     radius '+str(radius)+'  minutes \n#     qsystem J2000.0 INDEF \n# type btext \n\
# nheader 1 \n#     csystem J2000.0 \n# nfields 13 \n#       ra   1 0 d degrees %10.5f \n\
#     dec    2 0 d degrees %10.5f \n#     id   3 0 c NDEF %11s \n\
#     u       4 0 d degrees %6.3f \n#     uerr    5 0 d degrees %6.3f \n#     g       6 0 d degrees %6.3f \n\
#     gerr    7 0 d degrees %6.3f \n#     r       8 0 r INDEF %6.3f \n\
#     rerr    9 0 r INDEF %6.3f \n#     i      10 0 r INDEF %6.3f \n#     ierr   11 0 r INDEF %6.3f \n\
#     z      12 0 r INDEF %6.3f \n#     zerr   13 0 r INDEF %6.3f \n# END CATALOG HEADER\n#\n'
    ff = open(_output,'w')
    ff.write(headersloan)
    ff.close()
    if _ids:
         for i in range(0,len(_type)):
            try:                _type[i]=float(_type[i])
            except:                _type[i]=9999
         _ras=array(_ras)
         _decs=array(_decs)
         _type=array(_type)
         _ids=array(_ids)
         _rass=compress(_type==6,_ras)
         _decss=compress(_type==6,_decs)
         _idss=compress(_type==6,_ids)
         _gss=compress(_type==6,_gs)
         _rss=compress(_type==6,_rs)
         _iss=compress(_type==6,_is)
         _zss=compress(_type==6,_zs)
         _uss=compress(_type==6,_us)
         _dgss=compress(_type==6,_dgs)
         _drss=compress(_type==6,_drs)
         _diss=compress(_type==6,_dis)
         _dzss=compress(_type==6,_dzs)
         _duss=compress(_type==6,_dus)
         ff = open(_output,'a')
         for i in range(0,len(_idss)):
             ff.write('%12.12s\t%12.12s\t%s\t%8.8s\t%8.8s\t%8.8s\t%8.8s\t%8.8s\t%8.8s\t%8.8s\t%8.8s\t%8.8s\t%8.8s\n' %\
                          (str(_rass[i]),str(_decss[i]),str(_idss[i][-6:]),str(_uss[i]),str(_duss[i]),str(_gss[i]),str(_dgss[i]),str(_rss[i]),\
                               str(_drss[i]),str(_iss[i]),str(_diss[i]),str(_zss[i]),str(_dzss[i])))
         ff.close()
    else: _idss=''
    return _idss
#######################################################################

def transformsloanlandolt(stdcoo):
    from numpy import array, zeros
     ###  lupton 2005  ###### BVRI
     ### Jester et al. (2005) ### U
    if 'u' and 'g' and 'r' in stdcoo:
        stdcoo['B'] = array(stdcoo['g'], float) + 0.3130 * (array(stdcoo['g'], float) - array(stdcoo['r'], float)) + 0.2271
        stdcoo['Berr'] = (array(stdcoo['gerr'], float)**2 + 0.3130**2 * (array(stdcoo['gerr'], float)**2 + array(stdcoo['rerr'], float)**2))**0.5
        stdcoo['U'] = array(stdcoo['B'], float) + 0.78 * (array(stdcoo['u'], float) - array(stdcoo['g'], float)) - 0.88
        stdcoo['Berr'] = (array(stdcoo['Berr'], float)**2 + 0.78**2 * (array(stdcoo['uerr'], float)**2 + array(stdcoo['gerr'], float)**2))**0.5
    if 'g' and 'r' in stdcoo:
        if 'B' not in stdcoo:
            stdcoo['B'] = array(stdcoo['g'], float) + 0.3130 * (array(stdcoo['g'], float) - array(stdcoo['r'], float)) + 0.2271
            stdcoo['Berr'] = (array(stdcoo['gerr'], float)**2 + 0.3130**2 * (array(stdcoo['gerr'], float)**2 + array(stdcoo['rerr'], float)**2))**0.5
        if 'V' not in stdcoo:
            stdcoo['V'] = array(stdcoo['g'], float) - 0.5784 * (array(stdcoo['g'], float) - array(stdcoo['r'], float)) - 0.0038
            stdcoo['Verr'] = (array(stdcoo['gerr'], float)**2 + 0.5784**2 * (array(stdcoo['gerr'], float)**2 + array(stdcoo['rerr'], float)**2))**0.5
    if 'r' and 'i' in stdcoo:
        if 'R' not in stdcoo:
            stdcoo['R'] = array(stdcoo['r'], float) - 0.2936 * (array(stdcoo['r'], float) - array(stdcoo['i'], float)) - 0.1439
            stdcoo['Rerr'] = (array(stdcoo['rerr'], float)**2 + 0.2936**2 * (array(stdcoo['rerr'], float)**2 + array(stdcoo['ierr'], float)**2))**0.5
        if 'I' not in stdcoo:
            stdcoo['I'] = array(stdcoo['r'], float) - 1.2444 * (array(stdcoo['r'], float) - array(stdcoo['i'], float)) - 0.3820
            stdcoo['Ierr'] = (array(stdcoo['rerr'], float)**2 + 1.2444**2 * (array(stdcoo['rerr'], float)**2 + array(stdcoo['ierr'], float)**2))**0.5
    if 'g' and 'r' in stdcoo:
        if 'R' not in stdcoo:
            stdcoo['R'] = array(stdcoo['r'], float) - 0.1837 * (array(stdcoo['g'], float) - array(stdcoo['r'], float)) - 0.0971
            stdcoo['Rerr'] = (array(stdcoo['rerr'], float)**2 + 0.1837**2 * (array(stdcoo['gerr'], float)**2 + array(stdcoo['rerr'], float)**2))**0.5
    if 'i' and 'z' in stdcoo:
        if 'I' not in stdcoo:
            stdcoo['I'] = array(stdcoo['i'], float) - 0.3780 * (array(stdcoo['i'], float) - array(stdcoo['z'], float)) - 0.3974
            stdcoo['Ierr'] = (array(stdcoo['ierr'], float)**2 + 0.1837**2 * (array(stdcoo['ierr'], float)**2 + array(stdcoo['zerr'], float)**2))**0.5
    for fil in 'UBVRI':
        if fil not in stdcoo: stdcoo[fil] = zeros(len(stdcoo['r']))
    return stdcoo

#####################################################

def transformlandoltsloan(stdcoo):
    #  jordi et al 2006
    from numpy import array
    if 'B' and 'V' in stdcoo:
        if 'g' not in stdcoo:  
            stdcoo['g']=array(stdcoo['V'],float)+0.630*(array(stdcoo['B'],float)-array(stdcoo['V'],float))-0.124
    if 'V' and 'R' in stdcoo:
        if 'r' not in stdcoo:  
            VR=(array(stdcoo['V'],float)-array(stdcoo['R'],float))
            a=array(stdcoo['R'],float)+0.267*VR+0.088 # V-R < 0.93
            b=array(stdcoo['R'],float)+0.77*VR-0.37  #  V-R > 0.93
            stdcoo['r']=[ (a[i], b[i]) [ VR[i] <= 0.93 ] for i in range(0, len(VR)) ]
    if 'R' and 'I' in stdcoo:
        if 'i' not in stdcoo:  
            stdcoo['i']=array(stdcoo['I'],float)-0.247*(array(stdcoo['R'],float)-array(stdcoo['I'],float))+0.329
    if 'V' and 'R' and 'I' in stdcoo:
        if 'r' not in stdcoo:  
            VR=(array(stdcoo['V'],float)-array(stdcoo['R'],float))
            a=array(stdcoo['R'],float)+0.267*VR+0.088 # V-R < 0.93
            b=array(stdcoo['R'],float)+0.77*VR-0.37  #  V-R > 0.93
            stdcoo['r']=[ (a[i], b[i]) [ VR[i] <= 0.93 ] for i in range(0, len(VR)) ]
        if 'z' not in stdcoo:  
            stdcoo['z']= array(stdcoo['r'],float) - 1.584*(array(stdcoo['R'],float)-array(stdcoo['I'],float)) +  (0.386)
    for fil in 'ugriz':
        if fil not in stdcoo: stdcoo[fil]=array(stdcoo['V'],float)-array(stdcoo['V'],float)
    return stdcoo

####################################################

def sextractor(img):
        import lsc
        from lsc.util import defsex,delete
        import os
        from pyraf import iraf
        from iraf import proto
        from numpy import compress,array,asarray
        from astropy.io import fits
        
        hd = fits.getheader(img)
        if hd.get('SATURATE'):    _saturation=hd.get('SATURATE')
        else:                     _saturation=45000
        if _saturation>55000: _saturation=55000

        if hd.get('NAXIS1'):  _xdim=int(hd.get('NAXIS1'))
        else: _xdim=4010
        if hd.get('NAXIS2'):  _ydim=int(hd.get('NAXIS2'))
        else: _ydim=4010

        namesex=defsex('default.sex')
        os.system("sex '"+img+"[0]' -c "+namesex+" -CLEAN YES -SATUR_LEVEL "+str(_saturation)+' > _logsex')
        print 'sex '+img+'[0] -c '+namesex+' -CLEAN YES -SATUR_LEVEL '+str(_saturation)+' > _logsex'
        delete(namesex)
        delete('_logsex')
        xpix=iraf.proto.fields('detections.cat',fields='2',Stdout=1)
        ypix=iraf.proto.fields('detections.cat',fields='3',Stdout=1)
        cm=iraf.proto.fields('detections.cat',fields='4',Stdout=1)
        cl=iraf.proto.fields('detections.cat',fields='7',Stdout=1)
        fw=iraf.proto.fields('detections.cat',fields='8',Stdout=1)
        ell=iraf.proto.fields('detections.cat',fields='9',Stdout=1)
        bkg=iraf.proto.fields('detections.cat',fields='10',Stdout=1)
        fl=iraf.proto.fields('detections.cat',fields='6',Stdout=1)

        fl=compress((array(xpix)!=''),array(fl,float))
        cl=compress((array(xpix)!=''),array(cl,float))
        cm=compress((array(xpix)!=''),array(cm,float))
        fw=compress((array(xpix)!=''),array(fw,float))
        ell=compress((array(xpix)!=''),array(ell,float))
        bkg=compress((array(xpix)!=''),array(bkg,float))
        ypix=compress((array(xpix)!=''),array(ypix,float))
        xpix=compress((array(xpix)!=''),array(xpix,float))

        try:
            print len(fl),_xdim,_ydim
            ww=asarray([i for i in range(len(xpix)) if ((xpix[i]<_xdim) or (ypix[i]<_ydim))], dtype=int)
            cl,cm,fw,ell,xpix,ypix,bkg,fl=cl[ww],cm[ww],fw[ww],ell[ww],xpix[ww],ypix[ww],bkg[ww],fl[ww]

            ww=asarray([i for i in range(len(xpix)) if ((xpix[i]>20) or (ypix[i]<_ydim))], dtype=int)
            cl,cm,fw,ell,xpix,ypix,bkg,fl=cl[ww],cm[ww],fw[ww],ell[ww],xpix[ww],ypix[ww],bkg[ww],fl[ww]

            ww=asarray([i for i in range(len(xpix)) if (xpix[i]>3)], dtype=int)
            cl,cm,fw,ell,xpix,ypix,bkg,fl=cl[ww],cm[ww],fw[ww],ell[ww],xpix[ww],ypix[ww],bkg[ww],fl[ww]

            ww=asarray([i for i in range(len(fl)) if (fl[i]<=3)], dtype=int)
            cl,cm,fw,ell,xpix,ypix,bkg,fl=cl[ww],cm[ww],fw[ww],ell[ww],xpix[ww],ypix[ww],bkg[ww],fl[ww]

            fl=compress((array(fw)<=15)&(array(fw)>=-2),array(fl))
            cl=compress((array(fw)<=15)&(array(fw)>=-2),array(cl))
            cm=compress((array(fw)<=15)&(array(fw)>=-2),array(cm))
            xpix=compress((array(fw)<=15)&(array(fw)>=-2),array(xpix))
            ypix=compress((array(fw)<=15)&(array(fw)>=-2),array(ypix))
            ell=compress((array(fw)<=15)&(array(fw)>=-2),array(ell))
            bkg=compress((array(fw)<=15)&(array(fw)>=-2),array(bkg))
            fw=compress((array(fw)<=15)&(array(fw)>=-2),array(fw))
        except: 
            xpix,ypix,fw,cl,cm,ell=[],[],[],[],[],[]
            print '\n### ERROR Filtering the sextractor detections, please check that sextractor is working ......'
        delete('detections.cat')
        return xpix,ypix,fw,cl,cm,ell,bkg,fl

#############################################################################################################

def readapass(_ra,_dec,radius=30,field=''):
    import os,string,re
    import lsc
    line='/science/ASSM/findassm -c '+str(_ra)+' '+str(_dec)+' -bm '+str(radius)+' '+str(radius)+' -Vb 25.0 -Vf -5.0 -Rr 3.0 -Rb -3.0 -l ApassCat -F BVPgPrPieBeVegereid'
    xxx=os.popen(line).read()
    yyy=string.split(xxx,'\n')[3:-1]
    vector={}
    column={}
    yyy[0]=re.sub('J2000','',yyy[0])
    print  yyy[0]
    for i in range(0,len(string.split(yyy[0]))):
        if string.split(yyy[0])[i] in ['#RAdeg', 'DECdeg', 'B', 'V', 'Pg', 'Pr', 'Pi', 'eB', 'eV', 'eg', 'er', 'ei']:
            column[i]=string.split(yyy[0])[i]
    print column
    zzz=[]
    for j in yyy:
        if j[0]!='#':
            zzz.append(string.split(j))
    column2={}
    for i in column:
        column2[column[i]]=zip(*zzz)[i]
    filters=['B', 'V', 'Pg', 'Pr', 'Pi']

    filename='cataogue_APASS.cat'

    nfield=3+len(filters)*2
    ff = open(filename,'w')
    header='# BEGIN CATALOG HEADER\n# nfields '+str(nfield)+'\n#     ra     1  0 d degrees %10.5f\n#     dec    2  0 d degrees %10.5f\n'
    header=header+'#     id     3  0 c INDEF %15s\n'
    nn=4
    for f in filters:
        header=header+'#     '+str(re.sub('P','',f))+'      '+str(nn)+' 0 r INDEF %6.2f\n'
        nn=nn+1
        header=header+'#     '+str(re.sub('P','',f))+'err   '+str(nn)+' 0 r INDEF %6.2f\n'
        nn=nn+1
    header=header+'# END CATALOG HEADER\n#\n'
    ff.write(header)
    m=1
    print column2.keys()
    for i in range(0,len(column2[column2.keys()[0]])):
        ff.write('%14s %14s  %3s  ' % (str(column2['#RAdeg'][i]),str(column2['DECdeg'][i]),str(m)))
        m=m+1
        for f in filters:
            if float(column2[f][i])>0:
                ff.write(' %6.3f %6.3f  ' % (float(column2[f][i]),float(column2['e'+re.sub('P','',f)][i])))
            else:
                ff.write(' %6.3f %6.3f  ' % (float(9999),float(0.0)))
        ff.write('\n')
    ff.close()
    return column2

####################################################################

def crossmatchxy(_xx0,_yy0,_xx1,_yy1,tollerance):  #   pixel,pixel,pixel,pixel,pixel
     import numpy as np
     distvec=[]
     pos0=[]
     pos1=[]
     for jj in range(0,len(_xx0)):
          distance = np.sqrt((_xx0[jj]-_xx1)**2+(_yy0[jj]-_yy1)**2)
          if min(distance)<=tollerance:
               distvec.append(np.min(distance))
               pos0.append(jj)
               pos1.append(np.argmin(distance))
     return  distvec,pos0,pos1  #  

####################################################################################

def finewcs(img):
    import lsc
    import numpy as np
    from pyraf import iraf
    import os,string
    catvec=lsc.lscastrodef.querycatalogue('2mass',img,'vizir')
    namesex=lsc.util.defsex('default.sex')
    os.system("sex '"+img+"[0]' -c "+namesex+" -CATALOG_NAME _temp_catalog  > _logsex")
    aaa=np.genfromtxt('_temp_catalog',float)
    bbb=zip(*aaa)
    vector2=[str(k)+' '+str(v) for k,v in  zip(bbb[1],bbb[2])]
    colonne3=' 1   2 '
    distvec,pos0,pos1=lsc.lscastrodef.crossmatchxy(np.array(catvec['x']),np.array(catvec['y']),np.array(bbb[1]),np.array(bbb[2]),5)  
    if len(pos0)>20:    _order=4
    elif len(pos0)>10:  _order=3
    else:               _order=2

    print _order
    print len(pos0)

    xxx=np.array(bbb[1])[pos1]
    yyy=np.array(bbb[2])[pos1]
    raa=np.array(catvec['ra'])[pos0]
    decc=np.array(catvec['dec'])[pos0]
    vector4=[str(k)+' '+str(v)+' '+str(j)+' '+str(l) for k,v,j,l in  zip(raa,decc,xxx,yyy)]
    fitgeo=['general','xyscale','rxyscale']
    rmsx0=99
    rmsy0=99
    bestvalue=''
    if len(pos0)>5:
        for ff in fitgeo:
            _ccmap1=iraf.ccmap('STDIN','STDOUT',images=img,Stdin=vector4,fitgeome=ff,xcolum=3, xxorder=_order,\
                               xyorder=_order, yxorder=_order, yyorder=_order, ycolum=4,lngcolum=1,latcolumn=2,\
                               lngunit='degrees',update='No',interact='No',maxiter=3,Stdout=1,verbose='yes')
            if 'rms' in _ccmap1[_ccmap1.index('Wcs mapping status')+1]:
                try:           rmsx,rmsy=np.array(string.split(string.split(_ccmap1[_ccmap1.index('Wcs mapping status')+1],':')[-1])[0:2],float)
                except:        rmsx,rmsy=np.array(string.split(string.split(_ccmap1[_ccmap1.index('Wcs mapping status')+1],':')[-1])[0:2])
            print rmsx,rmsy,ff
            if rmsx<2 and rmsy<2:
                if rmsx+rmsy<=rmsx0+rmsy0:
                    rmsx0,rmsy0=rmsx,rmsy
                    bestvalue=ff
        print rmsx,rmsy,bestvalue
        if rmsx0<2 and rmsy0<2:
            print 'update wcs with distortion correction'  
            _ccmap1=iraf.ccmap('STDIN','STDOUT',images=img,Stdin=vector4,fitgeome=bestvalue,xcolum=3, xxorder=_order,\
                               xyorder=_order, yxorder=_order, yyorder=_order, ycolum=4,lngcolum=1,latcolumn=2,\
                               lngunit='degrees',update='Yes',interact='No',maxiter=3,Stdout=1,verbose='yes')
    return rmsx0,rmsy0,bestvalue
#    vector=[str(k)+' '+str(v) for k,v in  zip(catvec['x'],catvec['y'])]
#    iraf.display(img,1,fill='yes')
#    iraf.tvmark(1,'STDIN',Stdin=list(vector),mark="circle",number='yes',label='no',radii=20,nxoffse=5,nyoffse=5,color=205,txsize=4)
#    iraf.tvmark(1,'STDIN',Stdin=list(vector2),mark="cross",number='yes',label='no',radii=20,nxoffse=5,nyoffse=5,color=204,txsize=4)
    #vector3=[str(k)+' '+str(v) for k,v in  zip(xxx,yyy)]
    #iraf.tvmark(1,'STDIN',Stdin=list(vector3),mark="circle",number='yes',label='no',radii=10,nxoffse=5,nyoffse=5,color=206,txsize=4)
#        catvec=lsc.lscastrodef.querycatalogue('2mass',img,'vizir')
#        vector=[str(k)+' '+str(v) for k,v in  zip(catvec['x'],catvec['y'])]
#        iraf.tvmark(1,'STDIN',Stdin=list(vector),mark="circle",number='yes',label='no',radii=10,nxoffse=5,nyoffse=5,color=206,txsize=4)
#####################################################################################################3

def run_astrometry(im, clobber=True,redo=False):
    import lsc
    import os
    import shutil
    import numpy as np
    import string
    print 'astrometry for image ' + str(im)
    # Run astrometry.net
    hdr = lsc.readhdr(im)
    _wcserr = lsc.readkey3(hdr, 'wcserr')
    done = 0
    if float(_wcserr) == 0: 
        done = 1
    print redo
    if redo: 
        done = 0
    if done:
        print 'already done'
    else:
        ra = lsc.readkey3(hdr,'RA')
        dec = lsc.readkey3(hdr,'DEC')
        #    ra = fits.getval(im, 'RA')
        #    dec = fits.getval(im, 'DEC')
        cmd = 'solve-field --crpix-center --no-verify --no-fits2fits --no-tweak -l 30 '
        cmd += '--backend-config {} '.format(os.path.join(lsc.util.workdirectory, 'usr/backend.cfg'))
        cmd += '--radius 1.0 --ra {} --dec {} --guess-scale '.format(ra, dec)
        cmd += '--scale-units arcsecperpix --scale-low 0.1 --scale-high .7 '
        cmd += '--no-plots -N tmpwcs.fits '
        if clobber: cmd += '--overwrite '
        cmd += '--solved none --match none --rdls none --wcs none --corr none '
        cmd += ' --downsample 4 --fits-image '
        cmd += '%s' % im
        print cmd
        os.system(cmd)
        basename = im[:-5]
        if os.path.exists(basename + '.axy'):
            os.remove(basename + '.axy')
        else:
            print 'axy files do not exist'
        if os.path.exists(basename + '-indx.xyls'):
            os.remove(basename + '-indx.xyls')
        if os.path.exists('tmpwcs.fits'):
            hdrt = lsc.readhdr('tmpwcs.fits')
            _instrume = lsc.readkey3(hdrt,'instrume')
            sexvec = lsc.lscastrodef.sextractor('tmpwcs.fits')
            xpix,ypix,fw,cl,cm,ell,bkg,fl = sexvec
            if len(fw)>1:
                if 'kb' in _instrume:
                    fwhm = np.median(np.array(fw))*.68*2.35*0.467
                elif 'fl' in _instrume:
                    fwhm = np.median(np.array(fw))*.68*2.35*0.467          #  need to check
                elif 'fs' in _instrume:
                    fwhm = np.median(np.array(fw))*.68*2.35*0.30
                elif 'em' in _instrume:
                    fwhm = np.median(np.array(fw))*.68*2.35*0.278
                else:
                    fwhm = 5
            else:
                fwhm = 5
            astrostring = '1  1  1'
            dictionary = {'ASTROMET': [astrostring, 'rmsx rmsy nstars'],
                    'PSF_FWHM': [fwhm, 'FHWM (arcsec) - computed with sectractor'],
                    'CTYPE1'  : [ 'RA---TAN', 'TAN (gnomic) projection'],
                    'CTYPE2'  : ['DEC--TAN' , 'TAN (gnomic) projection'],
                    'WCSAXES' : [ hdrt['WCSAXES'] , 'no comment'],
                    'EQUINOX' : [ hdrt['EQUINOX'] , 'Equatorial coordinates definition (yr)'],
                    'LONPOLE' : [ hdrt['LONPOLE'] , 'no comment'],
                    'LATPOLE' : [ hdrt['LATPOLE'] , 'no comment'],
                    'CRVAL1'  : [ hdrt['CRVAL1']  , 'RA  of reference point'],
                    'CRVAL2'  : [ hdrt['CRVAL2'] , 'DEC of reference point'],
                    'CRPIX1'  : [ hdrt['CRPIX1']     , 'X reference pixel'],
                    'CRPIX2'  : [ hdrt['CRPIX2']     , 'Y reference pixel'],
                    'CUNIT1'  : ['deg     ' , 'X pixel scale units'],
                    'CUNIT2'  : ['deg     ' , 'Y pixel scale units'],
                    'CD1_1'   : [ hdrt['CD1_1'] , 'Transformation matrix'],
                    'CD1_2'   : [ hdrt['CD1_2'] , 'no comment'],
                    'CD2_1'   : [ hdrt['CD2_1'] , 'no comment'],
                    'CD2_2'   : [ hdrt['CD2_2'] , 'no comment'],
                    'IMAGEW'  : [ hdrt['IMAGEW']  , 'Image width,  in pixels.'],
                    'IMAGEH'  : [ hdrt['IMAGEH']  , 'Image height, in pixels.']}
            if 'WCS_ERR' in hdr and 'WCSERR' not in hdr:
                dictionary['WCS_ERR'] = [0, '']
            else:
                dictionary['WCSERR'] = [0, '']
            lsc.util.updateheader(im, 0, dictionary)
            lsc.mysqldef.updatevalue('photlco', 'WCS', 0, string.split(im, '/')[-1])
#        shutil.move('tmpwcs.fits', outputname)
#        lsc.util.updateheader(outputname, 0, {'ASTROMET': [astrostring, 'rmsx rmsy nstars'],
#                                              'PSF_FWHM': [fwhmgess, 'FHWM (arcsec) - computed with sectractor']})
        else:
            print 'tmpwcs.fits files do not exist'
###################################################################
