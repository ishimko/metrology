import sys
import re
from CommentsCleaner import DeleteComments
from os import path, system
from math import log2

validIdentifier = r"[a-z_]\w*"

def GetBodies(subroutinesList):
	bodiesRegexp = re.compile(r"(?<=begin).*(?=end\s*\;)", re.DOTALL)
	
	return bodiesRegexp.findall('\n'.join(subroutinesList))

def GetVariablesFromVarSection(varSectionText):
	return re.findall(validIdentifier + r'\s*(?=:|,)', varSectionText)

def GetDeclarativeSection(srcText, sectionName):
	result = re.search(r"(?<=" + sectionName + r").*?\b(?=begin|type|procedure|function|const|var)\b", srcText, re.DOTALL)
	return result.group() if result else ''
	
def GetAllDeclarativeSections(srcText, sectionName):
	return re.findall(r"(?<=" + sectionName + r").*?\b(?=begin|type|procedure|function|const|var)\b", srcText, re.DOTALL)

def BuildFrequencyDict(entriesList):
	result = {}
	
	for entry in entriesList:
		result[entry] = entriesList.count(entry)
		
	return result
		
def ProcessPascalOperators(srcText):
	pascalOperatorsRegexp = re.compile(r"\b(shl|shr|div|mod|and|or|xor|not|begin|if|for|while|repeat|case|with|break|continue|exit|goto|read(ln)?|write(ln)?)\b|(\+|\-|\*|\/|@|\^|:=|<=|>=|<>)")
	pascalOperatorsDict = BuildFrequencyDict(pascalOperatorsRegexp.findall(srcText))
	srcText = pascalOperatorsRegexp.sub(" ", srcText)
	
	otherKeywords = re.compile(r"\b(then|else|do|end|until|to|downto|of\s*\:)\b")
	srcText = otherKeywords.sub(" ", srcText)
	
	return srcText, {"unique": len(pascalOperatorsDict), "all": sum(pascalOperatorsDict.values())}
	
def GetSrcText(srcFilename):
	if path.isfile(srcFilename):
		srcFile = open(srcFilename, 'r')
		srcText = srcFile.read()
		srcFile.close()
		
		return srcText
	else:
		return False	
	

def CountDelimiters(srcText):
	delimitersDict = BuildFrequencyDict(re.findall(r'[([,;]|:[^=]|\.{2}|\.[^\d]', srcText))
	
	return {'unique': len(delimitersDict), 'all' :sum(delimitersDict.values())}

def RemoveProgramName(srcText):
	return re.sub(r"\bprogram .*?;", " ", srcText, flags = re.IGNORECASE)

def ProcessStandartTypeIdentifiers(srcText):
	standartTypesRegexp = re.compile(r"\b(?:array\b.*?\bof\b\s*|file\s*of|set\s*of|integer|byte|longint|shortint|smallint|real|float|double|boolean|word|char|string|ansistring|longword|text|record|pointer)\b")
	standartTypesList = [''.join((c for c in x if c.isalpha())) for x in standartTypesRegexp.findall(srcText)]
	srcText, standartTypesResult = ProcessIdentifiers(standartTypesList, srcText)
	
	return srcText, standartTypesResult

def GetTypesFromTypeSection(typeSectionText):
	return [x.group(0).strip() for x in re.finditer(validIdentifier + r"\s*(?=\=)", typeSectionText)]

def GetConstantsFromConstSection(constantSectionText):
	return GetTypesFromTypeSection(constantSectionText)
	
