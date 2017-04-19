import numpy as np
from astropy.io import fits

##########################        DEFINE FITSN  #########################################
def fitsn(img,imgpsf,coordlist,_recenter,fwhm0,original,sn,residual,_show,_interactive,dmax,dmin,z11='',z22='',midpt='',size=7,apco0=0):
    import lsc
    lsc.util.delete("apori")
    lsc.util.delete(img+".sn.mag")
#################################
    from pyraf import iraf
    import string
    iraf.imcoords(_doprint=0)
    iraf.digiphot(_doprint=0)
    iraf.daophot(_doprint=0)
    from iraf import digiphot
    from iraf import daophot
    from iraf import ptools
    a1 = int(fwhm0)
    a2 = int(2.*fwhm0+.5)
    a3 = int(3.*fwhm0+.5)
    a4 = int(4.*fwhm0+.5)
    ap = str(a1)+","+str(a2)+","+str(a3)
########################################
    if _recenter:        answ='yes'
    else:                answ='no'
#########################################
    hdr=lsc.util.readhdr(img+'.fits')
    _gain=lsc.util.readkey3(hdr,'gain')
    _ron=lsc.util.readkey3(hdr,'ron')
    _exptime=lsc.util.readkey3(hdr,'exptime')
    iraf.noao.digiphot.daophot.photpars.zmag = 0
    iraf.noao.digiphot.daophot.datapars.readnoi = _gain
    iraf.noao.digiphot.daophot.datapars.epadu = _ron
    iraf.noao.digiphot.daophot.datapars.datamin = dmin
    iraf.noao.digiphot.daophot.datapars.datamax = dmax
    iraf.noao.daophot.fitskypars.annulus=a3
    iraf.noao.daophot.photpars.apertures = ap
    iraf.noao.digiphot.daophot.datapars.exposure = 'exptime'
    iraf.noao.digiphot.daophot.datapars.airmass = 'airmass'
    iraf.noao.digiphot.daophot.datapars.filter = 'filter2'
    iraf.noao.digiphot.daophot.daopars.psfrad = a4
    #  modify fitrad to 3 fwhm to see if works better     
    iraf.noao.digiphot.daophot.daopars.fitrad = fwhm0 #* 3
    iraf.noao.digiphot.daophot.daopars.sannulus = int(a4)
    iraf.noao.digiphot.daophot.daopars.recenter = answ
    iraf.noao.digiphot.daophot.daopars.fitsky = 'yes'
