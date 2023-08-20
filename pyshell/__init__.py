
from cmd import Cmd
import copy
from typing import Union, Tuple

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
    FIELD_HELP_TITLE = 'help-title'
    FIELD_COMMAND_USAGES = 'cmd-usages'

    COMMAND_TYPE_STATIC = 'static'
    COMMAND_TYPE_DYANMIC_SOURCE = 'dynamic-source'
    COMMAND_TYPE_USER_INPUT = 'user-input'

    COMMAND_SOURCE_TYPE_FUNCTION = 'function'
    COMMAND_SOURCE_TYPE_LITERAL = 'literal'

    COMMAND_USAGE_DESCRIPTION = 'description'
    COMMAND_USAGE_EXAMPLE = 'usage'

    def __init__(self, definition : dict = None, completekey='tab', stdin=None, stdout=None):

        super().__init__(completekey=completekey, stdin=stdin, stdout=stdout)
        
        self.definition = self.parseDefinition(definition)
        

    def get_names(self):
        '''
        Override base class get_names so that we can dynamiclly add methods at 
        runtime and be compatible with base class functionality.
        '''
        return dir(self)

    def _merge(self, currentDefinitions : list, newDefinitions : list) -> dict:
        
        mergedDefinitionPointer = None
        for newChildDefinition in newDefinitions:
            foundDefinition = False            
            for currentChildDefinition in currentDefinitions:                
                mergedDefinitionPointer = currentChildDefinition
                newChildDefinitionType = self.getCommandDefinitionType(newChildDefinition)
                if (newChildDefinitionType == self.getCommandDefinitionType(currentChildDefinition)):
                    if (newChildDefinitionType == self.COMMAND_TYPE_STATIC):
                        if (self.getCommandName(newChildDefinition) == self.getCommandName(currentChildDefinition)):
                            foundDefinition = True
                            break
                    elif (newChildDefinitionType == self.COMMAND_TYPE_DYANMIC_SOURCE):
                        newChildDefintionSourceType = self.getDynamicSourceType(newChildDefinition)
                        if (newChildDefintionSourceType == self.getDynamicSourceType(currentChildDefinition)):
                            if (self.getFunctionVariableName(newChildDefinition) == self.getFunctionVariableName(currentChildDefinition)):                                    

                                if (newChildDefintionSourceType == self.COMMAND_SOURCE_TYPE_LITERAL):
                                    mergedDataDynamicSource = self.getDynamicSourceData(mergedDefinitionPointer)
                                    for cmd in self.getDynamicSourceData(newChildDefinition):
                                        if (cmd not in mergedDataDynamicSource):
                                            mergedDataDynamicSource.append(cmd)

                                foundDefinition = True
                                break                                
                    elif (newChildDefinitionType == self.COMMAND_TYPE_USER_INPUT):
                        if (self.getFunctionVariableName(newChildDefinition) == self.getFunctionVariableName(currentChildDefinition)):
                            foundDefinition = True
                            break                

            if (foundDefinition):
                newCommandChilderen = self.getCommandChilderen(newChildDefinition)
                if (newCommandChilderen is not None):
                    currentCommandChilderen = self.getCommandChilderen(currentChildDefinition)
                    if (currentCommandChilderen is not None):
                        mergedDefinitionPointer = self._merge(currentCommandChilderen, newCommandChilderen)
                    else:
                        mergedDefinitionPointer[self.FIELD_COMMAND_CHILDEREN] = copy.deepcopy(newCommandChilderen)
            else:
                currentDefinitions.append(copy.deepcopy(newChildDefinition))

        return currentDefinitions


    def mergeDefinitions(self, definition1, definition2) -> dict:

        mergedDefinition = copy.deepcopy(definition1)
        mergedChilderen = self._getDefinitionRoot(mergedDefinition)

        mergedChilderen = self._merge(mergedChilderen, self._getDefinitionRoot(definition2))

        return mergedDefinition

    def addDefinition(self, newDefinition):

        self.definition = self.mergeDefinitions(self.definition, newDefinition)
        self.parseDefinition(self.definition)

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
                    helpFuncName = 'help_' + cmdName

                    if (getattr(self, doFuncName, None) is None):
                        setattr(self, doFuncName, lambda arg, cmdName=cmdName: self.doCommandDefinition(cmdName, arg))

                    if (getattr(self, completeFuncName, None) is None):
                        setattr(self, completeFuncName, self.completeCommandDefinition)

                    if (getattr(self, helpFuncName, None) is None):
                        setattr(self, helpFuncName, lambda cmdName=cmdName: self.helpCommandDefinition(cmdName))
                    
            return definition
        
        raise Exception('definition object does not contain field: %s' % (self.FIELD_DEFINITIONS))

    def _getDefinitionRoot(self, localDefinition : dict) -> Union[list, None]:

        if (self.FIELD_DEFINITIONS in localDefinition):
            return localDefinition[self.FIELD_DEFINITIONS]

        return None
    
    def getDefinitionRoot(self) -> list:

        return self._getDefinitionRoot(self.definition)
    
    def getCommandDefinitionType(self, localDefinition : dict) -> Union[str, None]:

        if (self.FIELD_COMMAND_TYPE in localDefinition):
            return localDefinition[self.FIELD_COMMAND_TYPE]
        
        return None

    def getCommandChilderen(self, localDefinition : dict) -> Union[list, None]:
        '''
        Checks if localDefinition has child command definitions and returns the 
        list if it exists.  Returns None if no child definitions exist.
        '''
        if (self.FIELD_COMMAND_CHILDEREN in localDefinition):
            return localDefinition[self.FIELD_COMMAND_CHILDEREN]

        return None
    
    def getCommandName(self, localDefinition : dict) -> Union[str, None]:

        if (self.FIELD_COMMAND_NAME in localDefinition):
            return localDefinition[self.FIELD_COMMAND_NAME]
        
        return None
        
    def getDynamicSourceType(self, localDefinition : dict) -> Union[str, None]:

        if (self.FIELD_SOURCE_TYPE in localDefinition):
            return localDefinition[self.FIELD_SOURCE_TYPE]
        
        return None
    
    def getDynamicSource(self, localDefinition : dict) -> Union[str, None]:

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
    
    def getCommandHelpTitle(self, localDefinition) -> str:
        '''
        Checks if the help-title is defined in localDefinition.
        If it is the value is returned otherwise an empty str is returned.
        '''

        if (self.FIELD_HELP_TITLE in localDefinition):
            return localDefinition[self.FIELD_HELP_TITLE]
        
        return ''
    
    def getCommandUsages(self, localDefinition) -> Union[list, None]:
        '''
        Checks if localDefinition has command usage help and returns the 
        list if it exists.  Returns None if no command usages exist.        
        '''

        if (self.FIELD_COMMAND_USAGES in localDefinition):
            return localDefinition[self.FIELD_COMMAND_USAGES]
        
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
    
    def doCommandDefinition(self, cmdName : str, arg : str):        

        funcArgs = {}
        func = None

        cmdParts = self._parsePartialCommandLine(cmdName + ' ' + arg)

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

    def _appendCommandUsageFromDefinition(self, cmdUsage : dict, commandUsages : list) -> list:
        '''
        Takes cmdUsage which is a dict of the form 
        { 'description' : 'This command does blah, 'usage' : 'execute blah' }
        and turns it into a tuple.  Appends it to the commandUsages list and returns
        the update llist.
        '''

        if (self.COMMAND_USAGE_DESCRIPTION in cmdUsage):
            if (self.COMMAND_USAGE_EXAMPLE in cmdUsage):
                usage = (cmdUsage[self.COMMAND_USAGE_DESCRIPTION], cmdUsage[self.COMMAND_USAGE_EXAMPLE])
                commandUsages.append(usage)

            else:
                raise Exception('Command usage does not define %s' % (self.COMMAND_USAGE_EXAMPLE))
            
        else:
            raise Exception('Command usage does not define %s' % (self.COMMAND_USAGE_DESCRIPTION))
        
        return commandUsages
    
    def _appendCommandUsagesFromDefinition(self, newCommandUsages : list, commandUsages : list) -> list:
        '''
        Takes a list of command usage help (newCommandUsages) and appends to commandUsages
        '''
        for newCommandUsage in newCommandUsages:
            commandUsages = self._appendCommandUsageFromDefinition(newCommandUsage, commandUsages)

        return commandUsages


    def _getHelpCommandUsageFromDefinition(self, childDefinitions : list, commandUsages : list) -> list:
        
        for childDefinition in childDefinitions:

            childDefinitions = self.getCommandChilderen(childDefinition)
            if (childDefinitions is not None):
                commandUsages = self._getHelpCommandUsageFromDefinition(childDefinitions, commandUsages)

            usages = self.getCommandUsages(childDefinition)
            if (usages is not None):
                commandUsages = self._appendCommandUsagesFromDefinition(usages, commandUsages)

        return commandUsages
    
    def _displayHelp(self, helpTitle : str, commandUsages : list):

        print('\n\n%s' % (helpTitle))

        if (self.ruler):
            print('%s' % (self.ruler * len(helpTitle)))

        for cmdUsage in commandUsages:
            print('\n%s' % (cmdUsage[0]))
            print('\t%s' % (cmdUsage[1]))

        print()

    def helpCommandDefinition(self, cmdName : str):

        helpTitle = ''
        commandUsages = []
        for childDefinition in self.getDefinitionRoot():
            if (self.getCommandDefinitionType(childDefinition) == self.COMMAND_TYPE_STATIC):
                childDefinitionCmdName = self.getCommandName(childDefinition)

                if (cmdName == childDefinitionCmdName):

                    helpTitle = self.getCommandHelpTitle(childDefinition)

                    childDefinitions = self.getCommandChilderen(childDefinition)
                    if (childDefinitions is not None):
                        commandUsages = self._getHelpCommandUsageFromDefinition(childDefinitions, commandUsages)

                    usages = self.getCommandUsages(childDefinition)
                    if (usages is not None):
                        commandUsages = self._appendCommandUsagesFromDefinition(usages, commandUsages)

        
        self._displayHelp(helpTitle, commandUsages)
        

    