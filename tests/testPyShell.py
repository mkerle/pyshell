from unittest import TestCase

from pyshell import PyShell

class testPyShell(TestCase):

    def testPyShellWithCommandDefinition(self):

        shell = PyShell(self.commandDefinition)
        shell.prompt = '(test) '
        setattr(shell, 'getADOMDeviceList', lambda : ['deviceA', 'deviceB', 'deviceC', 'testDevice'])
        setattr(shell, 'handlePolicyAdd', lambda type, deviceName, sitecode, templateName: print('type=%s, deviceName=%s, sitecode=%s, templateName=%s' % (type, deviceName, sitecode, templateName)))
        
        shell.cmdloop()

    def testPyShellMerging(self):

        shell = PyShell(self.commandDefinition)
        shell.prompt = '(test) '
        setattr(shell, 'getADOMDeviceList', lambda : ['deviceA', 'deviceB', 'deviceC', 'testDevice'])
        setattr(shell, 'handlePolicyAdd', lambda type, deviceName, sitecode, templateName: print('type=%s, deviceName=%s, sitecode=%s, templateName=%s' % (type, deviceName, sitecode, templateName)))
        setattr(shell, 'handleAddDynamicInterfaces', lambda type, deviceName, sitecode: print('type=%s, deviceName=%s, sitecode=%s' % (type, deviceName, sitecode)))

        shell.addDefinition(self.commandDefinition2)

        shell.cmdloop()

    def setUp(self) -> None:

        self.commandDefinition = {
            'definitions' : [
                {
                    "cmd-name" : "add",
                    "cmd-type" : "static",                    
                    "cmd-childeren" : [
                        {
                            "cmd-name" : "policy",
                            "cmd-type" : "static",                            
                            "on-execute" : "handlePolicyAdd",
                            "var-name" : "type",
                            "cmd-childeren" : [
                                {
                                    "cmd-name" : "device",
                                    "cmd-type" : "static",                                    
                                    "cmd-childeren" : [  
                                        {                                      
                                            "cmd-type" : "dynamic-source",
                                            "source-type" : "function",
                                            "source" : "getADOMDeviceList",
                                            "var-name" : "deviceName",
                                            "cmd-childeren" : [
                                                {
                                                    "cmd-name" : "sitecode",
                                                    "cmd-type" : "static",                                                    
                                                    "cmd-childeren" : [
                                                        {                                                            
                                                            "cmd-type" : "user-input",
                                                            "var-name" : "sitecode",
                                                            "cmd-childeren" : [
                                                                {
                                                                    "cmd-name" : "template",
                                                                    "cmd-type" : "static",                                                                
                                                                    "cmd-childeren" : [
                                                                        {                                                                            
                                                                            "cmd-type" : "dynamic-source",                                                                
                                                                            "source-type" : "literal",
                                                                            "source" : [ 'general', 'security', 'telco', 'site-specific' ],
                                                                            "var-name" : "templateName"
                                                                        }
                                                                    ]
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }                                        
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        self.commandDefinition2 = {
            'definitions' : [
                {
                    "cmd-name" : "add",
                    "cmd-type" : "static",                    
                    "cmd-childeren" : [
                        {
                            "cmd-name" : "policy",
                            "cmd-type" : "static",                            
                            "var-name" : "type",
                            "cmd-childeren" : [
                                {
                                    "cmd-name" : "device",
                                    "cmd-type" : "static",                                    
                                    "cmd-childeren" : [  
                                        {                                      
                                            "cmd-type" : "dynamic-source",
                                            "source-type" : "function",
                                            "source" : "getADOMDeviceList",
                                            "var-name" : "deviceName",
                                            "cmd-childeren" : [
                                                {
                                                    "cmd-name" : "sitecode",
                                                    "cmd-type" : "static",                                                    
                                                    "cmd-childeren" : [
                                                        {                                                            
                                                            "cmd-type" : "user-input",
                                                            "var-name" : "sitecode",
                                                            "cmd-childeren" : [
                                                                {
                                                                    "cmd-name" : "template",
                                                                    "cmd-type" : "static",                                                                
                                                                    "cmd-childeren" : [
                                                                        {                                                                            
                                                                            "cmd-type" : "dynamic-source",                                                                
                                                                            "source-type" : "literal",
                                                                            "source" : [ 'general', 'rtu' ],
                                                                            "var-name" : "templateName",
                                                                            "on-execute" : "handlePolicyAdd",
                                                                        }
                                                                    ]
                                                                },
                                                                {
                                                                    "cmd-name" : "dynamic-interfaces",
                                                                    "cmd-type" : "static",
                                                                    "on-execute" : "handleAddDynamicInterfaces"
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        return super().setUp()