#    iraf.noao.digiphot.daophot.centerpars.cbox = 0
    iraf.noao.digiphot.daophot.centerpars.cbox = 4
    iraf.noao.digiphot.daophot.centerpars.calgori = 'gauss'

    #  fitskypars.salgorithm = "constant"
    #  fitskypars.skyvalue = 0
    print '\n### recentering: '+str(answ)
    if _show:
        iraf.noao.digiphot.daophot.phot(original,coordlist,"apori",veri='no')   
        iraf.noao.digiphot.daophot.phot(sn,coordlist,img+".sn.mag",veri='no')   
    else:
        iraf.noao.digiphot.daophot.phot(original,coordlist,"apori",veri='no',verb='no')   
        iraf.noao.digiphot.daophot.phot(sn,coordlist,img+".sn.mag",veri='no',verb='no')   

    lsc.util.delete(img+".sn.als")
    print sn,imgpsf,img
    iraf.allstar(sn,img+".sn.mag",imgpsf,img+".sn.als","",residual,veri='no',verb='no')
    lsc.util.delete("snfit.fits")
    iraf.imarith(sn+'.fits',"-",residual+'.fits',"snfit.fits")
    lsc.util.delete("skyfit.fits")
    iraf.imarith(original+'.fits',"-","snfit.fits","skyfit.fits")
    iraf.txsort(img+".sn.als","ID")
    tmptbl = iraf.txdump(img+".sn.als","mag,merr,xcenter,ycenter",expr='yes', Stdout=1)
    magerr,fitmag,centx,centy=[],[],[],[]
    for i in tmptbl:
        try:
            fitmag.append(float(string.split(i)[0]))#-2.5*log10(_exptime))
        except:
            fitmag.append(string.split(i)[0])
        try:
            magerr.append(float(string.split(i)[1]))
        except:
            magerr.append(string.split(i)[1])
        centx.append(float(string.split(i)[2]))
        centy.append(float(string.split(i)[3]))
    tmptbl=iraf.txdump("apori","mag",expr='yes', Stdout=1)
    apori1,apori2,apori3=[],[],[]
    for i in tmptbl:
        try:
            apori1.append(float(string.split(i)[0]))#-2.5*log10(_exptime))
        except:
            apori1.append(string.split(i)[0])
        try:            
            apori2.append(float(string.split(i)[1]))#-2.5*log10(_exptime))
        except:
            apori2.append(string.split(i)[1])
        try:
            apori3.append(float(string.split(i)[2]))#-2.5*log10(_exptime))
        except:
            apori3.append(string.split(i)[2])
            
    iraf.txsort(img+".sn.mag","YCENTER")
    tmptbl=iraf.txdump(img+".sn.mag","mag,magerr",expr='yes', Stdout=1) 

    if _show:
        print "********************************************************************"
        print "ID <apmag on original>  <apmag on bgsubt> fitmag truemag err_fit"         
        print "     ",a1,"       ",a2,"      ",a3,"        ",a1,"     ",a2,"     ",a3 


    apmag1,apmag2,apmag3,truemag=[],[],[],[]
    for i in range(len(tmptbl)):
        try:
            apmag1.append(float(string.split(tmptbl[i])[0]))#-2.5*log10(_exptime))
        except:
            apmag1.append(9999)
        try:
            apmag2.append(float(string.split(tmptbl[i])[1]))#-2.5*log10(_exptime))
        except:
            apmag2.append(9999)
        try:
            apmag3.append(float(string.split(tmptbl[i])[2]))#-2.5*log10(_exptime))
        except:
            apmag3.append(9999)
        try:
            truemag.append(fitmag[i]+float(apco0))
        except:
            truemag.append('INDEF')
        if _show:
            print i,apori1[i],apori2[i],apori3[i],apmag1[i],apmag2[i],apmag3[i],fitmag[i],truemag[i],magerr[i]
    if _show:
        print "********************************************************************"

    if _show:
        print midpt,z11,z22
        _tmp1,_tmp2,goon=lsc.util.display_image(original+'.fits',1, z11, z22, False, _xcen=.25, _ycen=.25, _xsize=.3, _ysize=.3)
        z01 = float(z11)-float(midpt)
        z02 = float(z22)-float(midpt) 
        s1 = 1
        s2 = -int(fwhm0)
        lsc.util.delete("tmptbl")
        ff=open('tmptbl','w')
        ff.write(str(s1)+' '+str(s2)+" ORIGINAL")
        ff.close()    
        iraf.tvmark(1,"tmptbl",autol='no',mark="none",inter='no',label='yes',txsize=2)
        _tmp1,_tmp2,goon=lsc.util.display_image('snfit.fits',1, z01, z02, False, _xcen=.25, _ycen=.75, _xsize=.3, _ysize=.3, _erase='no')
        lsc.util.delete("tmptbl")
        tmptbl0=iraf.txdump(img+".sn.als","xcen,ycen",expr='yes',Stdout=1)
        ff=open('tmptbl','w')
        for i in tmptbl0:
            ff.write(i+'\n')
        ff.close()    
        lra = int((2*float(size)*float(fwhm0))*2)
        iraf.tvmark(1,"tmptbl",autol='no',mark="circle", number='yes',nyoffset=lra,radi=a2,txsize=2,inter='no')
        s1 = 1
        s2 = -1*int(fwhm0)
        lsc.util.delete("tmptbl")
        ff=open('tmptbl','w')
        ff.write(str(s1)+' '+str(s2)+" FITTED")
        ff.close()    
        iraf.tvmark(1,"tmptbl",autol='no',mark="none",inter='no',label='yes',txsize=2)
        _tmp1,_tmp2,goon=lsc.util.display_image('skyfit.fits',1, z11, z22, False, _xcen=.75, _ycen=.25, _xsize=.3, _ysize=.3, _erase='no')
        s1 = 1
        s2 = -1*int(fwhm0)
        lsc.util.delete("tmptbl")
        ff=open('tmptbl','w')
        ff.write(str(s1)+' '+str(s2)+" RESIDUAL")
        ff.close()    
        iraf.tvmark(1,"tmptbl",autol='no',mark="none",inter='no',label='yes',txsize=2)
    return apori1,apori2,apori3,apmag1,apmag2,apmag3,fitmag,truemag,magerr,centx,centy

