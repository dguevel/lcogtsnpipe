from astropy.io import fits
import os
import numpy as np
import lsc
import datetime

def jd2date(inputjd):
 jd0 = 2451544.5 # On Jan 1, 2000 00:00:00
 return datetime.datetime(2000,01,01,00,00,00)+datetime.timedelta(days=inputjd-jd0)


def MJDnow(datenow='',verbose=False):
   import time
   _JD0=55927.
   if not datenow:
      datenow=datetime.datetime(time.gmtime().tm_year, time.gmtime().tm_mon, time.gmtime().tm_mday, time.gmtime().tm_hour, time.gmtime().tm_min, time.gmtime().tm_sec)
   _JDtoday=_JD0+(datenow-datetime.datetime(2012, 01, 01,00,00,00)).seconds/(3600.*24)+\
             (datenow-datetime.datetime(2012, 01, 01,00,00,00)).days
   if verbose: print 'JD= '+str(_JDtoday)
   return _JDtoday


def SDSS_gain_dark(camcol, ugriz, run):
    if camcol == 1:
        if ugriz == 'u':
            gain = 1.62
            dark = 9.61
        elif ugriz == 'g':
            gain = 3.32
            dark = 15.6025
        elif ugriz == 'r':
            gain = 4.71
            dark = 1.8225
        elif ugriz == 'i':
            gain = 5.165
            dark = 7.84
        elif ugriz == 'z':
            gain = 4.745
            dark = 0.81
        else:
            print 'ERROR in SDSS_dark_gain: UGRIZ not set!'
    elif camcol == 2:
        if ugriz == 'u':
            if run < 1100:
                gain = 1.595
            elif run > 1100:
                gain = 1.825
            else:
                print 'ERROR in SDSS_dark_gain: RUN not set!'
            dark = 12.6025
        elif ugriz == 'g':
                gain = 3.855
                dark = 1.44
        elif ugriz == 'r':
                gain = 4.6
                dark = 1.00
        elif ugriz == 'i':
            gain = 6.565
            if run < 1500:
                dark = 5.76
            elif run > 1500:
                dark = 6.25
            else:
                print 'ERROR in SDSS_dark_gain: RUN not set!'
        elif ugriz == 'z':
            gain = 5.155
            dark = 1.0
        else:
            print 'ERROR in SDSS_dark_gain: UGRIZ not set!'
    elif camcol == 3:
        if ugriz == 'u':
            gain = 1.59
            dark = 8.7025
        elif ugriz == 'g':
            gain = 3.845
            dark = 1.3225
        elif ugriz == 'r':
            gain =  4.72
            dark = 1.3225
        elif ugriz == 'i':
            gain = 4.86
            dark = 4.6225
        elif ugriz == 'z':
            gain = 4.885
            dark = 1.0
        else:
            print 'ERROR in SDSS_dark_gain: UGRIZ not set!'
    elif camcol == 4:
        if ugriz == 'u':
            gain = 1.6
            dark = 12.6025
        elif ugriz == 'g':
            gain = 3.995
            dark = 1.96
        elif ugriz == 'r':
            gain =  4.76
            dark = 1.3225
        elif ugriz == 'i':
            gain = 4.885
            if run < 1500:
                dark = 6.25
            elif run > 1500:
                dark = 7.5625
            else:
                print 'ERROR in SDSS_dark_gain: RUN not set!'
        elif ugriz == 'z':
            gain = 4.775
            if run < 1500:
                dark = 9.61
            elif run > 1500:
                dark = 12.6025
            else:
                print 'ERROR in SDSS_dark_gain: RUN not set!'
        else:
            print 'ERROR in SDSS_dark_gain: UGRIZ not set!'
    elif camcol == 5:
        if ugriz == 'u':
            gain = 1.47
            dark = 9.3025
        elif ugriz == 'g':
            gain = 4.05
            dark = 1.1025
        elif ugriz == 'r':
            gain = 4.725
            dark = 0.81
        elif ugriz == 'i':
            gain = 4.64
            dark = 7.84
        elif ugriz == 'z':
            gain = 3.48
            if run < 1500:
                dark = 1.8225
            elif run > 1500:
                dark = 2.1025
            else:
                print 'ERROR in SDSS_dark_gain: RUN not set!'
        else:
            print 'ERROR in SDSS_dark_gain: UGRIZ not set!'
    elif camcol == 6:
        if ugriz == 'u':
            gain = 2.17
            dark = 7.0225
        elif ugriz == 'g':
            gain = 4.035
            dark = 1.8225
        elif ugriz == 'r':
            gain = 4.895
            dark = 0.9025
        elif ugriz == 'i':
            gain = 4.76
            dark = 5.0625
        elif ugriz == 'z':
            gain = 4.69
            dark = 1.21
        else:
            print 'ERROR in SDSS_dark_gain: UGRIZ not set!'
    else:
        print 'ERROR in SDSS_dark_gain: CAMCOL is not set!'
    return gain, dark

