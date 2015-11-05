#state constants
ST_NORMAL = 0
ST_STRING = 1
ST_SINGLELINE_COMMENT = 2
ST_MULTILINE_COMMENT_BRACKET = 3
ST_MULTILINE_COMMENT_BRACKET_STAR = 4

#change states constants
CH_NONE = 0,
CH_COMMENT_OPENED = 1,
CH_COMMENT_CLOSED = 2,
CH_COMMENT_2_SYMBOLS_CLOSED = 3

def SetState(currentState, symbolBuffer):
    commentsStateChange = CH_NONE    
    skipApostrophe = False
    
    if symbolBuffer[0] == ord('{'):
        if currentState == ST_NORMAL:
            currentState = ST_MULTILINE_COMMENT_BRACKET
            commentsStateChange = CH_COMMENT_OPENED
            
    elif symbolBuffer[0] == ord('}'):
        if  currentState == ST_MULTILINE_COMMENT_BRACKET:
            currentState = ST_NORMAL
            commentsStateChange = CH_COMMENT_CLOSED
    
    elif symbolBuffer[0] == ord('('):
        if currentState == ST_NORMAL and symbolBuffer[1] == ord('*'):
            currentState = ST_MULTILINE_COMMENT_BRACKET_STAR
            commentsStateChange = CH_COMMENT_OPENED
    
    elif symbolBuffer[0] == ord('*'):
        if currentState == ST_MULTILINE_COMMENT_BRACKET_STAR and symbolBuffer[1] == ord(')'):
            currentState = ST_NORMAL
            commentsStateChange = CH_COMMENT_2_SYMBOLS_CLOSED
    
    elif symbolBuffer[0] == ord('/'):
        if currentState == ST_NORMAL and symbolBuffer[1] == ord('/'):
            currentState = ST_SINGLELINE_COMMENT
            commentsStateChange = CH_COMMENT_OPENED
    
    elif symbolBuffer[0] == ord('\n'):
        if currentState == ST_SINGLELINE_COMMENT:
            currentState = ST_NORMAL
            commentsStateChange = CH_COMMENT_CLOSED
    
    elif symbolBuffer[0] == ord("'"):
        if currentState == ST_NORMAL:
            currentState = ST_STRING
        elif currentState == ST_STRING:
            if symbolBuffer[1] == ord("'"):
                skipApostrophe = True
            else:
                currentState = ST_NORMAL
    
    return commentsStateChange, currentState, skipApostrophe
            

def DeleteComments(srcCode):
    srcCode = bytearray(srcCode, encoding = 'cp1251') 
    srcCode.append(ord('\n'))
    
    commentStateChange = CH_NONE
    currentState = ST_NORMAL
    
    symbolBuffer = bytearray(2)    
    symbolBuffer[0] = 0
    symbolBuffer[1] = srcCode[0]

    lastSymbolIndex = 0
    commentStartIndex = 0
    
    skipApostrophe = False
    
    while lastSymbolIndex <= len(srcCode):
        commentStateChange, currentState, skipApostrophe = SetState(currentState, symbolBuffer)
        
        if commentStateChange == CH_COMMENT_OPENED:
            commentStartIndex = lastSymbolIndex - 1
        
        elif commentStateChange == CH_COMMENT_CLOSED:
            srcCode[commentStartIndex : lastSymbolIndex] = b' '
            lastSymbolIndex = commentStartIndex + 1
            
        elif commentStateChange == CH_COMMENT_2_SYMBOLS_CLOSED:
            srcCode[commentStartIndex : lastSymbolIndex + 1] = b' '
            lastSymbolIndex = commentStartIndex + 1
            
        if skipApostrophe:
            lastSymbolIndex += 1
            
            symbolBuffer[0] = symbolBuffer[1]
            symbolBuffer[1] = srcCode[lastSymbolIndex]
            
            skipApostrophe = False            
            
        symbolBuffer[0] = symbolBuffer[1]            
        lastSymbolIndex += 1
                
        if lastSymbolIndex < len(srcCode):            
            symbolBuffer[1] = srcCode[lastSymbolIndex]
        else:        
            symbolBuffer[1] = 0
            
    
    return srcCode.decode('cp1251')
        
if __name__ == "__main__":
    srcCode = open('test.pas', 'r').read()
    
    srcCode = DeleteComments(srcCode)
    
    open("test.pas_cleaned", 'w').write(srcCode)   