###########################  DEFINE MANUAL CHANGING  #########################################

def manusn(img,imgpsf,dmag0,apori1,apori2,apori3,apmag1,apmag2,apmag3,fitmag,truemag,magerr,centx,centy,z11,z22,midpt,size,fwhm0,x1,y1,arterr):
   from pyraf import iraf
   import lsc
   import string,re,sys,os
   from numpy import zeros
   a2 = int(2.*fwhm0+.5)
   fdmag = 10**(-0.4*float(dmag0))
   lsc.util.delete(",_snfit.fit?,skyfit.fit?,_snfit.ar?")
   if truemag[0]=='INDEF':
       print 'ACTUNG'
       magerr[0]=0.0
       lsc.util.delete('test.fits')
       os.system('echo '+str(iraf.field(img+'.sn.coo', field='1,2', Stdout=1)[0])+' '+dmag0+' > dddd')
       iraf.addstar("snfit","dddd",imgpsf,"_snfit",nstar=1,veri='no',simple='yes',verb='yes')
       lsc.util.delete('dddd')
   else:
       iraf.imarith("snfit.fits","*",fdmag,"_snfit.fits")   
   iraf.imarith("original.fits","-","_snfit.fits","skyfit.fits")
   _tmp1,_tmp2,goon=lsc.util.display_image('original.fits',1, z11, z22, False, _xcen=.25, _ycen=.25, _xsize=.3, _ysize=.3)
   print z11,z22,midpt
   z01 = float(z11)-float(midpt)
   z02 = float(z22)-float(midpt) 
   s1 = 1
   s2 = -int(fwhm0)
   lsc.util.delete("tmptbl")
   ff=open('tmptbl','w')
   ff.write(str(s1)+' '+str(s2)+" ORIGINAL") 
   ff.close()
   iraf.tvmark(1,"tmptbl",autol='yes',mark="none",inter='no',label='yes',txsize=2)
   _tmp1,_tmp2,goon=lsc.util.display_image('_snfit.fits',1, z01, z02, False, _xcen=.25, _ycen=.75, _xsize=.3, _ysize=.3, _erase='no')
   lsc.util.delete("tmptbl")
   tmptbl=iraf.txdump(img+".sn.als","xcen,ycen",expr='yes', Stdout=1)
   ff=open('tmptbl','w')
   for i in tmptbl:
       ff.write(i) 
   ff.close()  
   lra = int((2*size*fwhm0)*2)
   iraf.tvmark(1,"tmptbl",autol='no',mark="circle", number='yes',nyoffset=lra,radi=a2,txsize=2,inter='no')
   s1 = 1
   s2 = -int(fwhm0)
   lsc.util.delete("tmptbl")
   ff=open('tmptbl','w')
   ff.write(str(s1)+' '+str(s2)+" FITTED") 
   ff.close()  
   iraf.tvmark(1,"tmptbl",autol='no',mark="none",inter='no',label='yes',txsize=2)
   _tmp1,_tmp2,goon=lsc.util.display_image('skyfit.fits',1, z11, z22, False, _xcen=.75, _ycen=.25, _xsize=.3, _ysize=.3, _erase='no')
   s1 = 1
   s2 = -int(fwhm0)
   lsc.util.delete("tmptbl")
   ff=open('tmptbl','w')
   ff.write(str(s1)+' '+str(s2)+" RESIDUAL") 
   ff.close()
   iraf.tvmark(1,"tmptbl",autol='no',mark="none",inter='no',label='yes',txsize=2)

   newmag=list(zeros(len(truemag)))
   for i in range(0,len(truemag)):
       try:
           newmag[i]=float(truemag[i])+float(dmag0)
       except:
           newmag[i]=float(dmag0)
           magerr[i]=0.0
   print truemag
   print newmag

   print "***************************************************************************" 
   print "#id  x_ori   y_ori     x     y    ap_ori ap_bgsub  fit_mag  err_art  err_fit" 
   for i in range(len(fitmag)):
       print "SN",i,str(centx[i]+x1),str(centy[i]+y1),str(centx[i]),str(centy[i]),"  ",str(apori3[i]),"  ",str(apmag3[i]),"  ",str(newmag[i]),"  ",str(arterr),"  ",str(magerr[i])
   print "**************************************************************************"

   return apori1,apori2,apori3,apmag1,apmag2,apmag3,fitmag,truemag,magerr,centx,centy,newmag

