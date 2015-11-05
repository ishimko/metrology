import re

VALID_IDENTIFIER_REGEXP = r"[a-z_]\w*"

def GetBodies(subroutinesList):
    bodiesRegexp = re.compile(r"(?<=begin).*(?=end\s*\;)", re.DOTALL)
    
    return bodiesRegexp.findall('\n'.join(subroutinesList))

def GetVariablesFromVarSection(varSectionText):
    return re.findall(VALID_IDENTIFIER_REGEXP + r'\s*(?=:|,)', varSectionText)
    
def GetAllDeclarativeSections(srcText, sectionName):
    return re.findall(r"(?<=" + sectionName + r").*?\b(?=begin|type|procedure|function|const|var)\b", srcText, re.DOTALL)
       
def CountPascalOperators(srcText):
    pascalOperatorsRegexp = re.compile(r"\+|\-|\*|\/|@|\^|:=|<=|>=|<>")
    return len(pascalOperatorsRegexp.findall(srcText))
    
GetConstantsFromConstSection = GetVariablesFromVarSection
    
def CountValidIdentifiers(srcText):
    return len(re.findall(r"\b" + VALID_IDENTIFIER_REGEXP + r'\b', srcText)) 

def DeleteIdentifiers(identifiersList, srcText):
    return re.sub(r"\b(" + "|".join(identifiersList) + r")\b", " ", srcText)

def GetVariablesList(srcText):
    variablesList = []
    PARAMETERS_MATCHING_GROUP = 2
    
    subroutineDeclarationRegexp = re.compile(r"(procedure|function)\s+" + VALID_IDENTIFIER_REGEXP + r"\s*(\(.*?\)\s*|):?.*?;", re.DOTALL)
    subroutineDeclarations = subroutineDeclarationRegexp.finditer(srcText)
    for subroutine in subroutineDeclarations:
        if subroutine:
            variablesList.extend(GetVariablesFromVarSection(subroutine.group(PARAMETERS_MATCHING_GROUP)))
    
    for varSection in GetAllDeclarativeSections(srcText, "var"):
        variablesList.extend(GetVariablesFromVarSection(varSection))
    
    return variablesList

def GetConstantsList(srcText):
    constantsList = []
    for constantSection in GetAllDeclarativeSections(srcText, 'const'):
        constantsList.extend(GetConstantsFromConstSection(constantSection))
    
    return constantsList

def GetEnumTypesIdentifiers(srcText):
    sectionsForLookup = GetAllDeclarativeSections(srcText, 'type') + GetAllDeclarativeSections(srcText, 'var')
    enumTypesList = []
    
    enumTypeRegexp = re.compile(r"[^\w]\(.*?\)", re.DOTALL)
    
    for section in sectionsForLookup:
        enumTypesList.extend(enumTypeRegexp.findall(section))
    
    return re.findall(VALID_IDENTIFIER_REGEXP, ''.join(enumTypesList), flags = re.IGNORECASE)

    
def DeleteOperands(srcText):
    operandsList = GetVariablesList(srcText) + GetConstantsList(srcText) + GetEnumTypesIdentifiers(srcText)
    
    return DeleteIdentifiers(operandsList, srcText)

def DeleteCompoundKeywords(srcText):
    return re.sub(r"\b(do|until|of|to|downto)\b", "", srcText)   

def ClearCode(srcText):
    srcText =  DeleteOperands(srcText)
    return DeleteCompoundKeywords(srcText)

def GetOperatorsCount(srcText):
    srcText = ClearCode(srcText)
    
    return CountPascalOperators(srcText) + CountValidIdentifiers(srcText)