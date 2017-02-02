#!/usr/bin/env python

from argparse import ArgumentParser
from lsc.lscabsphotdef import sloan2file

parser = ArgumentParser()
parser.add_argument('ra', type=float, help='right ascension (degrees)')
parser.add_argument('dec', type=float, help='declination (degrees)')
parser.add_argument('-r', '--radius', default=10., type=float, help='search radius (arcmin)')
parser.add_argument('-m', '--mag1', default=13., type=float, help='brighter magnitude cut')
parser.add_argument('-M', '--mag2', default=20., type=float, help='fainter magnitude cut')
parser.add_argument('-o', '--output', default='sloan.cat', help='name of output file')
args = parser.parse_args()

sloan2file(args.ra, args.dec, args.radius, args.mag1, args.mag2, args.output)
