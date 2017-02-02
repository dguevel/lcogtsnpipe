#!/usr/bin/env python
#
#
#  query apass catalogues
#
#
##########################################################
description=">> query APASS catalogue  "
usage = "%prog -r RA -d DEC [-R radius -o name_output]"

from optparse import OptionParser
import os,string,re
import glob,math,sys
import numpy as np

############################################################################
def deg2HMS(ra='', dec='', round=False):
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

def vizq(_ra,_dec,catalogue,radius):
    ''' Query vizquery '''
    _site='vizier.u-strasbg.fr'
    cat={'usnoa2':['I/252/out','USNO-A2.0','Rmag'],'2mass':['II/246/out','2MASS','Jmag'],
         'landolt':['II/183A/table2','','Vmag,B-V,U-B,V-R,R-I,Star,e_Vmag'],
         'ucac4':['I/322A/out','','Bmag,Vmag,gmag,rmag,imag,e_Vmag,e_Bmag,e_gmag,e_rmag,e_imag,UCAC4'],
         'apass':['II/336/apass9','',"Bmag,Vmag,g'mag,r'mag,i'mag,e_Vmag,e_Bmag,e_g'mag,e_r'mag,e_i'mag"],
         'usnob1':['I/284/out','USNO-B1.0','R2mag'],'sdss7':['II/294/sdss7','','objID,umag,gmag,rmag,imag,zmag,gc'],
         'sdss9':['V/139/sdss9','','objID,umag,gmag,rmag,imag,zmag,e_umag,e_gmag,e_rmag,e_imag,e_zmag,gc'],
         'sdss7':['II/294/sdss7','','objID,umag,gmag,rmag,imag,zmag,e_umag,e_gmag,e_rmag,e_imag,e_zmag,gc'],
         'sdss8':['II/306/sdss8','','objID,umag,gmag,rmag,imag,zmag,e_umag,e_gmag,e_rmag,e_imag,e_zmag,gc']}

    a=os.popen('vizquery -mime=tsv  -site='+_site+' -source='+cat[catalogue][0]+\
                   ' -c.ra='+str(_ra)+' -c.dec='+str(_dec)+' -c.eq=J2000 -c.rm='+str(radius)+\
                   ' -c.geom=b -oc.form=h -sort=_RA*-c.eq -out.add=_RAJ2000,_DEJ2000 -out.max=10000 -out='+\
                   cat[catalogue][1]+' -out="'+cat[catalogue][2]+'"').read()
    print 'vizquery -mime=tsv  -site='+_site+' -source='+cat[catalogue][0]+\
                   ' -c.ra='+str(_ra)+' -c.dec='+str(_dec)+' -c.eq=J2000 -c.rm='+str(radius)+\
                   ' -c.geom=b -oc.form=h -sort=_RA*-c.eq -out.add=_RAJ2000,_DEJ2000 -out.max=10000 -out='+\
                   cat[catalogue][1]+' -out="'+cat[catalogue][2]+'"'
    aa=a.split('\n')
    bb=[]
    for i in aa:
        if i and i[0]!='#':   bb.append(i)
    _ra,_dec,_name,_mag=[],[],[],[]
    for ii in bb[3:]:
        aa=ii.split('\t')

        rr, dd = deg2HMS(ra=re.sub(' ',':',aa[0]), dec=re.sub(' ',':',aa[1]), round=False)
        _ra.append(rr)
        _dec.append(dd)
        _name.append(aa[2])
    dictionary={'ra':_ra,'dec':_dec,'id':_name}
    sss=string.split(cat[catalogue][2],',')
    for ii in sss: dictionary[ii]=[]
    for ii in bb[3:]:
        aa=ii.split('\t')
        for gg in range(0,len(sss)):
           if sss[gg] not in ['UCAC4','id']:
              try:
                 dictionary[sss[gg]].append(float(aa[2+gg]))
              except:    
                 dictionary[sss[gg]].append(float(9999))
           else:
                 dictionary[sss[gg]].append(str(aa[2+gg]))

    if catalogue in ['sdss7','sdss9','sdss8']:
        dictionary['u']=dictionary['umag']
        dictionary['g']=dictionary['gmag']
        dictionary['r']=dictionary['rmag']
        dictionary['i']=dictionary['imag']
        dictionary['z']=dictionary['zmag']
        dictionary['uerr']=dictionary['e_umag']
        dictionary['gerr']=dictionary['e_gmag']
        dictionary['rerr']=dictionary['e_rmag']
        dictionary['ierr']=dictionary['e_imag']
        dictionary['zerr']=dictionary['e_zmag']
        for key in dictionary.keys():
           if key!='r':
              dictionary[key]=np.compress((np.array(dictionary['r'])<19)&(np.array(dictionary['r']>10)),dictionary[key])
        dictionary['r']=np.compress((np.array(dictionary['r'])<19)&(np.array(dictionary['r']>10)),dictionary['r'])

    elif  catalogue=='landolt':
        dictionary['B']=np.array(dictionary['Vmag'])+np.array(dictionary['B-V'])
        dictionary['U']=np.array(dictionary['B'])+np.array(dictionary['U-B'])
        dictionary['V']=np.array(dictionary['Vmag'])
        dictionary['Verr']=np.array(dictionary['e_Vmag'])
        dictionary['R']=np.array(dictionary['Vmag'])-np.array(dictionary['V-R'])
        dictionary['I']=np.array(dictionary['R'])-np.array(dictionary['R-I'])
        dictionary['id']=np.array(dictionary['Star'])
    elif  catalogue=='ucac4':
        dictionary['B']=np.array(dictionary['Bmag'])
        dictionary['V']=np.array(dictionary['Vmag'])
        dictionary['g']=np.array(dictionary['gmag'])
        dictionary['r']=np.array(dictionary['rmag'])
        dictionary['i']=np.array(dictionary['imag'])
        dictionary['Berr']=np.array(dictionary['e_Bmag'],float)/100.
        dictionary['Verr']=np.array(dictionary['e_Vmag'],float)/100.
        dictionary['gerr']=np.array(dictionary['e_gmag'],float)/100.
        dictionary['rerr']=np.array(dictionary['e_rmag'],float)/100.
        dictionary['ierr']=np.array(dictionary['e_imag'],float)/100.
        dictionary['id']=np.array(dictionary['UCAC4'],str)
        for key in dictionary.keys():
           if key!='r':
              dictionary[key]=np.compress((np.array(dictionary['r'])<22)&(np.array(dictionary['r']>10.5)),dictionary[key])
        dictionary['r']=np.compress((np.array(dictionary['r'])<22)&(np.array(dictionary['r']>10.5)),dictionary['r'])
    elif  catalogue=='apass':
        dictionary['B']=np.array(dictionary['Bmag'])
        dictionary['V']=np.array(dictionary['Vmag'])
        dictionary['g']=np.array(dictionary["g'mag"])
        dictionary['r']=np.array(dictionary["r'mag"])
        dictionary['i']=np.array(dictionary["i'mag"])
        dictionary['Berr']=np.array(dictionary['e_Bmag'],float)
        dictionary['Verr']=np.array(dictionary['e_Vmag'],float)
        dictionary['gerr']=np.array(dictionary["e_g'mag"],float)
        dictionary['rerr']=np.array(dictionary["e_r'mag"],float)
        dictionary['ierr']=np.array(dictionary["e_i'mag"],float)
        for key in dictionary.keys():
           if key!='r':
              dictionary[key]=np.compress((np.array(dictionary['r'])<22)&(np.array(dictionary['r']>10.5)),dictionary[key])
        dictionary['r']=np.compress((np.array(dictionary['r'])<22)&(np.array(dictionary['r']>10.5)),dictionary['r'])
    return dictionary
