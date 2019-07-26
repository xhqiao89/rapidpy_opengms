#Data : 2018-10-15
#Author : Fengyuan Zhang (Franklin)
#Email : franklinzhang@foxmail.com

from enum import Enum
import socket
import time
import threading
import json
import os
import sys
import zipfile

class EModelContextStatus(Enum):
    EMCS_INIT_BEGIN = 1,
    EMCS_INIT = 2,
    EMCS_INIT_END = 3,

    EMCS_STATE_ENTER_BEGIN = 4,
    EMCS_STATE_ENTER = 5,
    EMCS_STATE_ENTER_END = 6,

    EMCS_EVENT_BEGIN = 7,
    EMCS_EVENT = 8,
    EMCS_EVENT_END = 9,

    EMCS_REQUEST_BEGIN = 10,
    EMCS_REQUEST = 11,
    EMCS_REQUEST_END = 12,

    EMCS_RESPONSE_BEGIN = 13,
    EMCS_RESPONSE = 14,
    EMCS_RESPONSE_END = 15,

    EMCS_POST_BEGIN = 16,
    EMCS_POST = 17,
    EMCS_POST_END = 18,

    EMCS_STATE_LEAVE_BEGIN = 19,
    EMCS_STATE_LEAVE = 20,
    EMCS_STATE_LEAVE_END = 21,

    EMCS_FINALIZE_BEGIN = 22,
    EMCS_FINALIZE = 23,
    EMCS_FINALIZE_END = 24,

    EMCS_COMMON_BEGIN = 25,
    EMCS_COMMON_REQUEST = 26,
    EMCS_COMMON_END = 27,

    EMCS_INIT_CTRLPARAM_BEGIN = 28,
    EMCS_INIT_CTRLPARAM = 29,
    EMCS_INIT_CTRLPARAM_END = 30,

    EMCS_UNKOWN = 0

class ERequestResponseDataFlag(Enum):
    ERDF_OK = 1,
    ERDF_NOTREADY = 2,
    ERDF_ERROR = -1,
    ERDF_UNKNOWN = 0

class ERequestResponseDataMIME(Enum):
    ERDM_XML_STREAM = 1,
    ERDM_ZIP_STREAM = 2
    ERDM_RAW_STREAM = 3,
    ERDM_XML_FILE = 4,
    ERDM_ZIP_FILE = 5,
    ERDM_RAW_FILE = 6,
    ERDM_UNKNOWN = 0

