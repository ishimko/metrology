import sys
from os import system, path
import re
from CommentsCleaner import DeleteComments
from OperatorsCounter import GetOperatorsCount

def GetSrcText(filename):
    if path.isfile(filename):
        f = open(filename, 'r')
        result = f.read()
        f.close()
        
        return result
    else:
        return False
    
def RemoveStringLiterals(srcText):
    return re.sub("'([^']+|'')*'", "", srcText)

def PrepareSource(srcText):
    srcText = srcText.lower()
    srcText = RemoveStringLiterals(srcText)
    srcText = DeleteComments(srcText)
    
    srcText = re.sub(r"\b(record|case|try|repeat)\b", "begin", srcText)
    srcText = re.sub(r"\buntil\b", "end;", srcText)
    srcText = srcText.replace(";", " ; ")
    srcText = re.sub(r"\bend\b", "; end", srcText)
    
    return re.sub(r"\bprogram .*?;", "", srcText)   
    

def ProcessError(errorStr):
    print("Ошибка: " + errorStr + ".")    
    system("pause")
    
    exit(1)

def GetMaxIfNestingLevel(srcText):
    ST_NORMAL = 0
    ST_BEGIN_END_BLOCK = 1
    ST_THEN_BLOCK = 2
    ST_ELSE_BLOCK = 3
    
    NO_NESTING = -1 
        
    wordsList = srcText.split()
    maxNestingLevel = nestingLevel = NO_NESTING
    currentState = ST_NORMAL
    statesStack = []
    
    for currentWord in wordsList:
        if currentWord == "then":
            statesStack.append(currentState)
            
            nestingLevel += 1
            if nestingLevel > maxNestingLevel:
                maxNestingLevel = nestingLevel
            
            currentState = ST_THEN_BLOCK
                
        elif currentWord == "else":
            if currentState == ST_THEN_BLOCK:
                currentState = ST_ELSE_BLOCK
            else:
                nestingLevel -= 1
                currentState = statesStack.pop()
        
        elif currentWord == ";":
            while currentState != ST_BEGIN_END_BLOCK and currentState != ST_NORMAL:
                nestingLevel -= 1
                currentState = statesStack.pop()
                
        elif currentWord == 'begin':
            statesStack.append(currentState)
            currentState = ST_BEGIN_END_BLOCK
            
        elif currentWord == 'end':
            currentState = statesStack.pop()
    
    return maxNestingLevel 

def GetIfOperatorsNumber(srcText):
    return len(re.findall(r"\bif\b", srcText))

def PrintResult(operatorsCount, maxIfNestingLevel, ifOperatorsCount):
    print("Файл: {}".format(path.abspath(sys.argv[1])))
    print("Размер: {} байт\n".format(path.getsize(sys.argv[1])))
    
    print("Абсолютная сложность программы: {}".format(ifOperatorsCount))
    print("Относительная сложность программы: {}".format(ifOperatorsCount / operatorsCount))
    
    if maxIfNestingLevel <= 0:
        print("Вложенные операторы условия отсутствуют")
    else:
        print("Максимальный уровень вложенности оператора условия: {}".format(maxIfNestingLevel))

if __name__ == "__main__":
    PARAMETERS_NUMBER = 2
    FILE_PATH_INDEX = 1
    
    if len(sys.argv) != PARAMETERS_NUMBER:
        ProcessError("отсутствует параметр")
    
    srcText = GetSrcText(sys.argv[FILE_PATH_INDEX])
    
    if not srcText:
        ProcessError("файл не найден")
    else:
        srcText = PrepareSource(srcText)       
    
    PrintResult(GetOperatorsCount(srcText), GetMaxIfNestingLevel(srcText), GetIfOperatorsNumber(srcText))
    
    system("pause")
