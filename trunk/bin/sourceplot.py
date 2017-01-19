#!/usr/bin/env python

import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

import lsc

description = "Displays a plot of the data of fake sources within magcomparison"
usage = "%(prog)s [-e epoch -g graph -n objname -m magnitude]"
version = "0.1"


def create_magcomparison_query(args):
    query = "SELECT * from magcomparison "
    if str(args.epoch) == '':
        query += ' WHERE id > 1 '
    elif '-' not in str(args.epoch):
        query += ' WHERE dayobs = {0} '.format(args.epoch)
    else:
        epoch1, epoch2 = args.epoch.split('-')
        query += ' WHERE dayobs >= {0} AND dayobs <= {1} '.format(epoch1, epoch2)

    if args.name != '':
        query += ' AND objname = "{0}" '.format(args.name)

    if args.bad is False:
        query += ' AND diffmag != 9999 '

    query = lsc.mysqldef.querylike(query, likelist=[args.filestr])

    if args.magnitude != []:
        query += ' AND ( inmag = {0} '.format(args.magnitude[0])
        if len(args.magnitude) > 1:
            for i in range(1, len(args.magnitude)):
                query += ' OR inmag = {0} '.format(args.magnitude[i])
        query += ") "
    return query


def produce_result_set(args):
    # Connect to database, and query the db
    try:
        hostname, username, passwd, database = lsc.mysqldef.getconnection('lcogt2')
        db = lsc.mysqldef.dbConnect(hostname, username, passwd, database)
    except:
        print 'Error: Could not connect to database'

    query = create_magcomparison_query(args)
    if args.keepout is False:
        query += "AND outlier = FALSE"
    resultSet = lsc.mysqldef.sqlquery(db, query)

    return resultSet


def updateoutliers(resultSet, _magnitude):
    print "#" * 75
    # Group rows into lists based on inmag
    maggroup = []
    for inmag in _magnitude:
        maggroup.append([])

    for row in resultSet:
        for i, inmag in enumerate(_magnitude):
            if row['inmag'] == inmag:
                maggroup[i].append(row)

    for i, inmagrow in enumerate(maggroup):
        try:
            # Find outlier range in each inmag
            diffmagset = []
            for row in inmagrow:
                diffmagset.append(row["diffmag"])
            Q1 = np.percentile(diffmagset, 25)
            Q3 = np.percentile(diffmagset, 75)
            IQR = Q3 - Q1
            outlierrange = [Q1 - (1.5 * IQR), Q3 + (1.5 * IQR)]
            print "The outlier range for a magnitude of", _magnitude[i], "is", outlierrange

            # Set the data outlier key accordingly & update db
            for row in inmagrow:
                if row["diffmag"] < outlierrange[0] or row["diffmag"] > outlierrange[1]:
                    row["outlier"] = True
                else:
                    row["outlier"] = False
                value = row['outlier']
                id = row['id']
                lsc.mysqldef.updatevalue('magcomparison', 'outlier', value, id, connection="lcogt2", filename0="id")
        except:
            print "No data for magnitude:", _magnitude[i]

    print "Outliers have been updated", '\n', '#' * 75


def make_xy_sets(resultSet):
    # Put all inmags into x, and all diffmags into y. The same index will
    # correspond to the same row.
    x = []
    y = []
    for row in resultSet:
        x.append(row['inmag'])
        y.append(row['diffmag'])
    xset = np.array(x)
    yset = np.array(y)

    return xset, yset


def create_datasets_for_inmag(_magnitude, xset, yset):
    # Create list of numpy arrays. Each numpy array should have all data for some inmag.
    # The numpy arrays will be sorted in ascending order
    dataset = []
    for magindex, inmag in enumerate(_magnitude):
        dataset.append([])
        for xindex, x in enumerate(xset):
            if x == inmag:
                dataset[magindex].append(yset[xindex])

    for i in range(len(_magnitude)):
        dataset[i] = np.array(dataset[i])

    return dataset