################################################################################

def readapass2(_ra,_dec,_radius,_outputfile):
    dictionary=vizq(_ra,_dec,'apass',_radius)
    filters=['B', 'V', 'Pg', 'Pr', 'Pi']    
    if _outputfile: filename=_outputfile
    else:  filename='test_apass.txt'

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
    filters=['B', 'V', 'g', 'r', 'i']
#    return header,dictionary
    for i in range(0,len(dictionary['ra'])): 
        ff.write('%14s %14s  %3s  ' % (str(dictionary['ra'][i]),str(dictionary['dec'][i]),str(m)))
        m=m+1
        for f in filters:
            if float(dictionary[f][i])>0:
                ff.write(' %6.3f %6.3f  ' % (float(dictionary[f][i]),float(dictionary[f+'err'][i])))
            else:
                ff.write(' %6.3f %6.3f  ' % (float(9999),float(0.0)))
        ff.write('\n')
    ff.close()

#################################3
if __name__ == "__main__":
    parser = OptionParser(usage=usage,description=description)
    parser.add_option("-r", "--RA",dest="RA",default='12.0',type="str",
                  help='RA  (degree) \t [%default]')
    parser.add_option("-d", "--DEC",dest="DEC",default='12.0',type="str",
                  help='DEC (degree) \t [%default]')
    parser.add_option("-c", "--catalogue",dest="cat",default='apass',type="str",
                  help='catalogue  \t [%default]')
    parser.add_option("-o", "--output",dest="output",default='output_apass.cat',type="str",
                  help='output  \t [%default]')
    parser.add_option("-R", "--radius",dest="radius",default=30,type=float,
                  help='radius  \t [%default]')
    
    option,args = parser.parse_args()
    _ra=option.RA
    _dec=option.DEC
    _radius=option.radius
    _catalogue=option.cat
    _outputfile=option.output
    print _ra,_dec,_radius
    readapass2(_ra,_dec,_radius,_outputfile)
