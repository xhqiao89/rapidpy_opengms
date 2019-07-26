#Data : 2018-10-15
#Author : Fengyuan Zhang (Franklin)
#Email : franklinzhang@foxmail.com

class ModelDataHandler:
    def __init__(self, context):
        self.mContext = context

        self.mExecutionPath = ''
        self.mZipExecutionPath = ''
        self.mExecutionName = ''

        self.mSavePath = ''
        self.mSaveName = ''

        self.mReturnFileFullName = ''
        
    def connectDataMappingMethod(self, execName):
        self.mExecutionName = execName
        self.mZipExecutionPath = self.mContext.getMappingLibrary()
        if self.mZipExecutionPath[ : -1] != '\\':
            self.mZipExecutionPath = self.mZipExecutionPath + '\\'
        self.mExecutionPath = self.mContext.onGetModelAssembly(execName)
        # self.mContext.onPostMessageInfo(execName)
        if self.mExecutionPath[ : -1] != '\\':
            self.mExecutionPath = self.mExecutionPath + '\\'
        
        self.mSaveName = ''
        self.mSavePath = ''
        self.mReturnFileFullName = ''

    def configureWorkingDirection(self, savePath):
        if savePath == '':
            self.mSavePath = self.mContext.getModelInstanceDirectory()
        else :
            self.mSavePath = savePath
        if self.mSavePath[ : -1] != '\\':
            self.mSavePath = self.mSavePath + '\\'

    def conductUDXMapping(self, resultSaveName):
        pass

    def conductFileMapping(self, list_rawFiles):
        pass

    def getRealResultSaveName(self):
        pass

    def doRequestEvent_MappingData(self, resultSaveName, name, value, type):
        pass