def len2shape(pltlength):
    # find different shapes that would work
    if pltlength > 81 or pltlength <= 0:
        print "pltlength needs to be less than 81 and greater than 0"
        return "01"
    shape = []
    for i in range(1, pltlength + 1):
        if ((pltlength) % i) == 0:
            if i > 9 or (pltlength / i) > 9:
                pass
            else:
                shape.append(str(i) + str(pltlength / i))

    # choose shape with smallest difference between two parts
    if pltlength == 0:
        print "Your input length was 0"
        shape = "00"
    elif len(shape) == 0:
        if pltlength < 81 or pltlength > 0:
            shape = len2shape(pltlength + 1)
    else:
        mindiff = abs(int(shape[0][0]) - int(shape[0][1]))
        mindiffindex = 0
        for i in range(len(shape)):
            if abs(int(shape[i][0]) - int(shape[i][1])) < mindiff:
                mindiff = abs(int(shape[i][0]) - int(shape[i][1]))
                mindiffindex = i
        shape = shape[mindiffindex]
    return shape


def shape2rc(shape):
    # Convert the shape into row and col
    row = int(shape[0])
    col = int(shape[1])
    return row, col


def make_boxplot_or_histogram(_graph, ax, data, inmag):
    xlabel = "Input Mag: " + str(inmag)
    ax.set_xlabel(xlabel)

    if _graph == "boxplot":
        ax.boxplot(dataset[ii])
        ax.yaxis.grid(True)
        ax.set_ylabel("Difference Mag")

    elif _graph == "histogram":
        n, bins, patches = ax.hist(data, bins=20)
        ax.set_ylabel("Number of data points in bin")
        ax.axvline(inmag, color='red')


