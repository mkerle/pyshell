
from cmd import Cmd

class PyShell(Cmd):

    FIELD_DEFINITIONS = 'definitions'
    
    FIELD_HELP = 'help'

    FIELD_COMMAND_NAME = 'cmd-name'
    FIELD_COMMAND_TYPE = 'cmd-type'    
    FIELD_COMMAND_CHILDEREN = 'cmd-childeren'
    FIELD_ON_EXECUTE = 'on-execute'
    FIELD_SOURCE_TYPE = 'source-type'
    FIELD_SOURCE = 'source'
    FIELD_VAR_NAME = 'var-name'

    COMMAND_TYPE_STATIC = 'static'
    COMMAND_TYPE_DYANMIC_SOURCE = 'dynamic-source'
    COMMAND_TYPE_USER_INPUT = 'user-input'

    COMMAND_SOURCE_TYPE_FUNCTION = 'function'
    COMMAND_SOURCE_TYPE_LITERAL = 'literal'

    def __init__(self, definition : dict = None, completekey='tab', stdin=None, stdout=None):

        super().__init__(completekey=completekey, stdin=stdin, stdout=stdout)
        
        self.definition = self.parseDefinition(definition)
        

    def get_names(self):
        '''
        Override base class get_names so that we can dynamiclly add methods at 
        runtime and be compatible with base class functionality.
        '''
        return dir(self)

    def parseDefinition(self, definition : dict) -> dict:

        if (definition is None):
            return None
        elif (type(definition) is not dict):
            raise Exception('Invalid type for command definition object.  Expected dict type.')
        
        self.definition = definition

        if (self.FIELD_DEFINITIONS in definition):
            for childDefinition in self.getDefinitionRoot():
                if (self.getCommandDefinitionType(childDefinition) == self.COMMAND_TYPE_STATIC):
                    cmdName = self.getCommandName(childDefinition)
                    if (cmdName is None):
                        raise Exception('definition object for static command does not define a %s' % (self.FIELD_COMMAND_NAME))
                    
                    doFuncName = 'do_' + cmdName
                    completeFuncName = 'complete_' + cmdName                    

                    if (getattr(self, doFuncName, None) is None):
                        setattr(self, doFuncName, lambda arg: self.doCommandDefinition(cmdName + ' ' + arg))

                    if (getattr(self, completeFuncName, None) is None):
                        setattr(self, completeFuncName, self.completeCommandDefinition)
                    
            return definition
        
        raise Exception('definition object does not contain field: %s' % (self.FIELD_DEFINITIONS))
    
    def getDefinitionRoot(self) -> list:

        return self.definition[self.FIELD_DEFINITIONS]
    
    def getCommandDefinitionType(self, localDefinition : dict) -> str:

        if (self.FIELD_COMMAND_TYPE in localDefinition):
            return localDefinition[self.FIELD_COMMAND_TYPE]
        
        return None
    
    def getCommandName(self, localDefinition : dict) -> str:

        if (self.FIELD_COMMAND_NAME in localDefinition):
            return localDefinition[self.FIELD_COMMAND_NAME]
        
        return None
        
    def getDynamicSourceType(self, localDefinition : dict) -> str:

        if (self.FIELD_SOURCE_TYPE in localDefinition):
            return localDefinition[self.FIELD_SOURCE_TYPE]
        
        return None
    
    def getDynamicSource(self, localDefinition : dict) -> str:

        if (self.FIELD_SOURCE in localDefinition):
            return localDefinition[self.FIELD_SOURCE]
        
        return None
        
    def getDynamicSourceData(self, localDefinition) -> list[str]:
        
        if (self.getDynamicSourceType(localDefinition) == self.COMMAND_SOURCE_TYPE_FUNCTION):
            funcName = self.getDynamicSource(localDefinition)
            if (getattr(self, funcName, None) is None):
                raise Exception('Dyanmic source function not found on PyShell instance: %s' % (funcName))
            else:
                func = eval('self.' + funcName)
                return func()
        
        elif (self.getDynamicSourceType(localDefinition) == self.COMMAND_SOURCE_TYPE_LITERAL):
            return self.getDynamicSource(localDefinition)
        
        else:
            raise Exception('command definition with dynamic source has unknown source type defined: %s' % (self.getDynamicSourceType(localDefinition)))
        
    def getDefinitionFunction(self, localDefinition) -> callable:

        if (self.FIELD_ON_EXECUTE in localDefinition):
            funcName = localDefinition[self.FIELD_ON_EXECUTE]
            if (getattr(self, funcName, None) is None):
                raise Exception('Dyanmic source function not found on PyShell instance: %s' % (funcName))
            
            return eval('self.' + funcName)
        
        return None
        
    def getFunctionVariableName(self, localDefinition) -> str:

        if (self.FIELD_VAR_NAME in localDefinition):
            return localDefinition[self.FIELD_VAR_NAME]
        
        return None
    
    def _parsePartialCommandLine(self, line : str) -> list:

        rawCmdParts = line.split(' ')

        parsedCmdParts = []
        for cmd in rawCmdParts:
            if (len(cmd.strip()) > 0):
                parsedCmdParts.append(cmd.strip())

        return parsedCmdParts
    
    def completeCommandDefinition(self, text : str, line : str, begidx : int, endidx : int) -> list:
        
        partialLine = line
        if (line.endswith(text) and endidx > begidx):
            partialLine = line[:-len(text)]

        cmdParts = self._parsePartialCommandLine(partialLine)

        definitionPath = self.getDefinitionRoot()
        for cmdPart in cmdParts:
            matchedDefinition = None
            for definition in definitionPath:
                if (self.getCommandDefinitionType(definition) == self.COMMAND_TYPE_STATIC):
                    if (cmdPart == definition[self.FIELD_COMMAND_NAME]):
                        matchedDefinition = definition
                        break
                elif (self.getCommandDefinitionType(definition) == self.COMMAND_TYPE_DYANMIC_SOURCE):
                    if (cmdPart in self.getDynamicSourceData(definition)):
                        matchedDefinition = definition
                        break
                elif (self.getCommandDefinitionType(definition) == self.COMMAND_TYPE_USER_INPUT):
                    matchedDefinition = definition
                    break

            if (matchedDefinition is None):
                return []
            else:
                if (self.FIELD_COMMAND_CHILDEREN in matchedDefinition):
                    definitionPath = matchedDefinition[self.FIELD_COMMAND_CHILDEREN]
                else:
                    return []

        matches = []
        if (len(text) > 0):            
            for childDefinition in definitionPath:
                if (self.FIELD_COMMAND_NAME in childDefinition):
                    if (childDefinition[self.FIELD_COMMAND_NAME].startswith(text)):
                        matches.append(childDefinition[self.FIELD_COMMAND_NAME])
                elif (self.getCommandDefinitionType(childDefinition) == self.COMMAND_TYPE_DYANMIC_SOURCE):
                    possibleValues = self.getDynamicSourceData(childDefinition)
                    for possibleValue in possibleValues:
                        if (possibleValue.startswith(text)):
                            matches.append(possibleValue)
        else:            
            for childDefinition in definitionPath:
                if (self.getCommandDefinitionType(childDefinition) == self.COMMAND_TYPE_STATIC):
                    if (self.FIELD_COMMAND_NAME in childDefinition):
                        matches.append(childDefinition[self.FIELD_COMMAND_NAME])
                elif (self.getCommandDefinitionType(childDefinition) == self.COMMAND_TYPE_DYANMIC_SOURCE):
                    matches += self.getDynamicSourceData(childDefinition)

        return matches
    
    def doCommandDefinition(self, arg : str):        

        funcArgs = {}
        func = None

        cmdParts = self._parsePartialCommandLine(arg)

        definitionPath = self.getDefinitionRoot()
        for cmdPart in cmdParts:
            matchedDefinition = None
            for definition in definitionPath:

                if (self.getCommandDefinitionType(definition) == self.COMMAND_TYPE_STATIC):
                    if (cmdPart == definition[self.FIELD_COMMAND_NAME]):
                        if (self.FIELD_ON_EXECUTE in definition):
                            func = self.getDefinitionFunction(definition)
                
                        if (self.FIELD_VAR_NAME in definition):
                            funcArgs[self.getFunctionVariableName(definition)] = cmdPart

                        matchedDefinition = definition
                        break
                elif (self.getCommandDefinitionType(definition) == self.COMMAND_TYPE_DYANMIC_SOURCE):
                    if (cmdPart in self.getDynamicSourceData(definition)):
                        if (self.FIELD_ON_EXECUTE in definition):
                            func = self.getDefinitionFunction(definition)

                        if (self.FIELD_VAR_NAME in definition):
                            funcArgs[self.getFunctionVariableName(definition)] = cmdPart

                        matchedDefinition = definition
                        break
                elif (self.getCommandDefinitionType(definition) == self.COMMAND_TYPE_USER_INPUT):
                    if (self.FIELD_ON_EXECUTE in definition):
                        func = self.getDefinitionFunction(definition)

                    if (self.FIELD_VAR_NAME in definition):
                        funcArgs[self.getFunctionVariableName(definition)] = cmdPart
                        
                    matchedDefinition = definition
                    break

            if (matchedDefinition is None):
                print('ERROR in command: %s' % (cmdPart))
                return
            else:
                if (self.FIELD_COMMAND_CHILDEREN in matchedDefinition):
                    definitionPath = matchedDefinition[self.FIELD_COMMAND_CHILDEREN]

        func(**funcArgs)
    