def ProcessSubroutineText(subroutineText):
	uniqueOperandsNumber = allOperandsNumber = 0	
	uniqueOperatorsNumber = allOperatorsNumber = 0
	
	subroutineDeclarationRegexp = re.compile(r"(procedure|function)\s*" + validIdentifier + r"\s*(\(.*?\)\s*|):?.*?;", re.DOTALL)
	subroutineDeclaration = subroutineDeclarationRegexp.search(subroutineText)
	subroutineParams = subroutineDeclaration.group(2) if subroutineDeclaration else '' #second matching group
	subroutineText = subroutineText.replace(subroutineParams, '')
	
	varSectionText = GetDeclarativeSection(subroutineText, "var")
	typeSectionText = GetDeclarativeSection(subroutineText, "type")
	
	subroutineText, enumTypesIdentifiersResults = ProcessIdentifiers(GetEnumTypesIdentifiers(varSectionText + typeSectionText), subroutineText)
	uniqueOperandsNumber += enumTypesIdentifiersResults['unique']
	allOperandsNumber += enumTypesIdentifiersResults['all']	
	
	variablesList = GetVariablesFromVarSection(varSectionText + subroutineParams)
	if subroutineDeclaration.group(1) == 'function': #first matching group
		variablesList.append('result')
	subroutineText, variablesResults = ProcessIdentifiers(variablesList, subroutineText)
	uniqueOperandsNumber += variablesResults['unique']
	allOperandsNumber += variablesResults['all']
	
	constSectionText = GetDeclarativeSection(subroutineText, 'const')
	subroutineText, constResults = ProcessIdentifiers(GetConstantsFromConstSection(constSectionText), subroutineText)	
	uniqueOperandsNumber += constResults['unique']
	allOperandsNumber += constResults['all']
	
	subroutineText, typesResults = ProcessIdentifiers(GetTypesFromTypeSection(typeSectionText), subroutineText)
	uniqueOperatorsNumber += typesResults['unique']
	allOperatorsNumber += typesResults['all']
	
	return subroutineText, {
							"operands":
								{
									"all": allOperandsNumber, 
									"unique": uniqueOperandsNumber
								}, 
							"operators":
								{
									"all": allOperatorsNumber,
									"unique": uniqueOperatorsNumber
								}
							}	

def ProcessSubroutines(srcText):
	uniqueOperatorsNumber = allOperatorsNumber = 0
	uniqueOperandsNumber = allOperandsNumber = 0
	
	subroutineRegexp = re.compile(r'(?:procedure|function).*?(?:\bend\b\s*;\s*(?=\bvar\b|\bconst\b|\bprocedure\b|\bfunction\b\b|begin\b|\btype\b))', re.DOTALL)
	subroutinesList = []
	
	for subroutineMatch in subroutineRegexp.finditer(srcText):
		subroutineText = subroutineMatch.group()
		processedSubroutineText, subroutineResults  = ProcessSubroutineText(subroutineText)
		
		subroutinesList.append(processedSubroutineText)
		
		srcText = srcText.replace(subroutineText, "")
		
		uniqueOperandsNumber = subroutineResults['operands']['unique']
		allOperandsNumber = subroutineResults['operands']['all']
		
		uniqueOperatorsNumber = subroutineResults['operators']['unique']
		allOperatorsNumber = subroutineResults['operators']['all']
	
	
	return srcText, subroutinesList, {
									"operands":
										{
											"all": allOperandsNumber, 
											"unique": uniqueOperandsNumber
										}, 
									"operators":
										{
											"all": allOperatorsNumber,
											"unique": uniqueOperatorsNumber
										}
									}

def GetGlobals(srcText, itemSectionName, itemRegexp):
	itemSections = GetAllDeclarativeSections(srcText, itemSectionName)
	return re.findall(itemRegexp, '\n'.join(itemSections))

def GetMain(srcText):
	return re.search(r"(?<=begin).*?(?=end\s*\.|end\s*;\s*(?=var|const|procedure|function|begin|type))", srcText, re.DOTALL).group(0)