def varstats(_magnitude, dataset):
    # Returns mean and standard deviation for each inmag
    means = []
    stddevs = []
    for i in range(len(_magnitude)):
        means.append(np.mean(dataset[i]))
        stddevs.append(np.std(dataset[i]))

    return means, stddevs


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description=description, usage=usage, version=version)
    parser.add_argument("-n", "--name", dest="name", default='', type=str,
                        help='-n object name   \t [%(default)s]')
    parser.add_argument("-m", "--magnitude", nargs="+", default=[], help=
    "Choose data from a specific magnitude", type=float)
    parser.add_argument("-e", "--epoch", dest="epoch", default='', type=str,
                        help='epoch to search for data \t [%(default)s]')
    parser.add_argument("-g", "--graph", dest="graph", type=str, default="scatter",
                        help="Choose type of graph [scatter, histogram, boxplot, varstats]")
    parser.add_argument("--bestfit", dest="bestfit", action="store_true",
                        default=False, help="Make a bestfit line in scatterplot")
    parser.add_argument("--yx", dest="yx", action="store_true",
                        default=False, help="Display a y = x graph with scatter")
    parser.add_argument("-b", "--bad", dest="bad", action="store_true",
                        default=False, help="include images with bad diffmag from plots")
    parser.add_argument("-k", "--keepout", dest="keepout", action="store_true",
                        default=False, help="Keep outliers in data")
    parser.add_argument("-u", "--updateout", dest="updateout", action="store_true",
                        default=False, help="Update the outliers in the database")
    parser.add_argument("--filestr", nargs="+", type=str, dest="filestr", default=[],
                        help='Enter part(s) of the filename you want to search for')
    parser.add_argument("--compare", dest="compare", action="store_true",
                        default=False, help="Compare optimal and hotpants subtraction; only for sdss")

    args = parser.parse_args()
    _name = args.name
    _magnitude = args.magnitude
    _epoch = args.epoch
    _graph = args.graph
    _bestfit = args.bestfit
    _yx = args.yx
    _bad = args.bad
    _keepout = args.keepout
    _updateout = args.updateout
    _filestr = args.filestr
    _compare = args.compare

    resultSet = produce_result_set(args)

    if _magnitude == []:
        _magnitude = np.arange(14, 20.5, 0.5)
    _magnitude.sort()

    if _updateout is True:
        updateoutliers(resultSet, _magnitude)

    # if _keepout is False:
    #    del resultSet
    #    resultSet = produce_result_set(args, _keepout=_keepout)

    # Set x(inmag) data and y(diffmag) data as ndarrays
    xset, yset = make_xy_sets(resultSet)
    dataset = create_datasets_for_inmag(_magnitude, xset, yset)

    if _compare is True:
        args.filestr = 'optimal'
        resultSetOptimal = produce_result_set(args)
        xsetOptimal, ysetOptimal = make_xy_sets(resultSetOptimal)

        args.filestr = 'sdss.diff'
        resultSetHotpants = produce_result_set(args)
        xsetHotpants, ysetHotpants = make_xy_sets(resultSetHotpants)

        if len(xsetOptimal) != 0:
            plt.scatter(xsetOptimal, ysetOptimal, color="blue", label="Optimal Subtractions")
        if len(xsetHotpants) != 0:
            plt.scatter(xsetHotpants, ysetHotpants, color="red", label="Hotpants Subtractions")
        plt.xlabel('Input Magnitudes')
        plt.ylabel('Difference Magnitudes')

        if _bestfit is True:
            if len(xsetOptimal) != 0:
                paramsOptimal = np.polyfit(xsetOptimal, ysetOptimal, 1)
                plt.plot(xsetOptimal, np.polyval(paramsOptimal, xsetOptimal), color="blue", label="Best Fit Optimal")
                print "Best fit line data for Optimal:"
                print "Slope =", str(paramsOptimal[0]) + ",", "y-int =", paramsOptimal[1]
            if len(xsetHotpants) != 0:
                paramsHotpants = np.polyfit(xsetHotpants, ysetHotpants, 1)
                plt.plot(xsetHotpants, np.polyval(paramsHotpants, xsetHotpants), color="red", label="Best Fit Hotpants")
                print "Best fit line data for Hotpants:"
                print "Slope =", str(paramsHotpants[0]) + ",", "y-int =", paramsHotpants[1]
            plt.legend(loc="upper left")
            if len(xsetOptimal) != 0 and len(xsetHotpants) != 0:
                plt.annotate(xy=(18, 15), s="Params: slope, y-intercept \nOptimal: {0}, {1} \nHotpants {2}, {3}".format(
                    round(paramsOptimal[0], 2),
                    round(paramsOptimal[1], 2),
                    round(paramsHotpants[0], 2),
                    round(paramsHotpants[1], 2)))
            elif len(xsetOptimal) == 0 and len(xsetHotpants) != 0:
                plt.annotate(xy=(18, 15),
                             s="Params: slope, y-intercept\nHotpants {0}, {1}".format(round(paramsHotpants[0], 2),
                                                                                      round(paramsHotpants[1], 2)))
            elif len(xsetOptimal) == 0 and len(xsetHotpants) != 0:
                plt.annotate(xy=(18, 15),
                             s="Params: slope, y-intercept\nHotpants {0}, {1}".format(round(paramsOptimal[0], 2),
                                                                                      round(paramsOptimal[1], 2)))
            plt.show()

    # If user wants a scatterplot
    elif _graph == "scatter":
        plt.scatter(xset, yset)
        plt.xlabel('Input Magnitudes')
        plt.ylabel('Difference Magnitudes')
        # Create bestfit line in scatterplot
        if _bestfit == True:
            a = np.polyfit(xset, yset, 1)
            plt.plot(xset, a[0] * xset + a[1], color="red", label="Best Fit")
            print "Best fit line data:"
            print "Slope =", str(a[0]) + ",", "y-int =", a[1]

        # Create y = x line in scatterplot
        if _yx == True:
            plt.plot(xset, xset, color="purple", label="y = x")
        # Create legend
        if _bestfit or _yx:
            plt.legend(loc="upper left")



    # If user wants a boxplot or histogram
    elif _graph in ['boxplot', 'histogram']:
        shape = len2shape(len(_magnitude))
        row, col = shape2rc(shape)
        fig, axes = plt.subplots(nrows=row, ncols=col, figsize=(12, 7))
        fig.tight_layout()

        ii = 0
        for i in range(row):
            if row == 1:
                axis = axes
                if col == 1:
                    axis = [axis]
            else:
                axis = axes[i]
            for ax in axis:
                if ii < len(_magnitude):
                    make_boxplot_or_histogram(_graph, ax, dataset[ii], _magnitude[ii])
                    ii += 1

    # If user wants variable statistics for each inmag
    elif _graph == "varstats":
        means, stddevs = varstats(_magnitude, dataset)
        for i in range(len(_magnitude)):
            print "For an input magnitude of", _magnitude[i]
            print "Mean =", means[i], "and Standard Deviation =", stddevs[i], '\n'

    else:
        sys.argv.append('--help')
        args = parser.parse_args()

    plt.show()