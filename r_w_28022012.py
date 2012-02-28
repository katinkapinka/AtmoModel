#! /usr/bin/python
# -*- coding: utf-8 -*-
# version 19012012
# version 27022012 introduced Brenguiers adiabatic lapse rate
# version 28022012 outfile looking good...
# TODO: wrap up single operations in calculate_clw() into own functions 
'''
Created on Jan 10, 2012

@author: katinkapinka

Script to read and write an atmospheric profile in specific MonoRTM (Fortran90)
format and to insert a cloud into specific layers with specific liquid water content (clw)
by giving liquid water path and cloud boundaries.
Atmospheric parameters are read in and stored in lists as global variables for calculation
of an adiabatic distribution of the integrated liquid water path within the cloud.

MonoRTM is a radiative transfer model for processing monochromatic wavenumber values,
particularly in the microwave spectral region. The model was developed and is maintained and 
updated by AER (Atmospheric and Evironmental Research) Radiation and Climate Group, USA.
'''

import sys
import fortranformat as ff
import numpy as np


def read_and_store():
    ''' Read in lines from infile and store them in midfile.
    Split up even lines into variables for future calculations'''
    # is a midfile really needed??
     
    i=1
    for line in infile:
        midfile.write(line)
        line=line.rstrip()  # remove whitespace
      
        if i % 2 is 0:
            # print("line " + str(i))      # test  
            # print(line)       
        
            # import pdb            # initiate debugger while working with emacs/console
            # pdb.set_trace()    
           
            var =  ff.FortranRecordReader(lineFormat).read(line)
            
            # print(type(var))             # test
            # print(dir(var))
            # print(var)
            pave.append(float(var[0]))
            tave.append(float(var[1]))
            if var[3] == 0.0:
                altbot.append(alttop[alttop.__len__() - 1])
                # import pdb                # initiate debugger using emacs/console 
                # pdb.set_trace()
            else:
                altbot.append(float(var[3])) 
           
            if var[4] == 0.0:
                pbot.append(ptop[alttop.__len__() - 1])
            else:
                pbot.append(float(var[4]))

            if var[5] == 0.0:    
                tbot.append(ttop[alttop.__len__() - 1])
            else:
                tbot.append(float(var[5]))
            
            alttop.append(float(var[6]))
            ptop.append(float(var[7]))
            ttop.append(float(var[8]))

               
        i = i + 1

    infile.close()
    midfile.close()

def test_values_after_read():
    # print(altbot)
    # print(pbot)
    # print(tbot)
    print("#items: " + str(pave.__len__()))
    
    
def calculate_clw():
    ''' calculate the adiabatic liquid water content (clw)
    for each layer from atmospheric parameteres for a given integrated
    liquid water path (lwp) and cloud boundary altitudes (cldbot, cldtop) '''
    # in progress: maybe split this function up into a few functions
    # remember checking units, because in infile not necessarily SI-conform
    # how to hand over parameters? maybe read out of extra input file? or via console?
    # Brenguier adiabatic lapse rate cw

    # test parameters:
    cldbot = 0.2  # [km]
    cldtop = 0.4  # [km]
    lwp = 50     # [g/m2]
    # ####################

    cloudbase = altbot.index(cldbot) # position of cloud base layer
    cloudtop = alttop.index(cldtop) # postition of cloud top layer   
    # print(str(cloudbase))

    cw = 2 * lwp/(((cldtop - cldbot) * 1000) ** 2) # here LWP in g/m2
    print("  The moist adiabatic condensate coefficient is  " + str(cw))


    adiabaticlwc=[]
    for index, item in enumerate(alttop):  # gives list of adiabatic lwc in g/m3
        
        if index < cloudbase or index > cloudtop + 1: 
            adiabaticlwc.append("") 
        else:
            adiabaticlwc.append((item - cldbot)* 1000 * cw)  
#    print(cloudtest)

    correctedlwc=[]
    for index, item  in enumerate(adiabaticlwc):  # Karstens correction
        if index < cloudbase or index > cloudtop + 1:
            correctedlwc.append("")
        else:
            correctedlwc.append(item * (1.239-0.145*np.log(1000*(alttop[index] - cldbot))))
#    print(cloudcorrected)

    clwlist=[]
    total=sum(correctedlwc[cloudbase:cloudtop+2])  # why "+2" ??
    for index, item in enumerate(correctedlwc):  # converts lwc to lwp in mm!
        if index < cloudbase or index > cloudtop + 1:
            clwlist.append("")
        else:
            clwlist.append(round(item / total * lwp / 1000, 4)) 
#    print(clwlist)
    print("Sum of dicrete corrected LWC in the cloud:  " + str(total))
    print("Test sum for LWP after calculation:  " + str(sum(clwlist[cloudbase:cloudtop+2])))  # python round just cuts of the float and does not round! error in sum!
 
    return clwlist
   

def append_clw():
    ''' append clw to midfile and write to outfile'''
    
    outfile = open("outfile", "w")
    midfile = open("midfile", "r")
    
    counter = 1
    i = iter(calculate_clw())

    for line in midfile:
        
        if counter % 2 is 0:
            # print(" =============")    # test
            value = i.next()              
            outfile.write(line.strip("\n") + " " + str(value) + "\n")            
            
        else:
            # print("_______")           # test 
            outfile.write(line)            
            
        counter = counter + 1


    midfile.close()
    outfile.close()
    print("files closed")

# ################################################
# Invoke MAIN module
# ################################################

if __name__ == '__main__':

    print("reading args..")
    i = 1
    for arg in sys.argv: 
        print(str(i) + arg)
        i = i + 1
    
    try:
        # read filename argument
        infilename = sys.argv[1]
    except IndexError:
        #    print("got an index error: " + e)
        print("You need to specify an infile on the command line")    
        infilename = raw_input("filename: ")

        # TODO: catch IOError...

    # try:
    infile = open(infilename, "r")
    outfile = open("outfile", "w")    
    midfile = open("midfile", "w")    
    # except NameError:
    
    # ###############################################
    # define variables:
    # for layers L >= 2 values for bottom of layer must 
    # be collected from values for top of layer L-1
    pave=[]        # average pressure of current layer [hPa]
    tave=[]        # average temperature of current layer [K]
    altbot=[]    # altitude for bottom of current layer [km]
    alttop=[]    # altitude for top of current layer [km]
    pbot=[]        # pressure at altbot [hPa]
    tbot=[]        # temperature at altbot [K]
    ptop=[]        # pressure at alttop [hPa]
    ttop=[]        # temperature at alttop [K]
    # own parameters:
    lwp=[]        # integrated liquid water path [gm^-2]
    cldbot=[]    # altitude of cloud bottom [km]
    cldtop=[]    # altitude of cloud top [km]
    # to be calculated:
    # clw=[]        # cloud liquid water per layer [gm^-3]
    # ###############################################

    lineFormat = "1X, F10.4, F14.2, 14X, I2, F8.3, F8.3, F7.2, F7.3, F8.3, F7.2"
    targetFormat = "1X, F10.4, F14.2, 14X, I2, F8.3, F8.3, F7.2, F7.3, F8.3, F7.2"

    # call functions:
    read_and_store()
    test_values_after_read()
    calculate_clw()
    append_clw()

    print("done reading args.    ")
    
    print("all done!")