def downloadsdss(_ra,_dec,_band,_radius=20, force=False):
    from astroquery.sdss import SDSS
    from astropy import coordinates as coords
    import astropy.units as u
    from astropy.io import fits
    import os
    import sys
    import string
    import numpy as np
    from scipy import interpolate
    pos = coords.SkyCoord(ra=float(_ra)*u.deg,dec=float(_dec)*u.deg)
    print 'pos =', pos
    xid = SDSS.query_region(pos, spectro=False, radius=_radius*u.arcsec)
    print xid
    if xid:
       pointing=[]
       for i in xid:
          if i['run'] > 300:
             if (i['run'],i['camcol'],i['field']) not in pointing:
                pointing.append((i['run'],i['camcol'],i['field']))
       # if too many pointing, take only first 40
       if len(pointing) > 50:
          nn=50
       else: 
          nn=len(pointing)
       filevec=[]
       print len(pointing)
       for run, camcol, field in pointing[:nn]:
          #  naomaggie image
          output1 = _band+'_SDSS_'+str(run)+'_'+str(camcol)+'_'+str(field)+'.fits'
          #  image in count
          output2 = _band+'_SDSS_'+str(run)+'_'+str(camcol)+'_'+str(field)+'c.fits'
          #  weight image
          output3 = _band+'_SDSS_'+str(run)+'_'+str(camcol)+'_'+str(field)+'.weight.fits'
          #  sky image
          output4 = _band+'_SDSS_'+str(run)+'_'+str(camcol)+'_'+str(field)+'.sky.fits'
          if os.path.isfile(output1) and not force:
              print 'already downloaded', output1
              filevec.append(output2)
              filevec.append(output3)
              continue
          im = SDSS.get_images(run=run, camcol=camcol, field=field, band=_band, cache=True)
          if os.path.isfile(output1):
             os.system('rm '+output1)
          if os.path.isfile(output2):
             os.system('rm '+output2)
          if os.path.isfile(output3):
             os.system('rm '+output3)
          if os.path.isfile(output4):
             os.system('rm '+output4)
          im[0].writeto(output1)
#         im[0][0].writeto(output2)

          FITS_file = fits.open(output1)
          new_header = FITS_file[0].header
          camcol     = FITS_file[0].header['CAMCOL']  # camcol
          ugriz      = FITS_file[0].header['FILTER']  # ugriz filter
          run1        = FITS_file[0].header['RUN']     # run
          gain, dark_var = SDSS_gain_dark(camcol, ugriz, run1)
          new_header['gain']  = gain
          new_header['dark']  = dark_var
          new_header['BUNIT']  = 'counts'
          new_header['rdnoise']  = 2
          frame_image = FITS_file[0].data.transpose()
          allsky     = FITS_file[2].data['ALLSKY'].transpose()
          allsky     = allsky[:,:,0]
          xinterp    = FITS_file[2].data['XINTERP'].transpose()
          xinterp    = xinterp[:,0]
          yinterp    = FITS_file[2].data['YINTERP'].transpose()
          yinterp    = yinterp[:,0]
          sky_function = interpolate.interp2d(np.arange(allsky.shape[1]),\
                                              np.arange(allsky.shape[0]), allsky, kind='linear')
          sky_image    = sky_function(yinterp, xinterp) # in counts
          calib     = FITS_file[1].data #  nanomaggies per count
          calib_image = np.empty_like(frame_image)
          for i in np.arange(calib_image.shape[1]):
             calib_image[:,i] = calib
          # Calculate the error in the frame image for use fitting algorithms later.
          dn_image        = frame_image / calib_image  # + sky_image # counts
          dn_err_image    = np.sqrt((dn_image + sky_image)/ gain + dark_var)
          # frame_image_err = dn_err_image * calib_image  converts to nanomaggies
          
          frame_weight = 1 / ((dn_err_image)**2)
          new_header['SKYLEVEL']  = np.mean(sky_image)
          #  save image in count
          fits.writeto(output2, dn_image.transpose(), new_header,overwrite=True)
          #  save weight image
          fits.writeto(output3, frame_weight.transpose(), new_header,overwrite=True)
          #  save sky image 
          fits.writeto(output4, sky_image.transpose(), new_header,overwrite=True)
          filevec.append(output2)
          filevec.append(output3)
       return filevec
    else:
       return ''