def GetOperatorsAndOperandsCount(srcText):
	uniqueOperandsNumber = allOperandsNumber = 0
	
	uniqueOperatorsNumber = allOperatorsNumber = 0
	
	#обработка литералов
	srcText, intermediateResults = ProcessLiterals(srcText)
	uniqueOperandsNumber += intermediateResults['operands']['unique']
	allOperandsNumber += intermediateResults['operands']['all']
	
	uniqueOperatorsNumber += intermediateResults['operators']['unique']
	allOperatorsNumber += intermediateResults['operators']['all']
	
	#удаление дурацкого program myProg;
	srcText = RemoveProgramName(srcText) 
	
	#подсчет разделителей
	intermediateResults = CountDelimiters(srcText)
	uniqueOperatorsNumber += intermediateResults['unique']
	allOperatorsNumber += intermediateResults['all']
	
	#обработка стандартных идентификаторов типов
	srcText, standartTypesResults = ProcessStandartTypeIdentifiers(srcText)
	uniqueOperatorsNumber += standartTypesResults['unique']
	allOperatorsNumber += standartTypesResults['all']
	
	#выделение функций в отдельный список и удаление их из кода
	#отдельная обработка каждой функции и получние общего результата
	srcText, subroutinesList, intermediateResults = ProcessSubroutines(srcText)
	uniqueOperandsNumber += intermediateResults['operands']['unique']
	allOperandsNumber += intermediateResults['operands']['all']
	
	uniqueOperatorsNumber += intermediateResults['operators']['unique']
	allOperatorsNumber += intermediateResults['operators']['all']
	
	#выделение глобальных переменных/констант/типов
	globalVariablesList = GetGlobals(srcText, 'var', validIdentifier + r'\s*(?=:|,)')
	globalConstantsList = GetGlobals(srcText, 'const', validIdentifier + r"\s*(?=\=)")
	allOperandsNumber += len(globalVariablesList) + len(globalConstantsList)
	
	globalTypesList = GetGlobals(srcText, 'type', validIdentifier + r"\s*(?=\=)")
	allOperatorsNumber += len(globalTypesList)	
	
	#воссоединение исходного текста проги и !тел! подпрограмм
	srcText = GetMain(srcText) + '\n'.join(GetBodies(subroutinesList))
	
	#удаление и подсчет глобальных переменных/констант/типов
	srcText, intermediateResults = ProcessIdentifiers(globalVariablesList, srcText)
	uniqueOperandsNumber += intermediateResults['unique']
	allOperandsNumber += intermediateResults['all']
	
	srcText, intermediateResults = ProcessIdentifiers(globalConstantsList, srcText)
	uniqueOperandsNumber += intermediateResults['unique']
	allOperandsNumber += intermediateResults['all']
	
	srcText, intermediateResults = ProcessIdentifiers(globalTypesList, srcText)
	uniqueOperatorsNumber += intermediateResults['unique']
	allOperatorsNumber += intermediateResults['all']
	
	#подсчет операторов языка
	srcText, intermediateResults = ProcessPascalOperators(srcText)
	uniqueOperatorsNumber += intermediateResults['unique']
	allOperatorsNumber += intermediateResults['all']
	
	#оставшиеся идентификаторы - вызовы подпрограмм
	intermediateResults = CountOtherIdentifiers(srcText)
	uniqueOperatorsNumber += intermediateResults['unique']
	allOperatorsNumber += intermediateResults['all']	
	
	return {"all": allOperandsNumber, "unique": uniqueOperandsNumber}, 	{"all": allOperatorsNumber, "unique": uniqueOperatorsNumber}
	

def CountVariables(srcText, variablesList):
	resultDict = {}
	for variable in variablesList:
		variableRegexp = re.compile(r"\b"+variable+r"\b")
		srcText, variableNumber = variableRegexp.subn(" ", srcText)
		if variableNumber:
			resultDict[variable] = variableNumber
	return resultDict, srcText

def CountOtherIdentifiers(srcText):
	otherIdentifiersDict = BuildFrequencyDict(re.findall(r"\b" + validIdentifier + r'\b', srcText)) 
	return 	{'unique': len(otherIdentifiersDict), 'all': sum(otherIdentifiersDict.values())}


def GetEnumTypesIdentifiers(srcText):
	sectionsForLookup = GetDeclarativeSection(srcText, 'type') + GetDeclarativeSection(srcText, 'var')
	enumTypesList = []
	
	enumTypeRegexp = re.compile(r"[^\w]\(.*?\)", re.DOTALL)
	
	for section in sectionsForLookup:
		enumTypesList.extend(enumTypeRegexp.findall(section))
	
	return re.findall(validIdentifier, ''.join(enumTypesList), flags = re.IGNORECASE)

def ProcessIdentifiers(identifiersList, srcText):
	identifiersDict = {}
	for identifier in identifiersList:
		srcText, identifiersDict[identifier] = re.subn(r"\b" + identifier + r"\b", " ", srcText) 
	
	return srcText, {'unique':len(identifiersDict), 'all':sum(identifiersDict.values())}
		
	
