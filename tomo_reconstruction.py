# 
#   This file is part of Mantis, a Multivariate ANalysis Tool for Spectromicroscopy.
# 
#   Copyright (C) 2015 Mirna Lerotic, 2nd Look
#   http://2ndlookconsulting.com
#   License: GNU GPL v3
#
#   Mantis is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   any later version.
#
#   Mantis is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details <http://www.gnu.org/licenses/>.

from __future__ import division

import os
import numpy as np
import scipy as sp
from time import time


import warnings
warnings.simplefilter('ignore', DeprecationWarning)

from TomoCS.forward_backward_tv import fista_tv,gfb_tv
from TomoCS.projections import build_projection_operator
from TomoCS.util import generate_synthetic_data

import Mrc
        
#----------------------------------------------------------------------
def write_mrc(stack, mrcfn):
    
    stackf32 = stack.astype(np.float32)
    Mrc.save(stackf32, mrcfn,ifExists='overwrite',calcMMM=False)


#----------------------------------------------------------------------
class Ctomo:
    def __init__(self, stkdata):

        self.stack = stkdata
        
        self.tomorec = []
        
        
        
#----------------------------------------------------------------------   
# Calculate tomo - CS reconstruction for 1 dataset 
    def calc_tomo1(self, tomodata, theta, maxiter, beta, samplethickness):
        

        print 'Compressed sensing TV regression'
        #print 'Angles ', theta
        print 'TV beta ', beta
        print 'MAX iterations ', maxiter
        print "Sample thickness ", samplethickness
        
        #Check if we have negative angles, if yes convert to 0-360deg
        for i in range(len(theta)):
            if theta[i] < 0:
                theta[i] = theta[i] + 360
        #print 'Angles in 0-360 range: ', theta
                      
        nang = len(theta)
        #print 'Number of angles ', nang
                
        dims = tomodata.shape
        #print 'Dimensions ', dims, tomodata.dtype        
    
        stack = np.swapaxes(tomodata, 0, 1)


        theta = np.deg2rad(theta)
        
        dims = stack.shape
        ncols = dims[0]
        nrows = dims[1]
    

        recondata = []
        
        initx0 = np.zeros((nrows,nrows), dtype=np.float32)
        
        t1 = time()
        
        for j in range(ncols):
            #print j, ' of ', ncols
        #             for j in range(1):
            #j=ncols/2
            R = stack[j,:, :].T

 
            Rmax = np.amax(R)
            Rmin = np.amin(R)
         
            R = (R-Rmin)/(Rmax-Rmin)

#             pl.imshow(R, cmap=pl.cm.Greys_r)
#             pl.show()
                           
            proj = R.ravel()[:, np.newaxis]
            l = dims[1]
            proj_operator = build_projection_operator(l, n_dir=len(theta), angles=theta)
        
            
            # Reconstruction
            
            #res, energies = fista_tv(proj, 5, 100, proj_operator) 
            res, engs = gfb_tv(proj, beta, maxiter, H=proj_operator, x0=initx0)

    
        
            recondata.append(res[-1])
            initx0 = res[-1]
            
        t2 = time()
        print "reconstruction done in %f s" %(t2 - t1)                
                
        #Save the 3D tomo reconstruction to a HDF5 file
        recondata=np.array(recondata)
        dims = recondata.shape
        #print 'final dims', dims
        
        #Crop the data is sample thickness is defined
        if (samplethickness > 0) and (samplethickness<dims[2]-2):
            recondata = recondata[:,:,dims[2]/2-samplethickness/2:dims[2]/2+samplethickness/2]
               
        
        recondata = np.swapaxes(recondata, 0, 1)
        
        self.tomorec = recondata
        

#         write_mrc(recondata, 'testMantistomo.mrc')
        
        return
    

        
#----------------------------------------------------------------------   
# Save mrc
    def save_mrc(self, path, data):    
        
        write_mrc(data, path)

        