#!/usr/bin/env python

import lsc
import base64
from LCOGTingest import *
from datetime import datetime, timedelta
import os
import sys

if len(sys.argv) > 1:
    daterange = sys.argv[1]
    start, end = daterange.split('-')
    start = start[0:4] + '-' + start[4:6] + '-' + start[6:8]
    end = end[0:4] + '-' + end[4:6] + '-' + end[6:8]
else:
    now = datetime.utcnow()
    start = datetime.strftime(now - timedelta(days=7), '%Y-%m-%d') # check for data in the last week
    end = datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
    daterange = datetime.strftime(now - timedelta(days=7), '%Y%m%d') + '-' + datetime.strftime(now, '%Y%m%d')

login = lsc.mysqldef.query(["select username, userpw from programs where idcode='KEY2014A-003'"], conn)
username = login[0]['username']
password = base64.decodestring(login[0]['userpw'])
authtoken = authenticate(username, password)

frames = get_metadata(authtoken, start=start, end=end, OBSTYPE='EXPOSE', RLEVEL=91, public=False)       # all images where SNEx is a co-I
for telid in ['2m0a', '1m0a', '0m4a', '0m4b', '0m4c']:
    frames += get_metadata(authtoken, start=start, end=end, PROPID='standard', TELID=telid, RLEVEL=91)  # all photometric standards (except SQA)
frames += get_metadata(authtoken, start=start, end=end, INSTRUME='en06', RLEVEL=0, public=False)        # all FTN spectra SNEx is a co-I
frames += get_metadata(authtoken, start=start, end=end, INSTRUME='en05', RLEVEL=0, public=False)        # all FTS spectra SNEx is a co-I
frames += get_metadata(authtoken, start=start, end=end, PROPID='OGG_calib', RLEVEL=0)                   # FTN standard star spectra
frames += get_metadata(authtoken, start=start, end=end, PROPID='COJ_calib', RLEVEL=0)                   # FTS standard star spectra
frames += get_metadata(authtoken, start=start, end=end, PROPID='LCOEPO2016B-001', RLEVEL=91)            # supernova tracker images

print 'Total number of frames:', len(frames)

for frame in frames:
    try:
        filepath, filename = download_frame(frame)
    except Exception as e:
        print '!!! FAILED TO DOWNLOAD ' + frame['filename']
        sys.stderr.write(e)
        continue
    try:
        db_ingest(filepath, filename)
    except Exception as e:
        print '!!! FAILED TO INGEST ' + filename
        sys.stderr.write(e)
        continue
    if '-en0' in filename and '-e00.fits' in filename and not os.path.isfile(filepath + filename.replace('.fits', '.png')):
        try:
            fits2png(filepath + filename)
        except Exception as e:
            print '!!! FAILED TO MAKE PNG FOR ' + filename
            sys.stderr.write(e)

os.system('lscingestredudata.py -e ' + daterange) # ingest new data into photlco