def ProcessLiterals(srcText):
	def ProcessElementsByRegexp(srcText, elementRegexp):
		elementRegexp = re.compile(elementRegexp, re.DOTALL + re.IGNORECASE)
		elementsList = elementRegexp.findall(srcText)
		srcText = elementRegexp.sub(' ', srcText)
		frequencyDict = BuildFrequencyDict(elementsList)
		
		return srcText, {'unique': len(frequencyDict), 'all': sum(frequencyDict.values())}
	
	uniqueOperandsNumber = allOperandsNumber = 0
	uniqueOperatorsNumber = allOperatorsNumber = 0
	
	stringLiteralRegexp = r"'(?:[^']+|'')*'"
	srcText, stringLiteralsResult = ProcessElementsByRegexp(srcText, stringLiteralRegexp)
	uniqueOperandsNumber += stringLiteralsResult['unique']
	allOperandsNumber += stringLiteralsResult['all']
	
	srcText = srcText.replace("]", " ")

	arrayDeclarationDelimitersRegexp = r"\[|.{2}]"	
	srcText, arrayDeclarationDelimitersResult = ProcessElementsByRegexp(srcText, arrayDeclarationDelimitersRegexp)		
	uniqueOperatorsNumber += arrayDeclarationDelimitersResult['unique']
	allOperatorsNumber += arrayDeclarationDelimitersResult['all']
	
	numberLiteralsRegexp = r"\b\d+\.?\d*"
	srcText, numberLiteralsResult = ProcessElementsByRegexp(srcText, numberLiteralsRegexp)
	uniqueOperandsNumber += numberLiteralsResult['unique']
	allOperandsNumber += numberLiteralsResult['all']
	
	#строковых литералов нет, можно в нижний регистр
	srcText = srcText.lower()
	
	srcText, boolLiteralsResult = ProcessElementsByRegexp(srcText, r"\b(true|false)\b")
	uniqueOperandsNumber +=  boolLiteralsResult['unique']
	allOperandsNumber += boolLiteralsResult['all']

	return srcText, {
					"operands":
						{
							"all": allOperandsNumber, 
							"unique": uniqueOperandsNumber
						}, 
					"operators":
						{
							"all": allOperatorsNumber,
							"unique": uniqueOperatorsNumber
						}
					}

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print("Ошибка: отсутствует параметр!")
		exit(1)
	
	srcText = GetSrcText(sys.argv[1])
	
	if not srcText:
		print("Файл не найден!")
		exit(1)
		
	print("Файл {}".format(path.abspath(sys.argv[1])))
	print("Размер {} байт\n".format(path.getsize(sys.argv[1])))
		
	srcText = DeleteComments(srcText)
	operandsCount, operatorsCount = GetOperatorsAndOperandsCount(srcText)
	
	halsteadProgramVocabulary = operandsCount['unique'] + operatorsCount['unique']
	halsteadProgramLength = operandsCount['all'] + operatorsCount['all']
	halsteadProgramVolume = halsteadProgramLength * log2(halsteadProgramVocabulary)
	
	halsteadTheoreticalProgramVocabulary = operandsCount['unique'] + 1
	halsteadPotentialProgramVolume = halsteadTheoreticalProgramVocabulary * log2(halsteadTheoreticalProgramVocabulary)
	halsteadTheoreticalProgramLength = operatorsCount['unique'] * log2(operatorsCount['unique']) + operandsCount['unique'] * log2(operandsCount['unique'])
	
	halsteadProrgrammingQuality1 = halsteadPotentialProgramVolume / halsteadProgramVolume
	halsteadProrgrammingQuality2 = 2 * operandsCount['unique'] / (operatorsCount['unique'] * operandsCount['all'])
	
	halsteadIntellectualWork = halsteadTheoreticalProgramLength * log2(halsteadProgramVocabulary / halsteadProrgrammingQuality1)
	
	print('Операторы:\n\tуникальные (n1) - {operators[unique]}\n\tобщее количество (N1) - {operators[all]}'.format(operators = operatorsCount))
	print('Операнды:\n\tуникальные (n2) - {operands[unique]}\n\tобщее количество (N2) - {operands[all]}\n'.format(operands = operandsCount))
	
	
	print("Словарь программы (n) - {}".format(halsteadProgramVocabulary))
	print("Длина программы (N) - {}".format(halsteadProgramLength))
	print("Объем программы (V) - {}\n".format(halsteadProgramVolume))
	
	print("Теоретический словарь программы (n*) - {}".format(halsteadTheoreticalProgramVocabulary))
	print("Потенциальный объем программы (N*) - {}".format(halsteadPotentialProgramVolume))
	print("Теоретическая длина программы (N^) - {}\n".format(halsteadTheoreticalProgramLength))
	
	print("Уровень качества программирования (L) - {}".format(halsteadProrgrammingQuality1))
	print("Уровень качества программирования (без оценки теоретического объема) (L^) - {}\n".format(halsteadProrgrammingQuality2))
	print("Интеллектуальные усилия по написанию программы (E) - {}".format(halsteadIntellectualWork))
	
	system("pause")