def sdss_swarp(imglist,_telescope='spectral',_ra='',_dec='',output='', objname='',survey='sloan',combine_type='MEDIAN', show=False):
    import re
    import datetime
    import lsc
    import time
    import string

    if _telescope == 'spectral':
        pixelscale = 0.30104  # 2 meter
        _imagesize =  2020
    elif _telescope == 'sbig':
            pixelscale = 0.467  # 1 meter
            _imagesize =  2030
    elif _telescope == 'sinistro':
            pixelscale = 0.387  # 1 meter
            _imagesize =  4020

    if survey =='sloan':
       out1 = 'SDSS'
       hdr = fits.getheader(imglist[0])
       _filter = hdr.get('filter')
       _gain   = hdr.get('gain')
       _ron   = hdr.get('rdnoise')
       if not _ra:
          _ra = hdr.get('CRVAL1')
       if not _dec:
          _dec = hdr.get('CRVAL2')
       _saturate = hdr.get('SATURATE')
       if not _saturate:
          _saturate = 61000
       if 'day-obs' in hdr:
          _dayobs = hdr.get('day-obs')
       elif 'date-obs' in hdr:
          _dayobs = re.sub('-','',hdr.get('date-obs'))

       if '/' in _dayobs:
          _dayobs = '19'+''.join(string.split(_dayobs,'/')[::-1])

       try:
          _mjd = MJDnow(datetime.datetime(int(str(_dayobs)[0:4]),int(str(_dayobs)[4:6]),int(str(_dayobs)[6:8])))
       except:
          print 'warning, no mjd'
          _mjd = 0
          _dayobs = '19991231'

    elif survey =='ps1':
       out1 = 'PS1'
       imglist2=[]
       for i,img in enumerate(imglist):
           print i,img
           hdr = fits.open(img)
           if os.path.isfile(re.sub('.fits','_1.fits',img)):
              os.system('rm '+re.sub('.fits','_1.fits',img))
           fits.writeto(re.sub('.fits','_1.fits',img),hdr[1].data,hdr[1].header)
           imglist2.append(re.sub('.fits','_1.fits',img))

       imglist = imglist2
       hdr = fits.getheader(imglist[0])
       _saturate = hdr.get('HIERARCH CELL.SATURATION')
       _filter = string.split(hdr.get('HIERARCH FPA.FILTER'),'.')[0]
       _gain   = hdr.get('HIERARCH CELL.GAIN')
       _ron   = hdr.get('HIERARCH CELL.READNOISE')
       _mjd = hdr.get('MJD-OBS')
       _dayobs = jd2date(_mjd+2400000.5).strftime('%Y%d%m')
       if not _ra:
          _ra = hdr.get('RA_DEG')
       if not _dec:
          _dec = hdr.get('DEC_DEG')

    #  airmass
    if 'airmass' in hdr:
        _airmass = hdr.get('airmass')
    else:
        _airmass = 1

    #  filters
    filt={'U':'U','B':'B','V':'V','R':'R','I':'I','u':'up','g':'gp','r':'rp','i':'ip','z':'zs'}
    if _filter in filt.keys():
        _filter = filt[_filter]

    if 'date-obs' in hdr:
       _dateobs = hdr.get('date-obs')
    else:
       _dateobs = jd2date(_mjd+2400000.5).strftime('%Y-%d-%m')

    print imglist[0]
    print _dateobs, _dayobs, _mjd, _filter

    if not output:
       output = _telescope+'_'+str(out1)+'_'+str(_dayobs)+'_'+str(_filter)+'_'+objname +'.fits'

    imgmask = [] 
    skylevel = []
    # if the template is from sloan, use mask and weight image
    if survey =='sloan':
       welist = [i for i in imglist if '.weight.' in i]
       if len(welist):
          # if weight images provided, use them in swarp
          # and take out them from input list image
          imglist = [j for j in imglist if j not in welist]
          imgmask = welist
          for jj in imglist:
             img_data,img_header=fits.getdata(jj, header=True)
             if 'SKYLEVEL' in img_header:
                skylevel.append(img_header['SKYLEVEL'])
    elif survey=='ps1':
       wtlist = [i for i in imglist if '.wt_' in i]
       mklist = [i for i in imglist if '.mk_' in i]
       if len(wtlist):
          for i,name in enumerate(wtlist):
             weightimg = re.sub('.wt_','.weight.',name)
             imgmask.append(weightimg)
             if re.sub('.wt_','.mk_',name) in mklist:
                weight_data, weight_header = fits.getdata(name, header=True)
                mask_data, mask_header = fits.getdata(re.sub('.wt_','.mk_',name), header=True)
                weight_data = 1/weight_data 
                weight_fits = fits.PrimaryHDU(header=weight_header, data=weight_data)
                weight_fits.writeto(weightimg, output_verify='fix', overwrite=True)
             else:
                os.system('cp '+name+' '+weightimg)
       imglist = [j for j in imglist if (j not in wtlist) and (j not in mklist)]
       # measure skylevel in all ps1 images
       for jj in imglist:
          img_data,img_header=fits.getdata(jj, header=True)
          skylevel.append(np.mean(img_data))

