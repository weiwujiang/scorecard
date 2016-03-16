#coding = 'utf-8'
"""data explore for raw datasheet"""
__author__ = "changandao&jiangweiwu"
__date__   = "2016.3.8"

import numpy as np
import math
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

FilePath = '../data/'
Dataset = 'Training Set/'
MasterFile = FilePath + Dataset + 'PPD_Training_Master_GBK_3_1_Training_Set.csv'
Master = pd.read_csv(MasterFile,encoding="gb18030")
TypeStatement = pd.read_csv(FilePath + 'TypeState.csv')


def WOEFUNC(goodpct,badpct):
    global pct_ratio
    pct_ratio = goodpct/badpct
    pct_ratio =  pct_ratio.fillna(0.)
    npratio = np.array(pct_ratio)
    WOE = np.log(npratio)
    WOE = pd.Series(WOE)
    return WOE


def IVCAL(good,bad):
    goodall = good.sum()
    badall = bad.sum()
    pct_good = good/goodall
    pct_bad = bad/badall
    WOEvalue = WOEFUNC(pct_good,pct_bad)
    pct_diff = pct_good-pct_bad
    pct_diff =  pct_diff.fillna(0.)
    npdiff = np.array(pct_diff)
    iv = npdiff*WOEvalue
    ivser = pd.Series(iv)
    IV = ivser.sum()
    return IV


def resetType(df,oridf):
    typetmp = df.dropna(axis=1)
    se = typetmp.set_index('Idx')
    ser = pd.Series(se['Index'],index = typetmp['Idx'])
    for i in ser.index:
        if ser[i]=='Categorical':
            ser[i] = 'object'
        elif ser[i]=='Numerical':
            if oridf[i].dtypes == 'object':
                print i, oridf.columns.get_loc(i)
                ser[i] = 'float64'
            else:pass
        else:pass
        try:
            oridf[i] = oridf[i].astype(ser[i])
        except:pass
    return oridf


def Objectprocess(goodser, badser,totalser):
    goodOValue = goodser.value_counts()
    badOValue = badser.value_counts()
    totalOvalue = totalser.value_counts()
    badtmp = goodOValue.copy()
    goodtmp = badOValue.copy()
    badtmp[(totalOvalue - badOValue).notnull()] = badOValue+1
    badtmp[(totalOvalue - badOValue).isnull()] = 1
    goodtmp[(totalOvalue - goodOValue).notnull()] = goodOValue+1
    goodtmp[(totalOvalue - goodOValue).isnull()] = 1

    goodtmp = goodtmp.sort_index()
    badtmp = badtmp.sort_index()

    IV_Objekt = IVCAL(goodtmp,badtmp)
    return IV_Objekt


def NUMprocess(goodser, badser, totalser,bin):
    totalcuts = pd.cut(totalser, bin, right = True, include_lowest = True)
    goodcuts = pd.cut(goodser, bin, right = True, include_lowest = True)
    badcuts = pd.cut(badser, bin, right = True, include_lowest = True)

    ####### do statistics
    totalsum = totalcuts.value_counts()
    goodsum = goodcuts.value_counts()
    badsum = badcuts.value_counts()

    totalsum = totalsum.sort_index() # sort the index
    goodsum = goodsum.sort_index()# sort the index
    badsum = badsum.sort_index()# sort the index
    badsum[(totalsum==0) != (badsum == 0)] = 1
    goodsum[(totalsum==0) != (goodsum == 0)] = 1

    IV_NUM = IVCAL(goodsum,badsum)
    return IV_NUM


#def replaceObject():


def IVFunc(Aframe, k):
    if -1 in Aframe:
        print 'wow!'
    lst = []
    final_IV = 0
    count = 0
    dicretcount = 0
    newFrame = Aframe.set_index('Idx')
    goodN = newFrame.groupby('target').get_group(1)
    badN = newFrame.groupby('target').get_group(0)

    dropgroup = []
    for clm in newFrame.columns:
        if len(newFrame[clm].dropna())<30000*0.8:
            #print 'column need to be deleted ',clm,newFrame.columns.get_loc(clm)
            del newFrame[clm]
            continue
        else:
            #oricount = newFrame[clm].count() #total count without NaN
            #totalTypes = len(newFrame[clm].value_counts())
            ###### Handling the Categories ######
            if newFrame[clm].dtypes =='object':
                #print 'oblect',clm, newFrame.columns.get_loc(clm)
                final_IV = Objectprocess(goodN[clm],badN[clm],newFrame[clm])
                if final_IV >1:
                    count+=1
                    print 'BUG'
                    continue
            ######## numerical#######
            else:
                ####### Discretization
                Maxmum = float(newFrame[clm].max())
                Minmum = float(newFrame[clm].min())
                dist = float((Maxmum - Minmum)/k)
                #print Maxmum, Minmum
                if Maxmum < 100:
                    final_IV = Objectprocess(goodN[clm],badN[clm],newFrame[clm])
                    dicretcount+=1
                    print 'discret: ', final_IV
                    #print 'depends: ', clm, newFrame.columns.get_loc(clm)
                else:
                    if dist == 0:
                        #print 'column need to be deleted ',clm,newFrame.columns.get_loc(clm)
                        dropgroup.append(newFrame[clm])
                        #count +=1
                        del newFrame[clm]
                        continue
                    bins =[]
                    for i in range(0,k+1):
                        start = Minmum + i*dist
                        bins.append(start)
                    final_IV = NUMprocess(goodN[clm],badN[clm],newFrame[clm],bins)
                    if final_IV >1:
                        count+=1
                        #print final_IV
                        continue
                    elif final_IV >0.1:
                        pass

            lst.append(final_IV)
    print dicretcount,count
    return lst,newFrame

Master = Master.replace(-1, np.nan)
Master = resetType(TypeStatement,Master)
IV,DF = IVFunc(Master,20)
#print DF
print IV
print len(DF.columns)
'''for element in IV:
    if element > 1:
        print element'''