###################   DEFINE ERROR     ######################################
def errore(img,imgpsf,coordlist,size,truemag,fwhm0,leng0,_show,_interactive,_numiter,z11,z22,midpt,nax,nay,xbgord0,ybgord0,_recenter,apco0,dmax,dmin):
    import lsc
    import os,sys,re,string
    from numpy import array,mean,std,compress,average
    from pyraf import iraf
    if not _numiter: _numiter=3
    dartf=100
    while dartf>=size-1:
        if _interactive:
            artfac0 =raw_input('>>> Dispersion of artificial star positions (in units of FWHM) [1] ')
            if not artfac0: artfac0=1
        else:
            artfac0=1
        try:  
            artfac0=float(artfac0)
            if float(artfac0)>=size-1:
                print '!!! WARNING: '+str(artfac0)+' too large (max '+str(size)+'- 1)'
                print 'try again....'
            else:
                dartf = artfac0
        except:
            print '#### WARNING: '+str(artfac0)+' should be a number !!!!'
            print 'try again....'
    lsc.util.delete("tmpar?")

    lsc.util.delete('artskyfit.fits')
    os.system('cp skyfit.fits artskyfit.fits')
    i=0
    tmpart=[]
    while i<=8:
        lsc.util.delete("reserr.fit?,artbg.fit?,artstar.fit?,artres.fit?,artfit.fit?")
        artrad = fwhm0/2.
        #artseed = artseed+1234
        artx =  int(i/3.)-1
        if i<=2: arty = artx+i
        if 3<=i<=5: arty = artx-1+i-3
        if i>=6: arty = artx-2+i-6

        ff=open(img+".sn.coo",'r')
        ss=ff.readline()
        ff.close()
        xbb=float(string.split(ss)[0])
        ybb=float(string.split(ss)[1])

        xbb=xbb+artx*fwhm0*artfac0
        ybb=ybb+arty*fwhm0*artfac0

        lsc.util.delete(coordlist)
        ff=open(coordlist,'w')
        ff.write(str(xbb)+'  '+str(ybb)+'  '+str(truemag[0])+"  1")
        ff.close()
                        
        xb1 = int(float(xbb)-fwhm0*float(leng0)/2)
        xb2 = int(float(xbb)+fwhm0*float(leng0)/2) 
        yb1 = int(float(ybb)-fwhm0*float(leng0)/2)
        yb2 = int(float(ybb)+fwhm0*float(leng0)/2)
        sec="1 "+str(xb1)+" 1 "+str(nay)+'\n'
        sec=sec+str(xb2)+' '+str(nax)+" 1 "+str(nay)+'\n'
        sesc=sec+str(xb1)+' '+str(xb2)+" 1 "+str(yb1)+'\n'
        sec=sec+str(xb1)+' '+str(xb2)+' '+str(yb2)+' '+str(nay)+'\n'
        ff = open('sec','w')
        ff.write(sec)
        ff.close()

        lsc.util.delete("reserr.ar?")
        lsc.util.delete("artlist.ma?")
        lsc.util.delete("artsky.fit?")
        lsc.util.delete("artbg.fit?")
        lsc.util.delete("artbgs.fit?")
        lsc.util.delete("artsn.fit?")
        lsc.util.delete("artres.fit?")
        lsc.util.delete("artlist.al?")

        iraf.addstar("artskyfit",coordlist,imgpsf,"reserr",nstar=1,veri='no',simple='yes',verb='no')
        # reserr = skyfit + artificial star ########
        inp = "artbg.fits["+str(xb1)+":"+str(xb2)+","+str(yb1)+":"+str(yb2)+"]"
        out = "artsky.fits["+str(xb1)+":"+str(xb2)+","+str(yb1)+":"+str(yb2)+"]" 
        iraf.imsurfit("reserr","artbg",xorder=xbgord0,yorder=ybgord0,regions="section",section="sec")  
        midpt=np.mean(fits.getdata('artbg.fits'))
        iraf.imcopy('reserr.fits','artsky.fits')
        iraf.imcopy(inp,'artbgs.fits')
        iraf.imcopy("artbgs.fits",out)
        iraf.imarith("reserr","-","artsky","artsn",calctype="r",pixtype="r",verb='no') 
        iraf.imarith("artsn","+",midpt,"artsn",verb='no')

        artap1, artap2, artap3, artmag1, artmag2, artmag3, artfitmag, arttruemag, artmagerr, artcentx, artcenty = \
            fitsn(img,imgpsf,coordlist,_recenter,fwhm0,'reserr','artsn','artres',_show,_interactive,dmax,dmin,z11,z22,midpt,size,apco0)

        for ii in range(0,_numiter):
            lsc.util.delete("reserr.ar?")
            lsc.util.delete("artlist.ma?")
            lsc.util.delete("artsky.fit?")
            lsc.util.delete("artbg.fit?")
            lsc.util.delete("artbgs.fit?")
            lsc.util.delete("artsn.fit?")
            lsc.util.delete("artres.fit?")
            lsc.util.delete("artlist.al?")

            iraf.imsurfit("skyfit","artbg",xorder=xbgord0,yorder=ybgord0,regions="section",section="sec")
            midpt = np.mean(fits.getdata('artbg.fits'))
            iraf.imcopy("reserr.fits","artsky.fits")
            iraf.imcopy(inp,"artbgs.fits")
            iraf.imcopy("artbgs.fits",out)

            iraf.imarith("reserr","-","artsky","artsn",calctype="r",pixtype="r",verb='no') 
            iraf.imarith("artsn.fits","+",midpt,"artsn.fits",verb='no') 
            artap1, artap2, artap3, artmag1, artmag2, artmag3, artfitmag, arttruemag, artmagerr, artcentx, artcenty = \
                fitsn(img,imgpsf,coordlist,_recenter,fwhm0,'reserr','artsn','artres',_show,_interactive,dmax,dmin,z11,z22,midpt,size,0)