#    elif len(welist):
#       imglist = [j for j in imglist if j not in welist]
#       imgmask = welist


    print imgmask
    print skylevel
    sampling = 'BILINEAR' # LANCZOS3
    line = 'swarp ' + ','.join(imglist) + ' -IMAGEOUT_NAME ' + str(output) + \
            ' -WEIGHTOUT_NAME ' + re.sub('.fits', '', output) + '.weight.fits' + \
            ' -RESAMPLE_DIR ./ -RESAMPLE_SUFFIX .swarptemp.fits -RESAMPLING_TYPE ' +sampling+ \
            ' -COMBINE Y  -COMBINE_TYPE ' + str(combine_type)+ \
            ' -VERBOSE_TYPE NORMAL -SUBTRACT_BACK Y -INTERPOLATE Y' + \
            ' -PIXELSCALE_TYPE MANUAL,MANUAL -PIXEL_SCALE ' + str(pixelscale) + ',' + str(pixelscale) + \
            ' -IMAGE_SIZE ' + str(_imagesize) + ',' + str(_imagesize) + \
            ' -CENTER_TYPE MANUAL,MANUAL -CENTER ' + str(_ra) + ',' + str(_dec) + \
            ' -GAIN_DEFAULT ' + str(_gain)

    if imgmask:
       line += ' -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_IMAGE ' +  ','.join(imgmask)
    print line
    os.system(line)

    # the output of swarp give the normalized weight 
    # we want to store the variance image
    # we invert the normalized weight and we "de-normalized" this image
    hd = fits.getheader(output)
    ar = fits.getdata(output)
    hd2 = fits.getheader(re.sub('.fits', '', output) + '.weight.fits')
    ar2 = fits.getdata(re.sub('.fits', '', output) + '.weight.fits')
    variance = 1 / ar2
    #  this is to take in account that the weight is normalized
    variance *= (np.median(np.abs(ar - np.median(ar)))*1.48)**2/np.median(variance)
    varimg = re.sub('.fits', '', output) + '.var.fits'
    fits.writeto(varimg, variance, hd2, overwrite=True)

    # put the saturation all values where the weight is zero 
    ar = np.where(ar2 == 0, _saturate, ar)

    if len(skylevel):
        hd['SKYLEVEL'] = (np.mean(skylevel), 'average sky level')
    hd['L1FWHM']   = (9999,       'FHWM (arcsec) - computed with sextractor')
    hd['WCSERR']   = (0,          'error status of WCS fit. 0 for no error')
    hd['MJD-OBS']  = (_mjd,       'MJD')
    hd['RA']       = (_ra,        'RA')
    hd['DEC']      = (_dec,       'DEC')
    hd['RDNOISE']  = (_ron,       'read out noise')
    hd['PIXSCALE'] = (pixelscale, '[arcsec/pixel] Nominal pixel scale on sky')
    hd['FILTER']   = (_filter,    'filter used')
    hd['DAY-OBS']   = (_dayobs,    'day of observation')
    hd['AIRMASS']  = (_airmass,   'airmass')
    hd['DATE-OBS'] = (_dateobs,   'date of observation')
    hd['GAIN']     = (_gain,      'gain')
    hd['SATURATE'] = (_saturate,  'saturation level ')
    if objname:
        hd['OBJECT'] = (objname, 'title of the data set')
    if survey == 'sloan':
        hd['TELESCOP'] = ('SDSS', 'name of the telescope')
        hd['INSTRUME'] = ('SDSS', 'instrument used')
        hd['SITEID'] = ('SDSS', 'ID code of the Observatory site')
    elif survey == 'ps1':
        hd['TELESCOP'] = ('PS1', 'name of the telescope')
        hd['INSTRUME'] = ('PS1', 'instrument used')
        hd['SITEID'] = ('PS1', 'ID code of the Observatory site')

    ar, hdr = northupeastleft(data=ar, header=hd)
    out_fits = fits.PrimaryHDU(header=hd, data=ar)
    out_fits.writeto(output, overwrite=True, output_verify='fix')
    northupeastleft(filename=varimg)
    if show:
       lsc.display_image(output,2,True,'','')
    return output, varimg

