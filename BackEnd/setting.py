from datetime import datetime

nowYearMonth = str(datetime.today().year) + '.' + str(datetime.today().month) + '.xml'
XML_KR_SAVEPATH = '.\\Data\\Xml_Files\\KR\\' + nowYearMonth
XML_KR_READPATH = 'Data\\Xml_Files\\KR'

XML_US_SAVEPATH = '.\\Data\\Xml_Files\\US\\' + nowYearMonth
XML_US_READPATH = 'Data\\Xml_Files\\US'

JSON_HISTORY_PATH = './Data/Json_Files/history.txt'

JSON_ANALYZE_FOLDER_PATH = './Data/Json_Files/Today_Analyze'