####### 
        if i==0: era='yes'
        else:    era='no'
        artx = .5+.25*artx
        arty = .5+.25*arty
        if _show:
            _tmp1,_tmp2,goon=lsc.util.display_image('skyfit.fits',1,'', '', False, _xcen=artx, _ycen=arty, _xsize=.25, _ysize=.25, _erase=era)
	try:
            tmpart.append(float(arttruemag[0]))
	except: pass
        i=i+1

    for i in tmpart:  print i 
    
    print " ########## "
    try:
        media = mean(array(tmpart))
        arterr = std(array(tmpart))
        arterr2 = std(compress((average(tmpart)-std(tmpart)<array(tmpart))&(array(tmpart)<average(tmpart)+std(tmpart)),array(tmpart)))
    except:
        media = 0
        arterr = 0
        arterr2 = 0
    print '### average = %6.6s \t arterr= %6.6s ' % (str(media),str(arterr))
    print '###  %6.6s \t (error at 1 sigma rejection) ' % (str(arterr2))
    lsc.util.delete("reserr.fit?,artbg.fit?,artstar.fit?,artres.fit?,artfit.fit?,artskyfit.fit?")
    lsc.util.delete("reserr.ar?")
    lsc.util.delete("artlist.co?")
    return arterr2,arterr
##############################################################################