def northupeastleft(filename='', data=None, header=None):
    if filename:
        data, header = fits.getdata(filename, header=True)
    else:
        header = header.copy()
    if abs(header['cd1_2']) > abs(header['cd1_1']):
        data = data.T
        header['cd1_1'], header['cd1_2'] = header['cd1_2'], header['cd1_1']
        header['cd2_2'], header['cd2_1'] = header['cd2_1'], header['cd2_2']
        header['crpix1'], header['crpix2'] = header['crpix2'], header['crpix1']
        header['naxis1'], header['naxis2'] = header['naxis2'], header['naxis1']
        header['datasec'] = '[' + ','.join(header['datasec'].strip('[]').split(',')[::-1]) + ']'
        print 'swapping x and y axes'
    if header['cd1_1'] > 0:
        data = data[:,::-1]
        header['cd1_1'] *= -1
        header['cd2_1'] *= -1
        print 'flipping around x'
    if header['cd2_2'] < 0:
        data = data[::-1]
        header['cd2_2'] *= -1
        header['cd1_2'] *= -1
        print 'flipping around y'
    if filename:
        fits.writeto(filename, data, header, overwrite=True, output_verify='fix')
    else:
        return data, header

##################################################################################
def sloanimage(img,survey='sloan',frames=[], show=False, force=False):
   import sys
   from lsc import readhdr, readkey3,deg2HMS,display_image
   if show:
      display_image(img,1,True,'','')
   hdr = readhdr(img)
   _ra = readkey3(hdr,'RA')
   _dec = readkey3(hdr,'DEC')
   _object = readkey3(hdr,'object')
   _instrume = readkey3(hdr,'instrume')
   _filter = readkey3(hdr,'filter')
   _radius = 1100
   filt={'up':'u','gp':'g','rp':'r','ip':'i','zs':'z'}

   if _filter in filt.keys():
      _band = filt[_filter]
   else:
      _band = _filter

   if 'fs' in _instrume:
      _telescope = 'spectral'
   elif 'fl' in _instrume:
      _telescope = 'sinistro'
   elif 'kb' in _instrume:
      _telescope = 'sbig'

   print _ra, _dec, _band, _radius
   if survey == 'sloan':
      frames =  downloadsdss(_ra, _dec, _band, _radius, force)
   elif survey == 'ps1':
      if len(frames) == 0:
         delta= 0.22
         DR = delta/np.cos(_dec*np.pi/180)
         DD = delta
         f=open(_object+'_'+_band+'_ps1request.txt','w')
         f.write('%s   %s   %s\n' %(str(_ra),str(_dec),str(_band)))
         f.write('%s   %s   %s\n' %(str(_ra+DR),str(_dec+DD),str(_band)))
         f.write('%s   %s   %s\n' %(str(_ra-DR),str(_dec-DD),str(_band)))
         f.write('%s   %s   %s\n' %(str(_ra+DR),str(_dec-DD),str(_band)))
         f.write('%s   %s   %s\n' %(str(_ra-DR),str(_dec+DD),str(_band)))
         f.close()
         print '#'*20
         print "Please submit file:"+_object+'_'+_band+'_ps1request  at this link (you need an account)\n'
         print "   http://psps.ifa.hawaii.edu/PSI/postage_stamp.php    "
         print "   select:\n       Survey ID:    3PI          3PI.PV3  \n  "
         print "   Image Type:       Total Stacked Image, 1 pixel 0.250 "
         print "   Method of Image Selection by:   Coordinate- Images are selected based on supplied Ra and DEC   "
         print "   Size of the Postage Stamp:   (x) Arc-Second             Width:  2000         Height: 2000    pixel"
         print "   Center Coordinate of Image  - Input coordinate From: "
         print "                  (x)  Upload File           "
         print "        Choose File:    "+_object+'_'+_band+'_ps1request.txt'
         print '#'*20
         answ = raw_input('Do you want to wait that the frames are downloded [y/n]  [y] ? ')
         if not answ: 
             answ= 'y'
         if answ in ['Yes','yes','Y','y']:
              print 'Which is the last req_name at this page: '
              answ1 = raw_input('http://psps.ifa.hawaii.edu/PSI/postage_stamp_results.php ? ' )
              if not answ1:  
                  sys.exit('no name provided, no PS1 images have been downloaded')
              else:
                  print 'try download........'
                  frames = downloadPS1('./',answ1)
      else:
          frames2 = []
          for img in frames:
               if '_'+_band+'_' in img:
                    frames2.append(img)

          frames = frames2
   if len(frames):
         out, varimg = sdss_swarp(frames,_telescope,_ra,_dec,'',_object, survey, show=show)
   else:
       sys.exit('exit, no PS1 images have been downloaded')
   return out, varimg
