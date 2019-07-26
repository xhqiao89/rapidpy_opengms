#### This is the encapsulation script to connect the model entry function with the .mdl file
# Basically it reads in inputs, executes the service, and returns the results

from .modelservicecontext import EModelContextStatus
from .modelservicecontext import ERequestResponseDataFlag
from .modelservicecontext import ERequestResponseDataMIME
from .modelservicecontext import ModelServiceContext
from .modeldatahandler import ModelDataHandler
from .inflow.lsm_rapid_process import run_lsm_rapid_process

import sys
import os

# Begin
if len(sys.argv) < 4:
    exit()

ms = ModelServiceContext()
ms.onInitialize(sys.argv[1], sys.argv[2], sys.argv[3])
mdh = ModelDataHandler(ms)

# State - mainProcess
ms.onEnterState('mainProcess')

#### Model inputs
# Event - rapid_io_files_location
ms.onFireEvent('rapid_io_files')

ms.onRequestData()

rapid_io_files = None
if ms.getRequestDataFlag() == ERequestResponseDataFlag.ERDF_OK:
    if ms.getRequestDataMIME() == ERequestResponseDataMIME.ERDM_RAW_FILE:
        rapid_io_files = ms.getRequestDataBody()
    if ms.getRequestDataMIME() == ERequestResponseDataMIME.ERDM_ZIP_FILE:
        rapid_io_files = ms.getRequestDataBody()
        ms.mapZipToCurrentDataDirectory(rapid_io_files)
        rapid_io_files = ms.getDataFileByExt('tif')[0]
        #get current data directory
        event_folder= ms.getCurrentDataDirectory()

        rapid_io_files_path = os.path.join(event_folder, 'input')
else:
    ms.onFinalize()

# Event - lsm_data_location
ms.onFireEvent('lsm_data')

ms.onRequestData()

lsm_data = None
if ms.getRequestDataFlag() == ERequestResponseDataFlag.ERDF_OK:
    if ms.getRequestDataMIME() == ERequestResponseDataMIME.ERDM_RAW_FILE:
        lsm_data = ms.getRequestDataBody()
    if ms.getRequestDataMIME() == ERequestResponseDataMIME.ERDM_ZIP_FILE:
        lsm_data = ms.getRequestDataBody()
        ms.mapZipToCurrentDataDirectory(rapid_io_files)
        lsm_data = ms.getDataFileByExt('tif')[0]
        lsm_data_path = os.path.join(event_folder, 'data')
else:
    ms.onFinalize()

# Event - streamflow
ms.onFireEvent('streamflow')

ms.setResponseDataFlag(ERequestResponseDataFlag.ERDF_OK)

ms.setResponseDataMIME(ERequestResponseDataMIME.ERDM_RAW_FILE)

dir_data = os.path.join(event_folder,'output')

run_lsm_rapid_process(rapid_executable_location='/home/sherry/rapid/run/rapid', rapid_io_files_location=rapid_io_files_path, lsm_data_location=lsm_data_path,rapid_output_location=dir_data, use_all_processors=False,num_processors=1)

#### find the Qout nc file from the results folder and move it to *dir_data* directory

for file in os.listdir(dir_data):
    if file.startswith("Qout"):
        Qout_file = os.path.join(dir_data, file)

ms.setResponseDataBody(Qout_file)

ms.onResponseData()

ms.onLeaveState()

print('Start to finalize!')

ms.onFinalize()