class ModelServiceContext:
    def __init__(self):
        self.mPort = 6000
        self.mHost = '127.0.0.1'
        self.mInstanceID = ''
        self.mClientSocket = None
        self.mMornitoringThread = None
        self.mDebugScriptFile = ''
        self.mStatus = EModelContextStatus.EMCS_UNKOWN
        self.mData = ''
        self.mMappingLibDir = ''
        self.mInstanceDir = ''
        self.mCurrentState = ''
        self.mCurrentEvent = ''
        self.mRequestDataFlag = ERequestResponseDataFlag.ERDF_UNKNOWN
        self.mRequestDataBody = ''
        self.mRequestDataMIME = ERequestResponseDataMIME.ERDM_UNKNOWN
        
        self.mResponseDataFlag = ERequestResponseDataFlag.ERDF_UNKNOWN
        self.mResponseDataBody = ''
        self.mResponseDataMIME = ERequestResponseDataMIME.ERDM_UNKNOWN

        self.mProcessParams = {}
        self.mControlParams = {}

    def _bindSocket(self):
        self.mClientSocket = socket.socket()
        try:
            self.mClientSocket.connect((self.mHost, int(self.mPort)))
        except ZeroDivisionError as ex:
            return -1
        return 1
    
    def _sendMessage(self, message):
        self.mClientSocket.sendall(message)

    def _receiveMessage(self):
        msg = str(self.mClientSocket.recv(10240))
        # print '[MSG]:' + msg
        return msg

    def _wait4Status(self, status, timeout = 72000):
        time_end = time.time() + timeout
        while True:
            time.sleep(0.01)
            if self.mStatus == status or time.time() > time_end :
                return 1

    def _resetRequestDataInfo(self):
        self.mRequestDataBody = ''
        self.mRequestDataFlag = ERequestResponseDataFlag.ERDF_UNKNOWN
        self.mRequestDataMIME = ERequestResponseDataMIME.ERDM_UNKNOWN

    def _resetResponseDataInfo(self):
        self.mRequestDataBody = ''
        self.mRequestDataFlag = ERequestResponseDataFlag.ERDF_UNKNOWN
        self.mRequestDataMIME = ERequestResponseDataMIME.ERDM_UNKNOWN

    def _sendProcessParam(self):
        self._sendMessage('{ProcessParams}' + self.mInstanceID + '&' + json.dumps(self.mProcessParams))

    def onInitialize(self, host, port, instanceID):
        self.mHost = host
        self.mPort = port
        self.mInstanceID = instanceID
        self.mStatus = EModelContextStatus.EMCS_INIT_BEGIN
        if self._bindSocket() == 1:
            # start monitoring thread
            self.mMornitoringThread = threading.Thread(target=ModelServiceContext.Monitoring_thread, name='Monitoring', args=(self,))
            self.mStatus = EModelContextStatus.EMCS_INIT
            if self.mMornitoringThread == None:
                print('error in create thread!')
                return exit()
            self.mMornitoringThread.start()
            self._sendMessage('{init}' + self.mInstanceID + '&' + self.mDebugScriptFile)
            self._wait4Status(EModelContextStatus.EMCS_INIT_END)
            startPos = self.mData.index('[')
            endPos = self.mData.index(']')
            self.mMappingLibDir = self.mData[startPos + 1 : endPos]
            self.mData = self.mData[endPos + 1 : ]
            startPos = self.mData.index('[')
            endPos = self.mData.index(']')
            self.mInstanceDir = self.mData[startPos + 1 : endPos]
        else:
            print('Init Failed! Cannot Connect Model Service Container')
            return exit()
    
    def onEnterState(self, stateId):
        self.mStatus = EModelContextStatus.EMCS_STATE_ENTER_BEGIN
        self.mCurrentState = stateId
        self._sendMessage('{onEnterState}' + self.mInstanceID + '&' + stateId)
        self.mStatus = EModelContextStatus.EMCS_STATE_ENTER
        self._wait4Status(EModelContextStatus.EMCS_STATE_ENTER_END)
        return 0

    def onFireEvent(self, eventName):
        self.mStatus = EModelContextStatus.EMCS_EVENT_BEGIN
        self.mCurrentEvent = eventName
        self._sendMessage('{onFireEvent}' + self.mInstanceID + "&" + self.mCurrentState + "&" + eventName)
        self.mStatus = EModelContextStatus.EMCS_EVENT
        self._wait4Status(EModelContextStatus.EMCS_EVENT_END)
        
    def onRequestData(self):
        self._resetRequestDataInfo()
        if self.mCurrentState == '' or self.mCurrentEvent == '':
            return -1
        self._resetRequestDataInfo()
        self.mStatus = EModelContextStatus.EMCS_REQUEST_BEGIN
        self._sendMessage('{onRequestData}' + self.mInstanceID + '&' + self.mCurrentState + '&' + self.mCurrentEvent)
        self._wait4Status(EModelContextStatus.EMCS_REQUEST_END)
        
        posBegin = self.mData.index('[')
        posEnd = self.mData.index(']')
        dataFlag = self.mData[posBegin + 1 : posEnd - posBegin]
        dataRemained = self.mData[posEnd + 1 : ]

        if dataFlag == 'OK':
            self.mRequestDataFlag = ERequestResponseDataFlag.ERDF_OK
        else:
            self.mRequestDataFlag = ERequestResponseDataFlag.ERDF_ERROR
            self.mRequestDataMIME = ERequestResponseDataMIME.ERDM_UNKNOWN
            return 0
        
        posBegin = dataRemained.index('[')
        posEnd = dataRemained.index(']')
        dataMIME = dataRemained[posBegin + 1 : posEnd - posBegin]

        if dataMIME == 'XML|STREAM':
            self.mRequestDataMIME = ERequestResponseDataMIME.ERDM_XML_STREAM
        elif dataMIME == 'ZIP|STREAM':
            self.mRequestDataMIME = ERequestResponseDataMIME.ERDM_ZIP_STREAM
        elif dataMIME == 'RAW|STREAM':
            self.mRequestDataMIME = ERequestResponseDataMIME.ERDM_RAW_STREAM
        elif dataMIME == 'XML|FILE':
            self.mRequestDataMIME = ERequestResponseDataMIME.ERDM_XML_FILE
        elif dataMIME == 'ZIP|FILE':
            self.mRequestDataMIME = ERequestResponseDataMIME.ERDM_ZIP_FILE
        elif dataMIME == 'RAW|FILE':
            self.mRequestDataMIME = ERequestResponseDataMIME.ERDM_RAW_FILE
        else:
            self.mRequestDataMIME = ERequestResponseDataMIME.ERDM_UNKNOWN

        self.mRequestDataBody = dataRemained[posEnd + 1 : ]

    def onResponseData(self):
        self.mStatus = EModelContextStatus.EMCS_RESPONSE_BEGIN
        if self.mResponseDataFlag == ERequestResponseDataFlag.ERDF_OK:
            mime = ''
            if self.mResponseDataMIME == ERequestResponseDataMIME.ERDM_XML_STREAM:
                mime = '[XML|STREAM]'
            elif self.mResponseDataMIME == ERequestResponseDataMIME.ERDM_ZIP_STREAM:
                mime = '[ZIP|STREAM]'
            elif self.mResponseDataMIME == ERequestResponseDataMIME.ERDM_RAW_STREAM:
                mime = '[RAW|STREAM]'
            elif self.mResponseDataMIME == ERequestResponseDataMIME.ERDM_XML_FILE:
                mime = '[XML|FILE]'
            elif self.mResponseDataMIME == ERequestResponseDataMIME.ERDM_ZIP_FILE:
                mime = '[ZIP|FILE]'
            elif self.mResponseDataMIME == ERequestResponseDataMIME.ERDM_RAW_FILE:
                mime = '[RAW|FILE]'
            else:
                mime = '[UNKNOWN]'
            
            self._sendMessage('{onResponseData}' + self.mInstanceID + '&' + self.mCurrentState + '&' + self.mCurrentEvent + '&' + str(len(self.mResponseDataBody)) + '[OK]' + mime + self.mResponseDataBody )
            self.mStatus = EModelContextStatus.EMCS_RESPONSE

            self._wait4Status(EModelContextStatus.EMCS_RESPONSE_END)
        elif self.mResponseDataFlag == ERequestResponseDataFlag.ERDF_ERROR:
            self._sendMessage('{onResponseData}' + self.mInstanceID + '&' + self.mCurrentState + '&' + self.mCurrentEvent + '&0[ERROR]' )
            self.mStatus = EModelContextStatus.EMCS_RESPONSE
            self._wait4Status(EModelContextStatus.EMCS_RESPONSE_END)
        elif self.mResponseDataFlag == ERequestResponseDataFlag.ERDF_NOTREADY:
            self._sendMessage('{onResponseData}' + self.mInstanceID + '&' + self.mCurrentState + '&' + self.mCurrentEvent + '&' + len(self.mResponseDataBody))
            self.mStatus = EModelContextStatus.EMCS_RESPONSE
            self._wait4Status(EModelContextStatus.EMCS_RESPONSE_END)
        
        self._resetResponseDataInfo()

    def onPostErrorInfo(self, errinfo):
        self.mStatus = EModelContextStatus.EMCS_POST_BEGIN
        self._sendMessage('{onPostErrorInfo}' + self.mInstanceID + '&' + errinfo)
        self.mStatus = EModelContextStatus.EMCS_POST
        self._wait4Status(EModelContextStatus.EMCS_POST_END)

    def onPostWarningInfo(self, warninginfo):
        self.mStatus = EModelContextStatus.EMCS_POST_BEGIN
        self._sendMessage('{onPostMessageInfo}' + self.mInstanceID + '&' + warninginfo)
        self.mStatus = EModelContextStatus.EMCS_POST
        self._wait4Status(EModelContextStatus.EMCS_POST_END)

    def onPostMessageInfo(self, messageinfo):
        self.mStatus = EModelContextStatus.EMCS_POST_BEGIN
        self._sendMessage('{onPostMessageInfo}' + self.mInstanceID + '&' + messageinfo)
        self.mStatus = EModelContextStatus.EMCS_POST
        self._wait4Status(EModelContextStatus.EMCS_POST_END)

    def onLeaveState(self):
        self.mStatus = EModelContextStatus.EMCS_STATE_LEAVE_BEGIN
        self._sendMessage('{onLeaveState}' + self.mInstanceID + '&' + self.mCurrentState)
        self.mStatus = EModelContextStatus.EMCS_STATE_LEAVE
        self._wait4Status(EModelContextStatus.EMCS_STATE_LEAVE_END)
    
    def onFinalize(self):
        self.mStatus = EModelContextStatus.EMCS_FINALIZE_BEGIN
        self._sendMessage('{onFinalize}' + self.mInstanceID)
        self.mStatus = EModelContextStatus.EMCS_FINALIZE
        self._wait4Status(EModelContextStatus.EMCS_FINALIZE_END)
        # self.mMornitoringThread.join()
        sys.exit()

    def onGetModelAssembly(self, methodName):
        self.mStatus = EModelContextStatus.EMCS_COMMON_BEGIN
        self._sendMessage('{onGetModelAssembly}' + self.mInstanceID + '&' + methodName)
        self.mStatus = EModelContextStatus.EMCS_COMMON_REQUEST
        self._wait4Status(EModelContextStatus.EMCS_COMMON_END)
        assembly = self.mData[0 : self.mData.index('}') + 1]
        return assembly

    def initControlParam(self):
        self.mStatus = EModelContextStatus.EMCS_INIT_CTRLPARAM_BEGIN
        self._sendMessage('{onInitControlParam}' + self.mInstanceID)
        self.mStatus = EModelContextStatus.EMCS_INIT_CTRLPARAM
        self._wait4Status(EModelContextStatus.EMCS_INIT_CTRLPARAM_END)
        
        posEnd = self.mData.index('&')
        controlParamBuffer = self.mData[posEnd + 1 : ]

        try:
            self.mControlParams = json.loads(controlParamBuffer)
        except ZeroDivisionError as ex:
            pass

    #Data 
    def getRequestDataFlag(self):
        return self.mRequestDataFlag

    def getRequestDataMIME(self):
        return self.mRequestDataMIME

    def getRequestDataBody(self):
        return self.mRequestDataBody

    def setResponseDataFlag(self, flag):
        self.mResponseDataFlag = flag

    def setResponseDataMIME(self, MIME):
        self.mResponseDataMIME = MIME

    def setResponseDataBody(self, body):
        self.mResponseDataBody = body

    def getResponseDataFlag(self):
        return self.mResponseDataFlag

    def getResponseDataMIME(self):
        return self.mResponseDataMIME

    def getResponseDataDody(self):
        return self.mResponseDataBody

    def getCurrentStatus(self):
        return self.mStatus

    def getProcessParam(self, key):
        return self.mProcessParams.get(key, None)

    def setProcessParam(self, key, value):
        self.mProcessParams[key] = value
        self._sendProcessParam()

    # Directory
    def getCurrentDataDirectory(self):
        instanceDir = self.getModelInstanceDirectory()
        if os.path.exists(instanceDir) == False:
            os.makedirs(instanceDir) 
        stateDir = instanceDir + self.getCurrentRunningState() + '\\'
        if os.path.exists(stateDir) == False:
            os.makedirs(stateDir) 
        eventDir = stateDir + self.getCurrentRunningEvent() + '\\'
        if os.path.exists(eventDir) == False:
            os.makedirs(eventDir)
        return eventDir

    def getMappingLibraryDirectory(self):
        if self.mMappingLibDir[:-1] != '\\':
            self.mMappingLibDir = self.mMappingLibDir + '\\'
        return self.mMappingLibDir

    def getModelInstanceDirectory(self):
        if self.mInstanceDir[:-1] != '\\':
            self.mInstanceDir = self.mInstanceDir + '\\'
        return self.mInstanceDir

    def getCurrentRunningState(self):
        return self.mCurrentState
        
    def getCurrentRunningEvent(self):
        return self.mCurrentEvent

    def getDataFileByExt(self, ext):
        ext = ext.lower()
        dire = self.getCurrentDataDirectory()
        list_files = os.listdir(dire)
        list_f = []
        for filepath in list_files:
            if ext == ModelServiceContext.getFileExtension(filepath).lower():
                list_f.append(dire + filepath)
        return list_f

    def mapZipToCurrentDataDirectory(self, zipf):
        z = zipfile.ZipFile(zipf, 'r')
        dire = self.getCurrentDataDirectory()
        z.extractall(path=dire)
        z.close()

    @staticmethod
    def getFileExtension(path):
        return os.path.splitext(path)[1][1:]

    @staticmethod
    def Monitoring_thread(ms):
        while True:
            data = ms._receiveMessage()
            strCmds = data.split('\n')
            for cmd in strCmds:
                header = cmd[0 : cmd.index('}') + 1]
                ms.mData = cmd[cmd.index('}') + 1 : ]
                if header == '{Initialized}':
                    ms.mStatus = EModelContextStatus.EMCS_INIT_END
                elif header == '{Enter State Notified}':
                    ms.mStatus = EModelContextStatus.EMCS_STATE_ENTER_END
                elif header == '{Fire Event Notified}':
                    ms.mStatus = EModelContextStatus.EMCS_EVENT_END
                elif header == '{Request Data Notified}':
                    ms.mStatus = EModelContextStatus.EMCS_REQUEST_END
                elif header == '{Response Data Notified}':
                    ms.mStatus = EModelContextStatus.EMCS_RESPONSE_END
                elif header == '{Response Data Received}':
                    ms.mStatus = EModelContextStatus.EMCS_RESPONSE_END
                elif header == '{Post Error Info Notified}':
                    ms.mStatus = EModelContextStatus.EMCS_POST_END
                elif header == '{Post Warning Info Notified}':
                    ms.mStatus = EModelContextStatus.EMCS_POST_END
                elif header == '{Post Message Info Notified}':
                    ms.mStatus = EModelContextStatus.EMCS_POST_END
                elif header == '{Leave State Notified}':
                    ms.mStatus = EModelContextStatus.EMCS_STATE_LEAVE_END
                elif header == '{Finalize Notified}':
                    ms.mStatus = EModelContextStatus.EMCS_FINALIZE_END
                    return
                elif header == '{GetModelAssembly Notified}':
                    ms.mStatus = EModelContextStatus.EMCS_COMMON_END
                elif header == '{SetControlParams Notified}':
                    #TODO Control Parameter
                    pass
                elif header == '{kill}':
                    return sys.exit()
                else :
                    print('Unknown Command!')
                    pass
    