####################################################


def downloadPS1(homedir,filename):
    import sys
    import string
    import os
    import re
    import urllib
    import urllib2
    parent_dir = os.getcwd()+'/'
    directory=filename+'/'
    os.system('rm '+str(homedir)+'pssindex.txt')
    dataStoreBase = 'http://datastore.ipp.ifa.hawaii.edu/pstampresults/'
    dataStoreProduct = directory
    urlOfFileToDownload = dataStoreBase + dataStoreProduct + 'index.txt'
    print urlOfFileToDownload
    localFilename = homedir+'pss' + os.path.basename(urlOfFileToDownload)
    try:
       urllib.urlretrieve(urlOfFileToDownload, localFilename)
    except:
        print 'req_name found on poststamp datastore'
        sys.exit()
    frames = []
    try:
        f=file(homedir+'pssindex.txt','r')
        _index=f.readlines()
        f.close()
        for i in range(0,len(_index)):
            print string.split(_index[i],'|')[0],string.count(string.split(_index[i],'|')[0],'results.fits')
            if  string.count(string.split(_index[i],'|')[0],'.fits') and string.count(string.split(_index[i],'|')[0],'results.fits')==0:

                urlOfFileToDownload3 = dataStoreBase + dataStoreProduct +string.split(_index[i],'|')[0]
                urlOfFileToDownload3=re.sub('.txt','',urlOfFileToDownload3)
                localFilename3 = parent_dir+ os.path.basename(urlOfFileToDownload3)
                if not os.path.isfile(localFilename3):
                    print 'downloading file: '+string.split(_index[i],'|')[0]
                    try:
                        urllib.urlretrieve(urlOfFileToDownload3, localFilename3)
                    except:
                        print 'problem '+str(urlOfFileToDownload3)
                        pass
                else:
                    print 'file already downloaded '

                if not os.path.isdir(homedir+filename):
                    os.mkdir(homedir+filename)
                os.system('mv '+string.split(localFilename3,'/')[-1]+' '+homedir+filename+'/')
                if 'unconv.fits' in string.split(localFilename3,'/')[-1]:
                           frames.append(homedir+filename++'/'+string.split(localFilename3,'/')[-1])
    except:
        print 'stamp_directory not found '
        sys.exit()
    os.system('rm '+str(homedir)+'pssindex.txt')
    print 'download COMPLETE '
    return frames

################################################################################################################
