from datetime import datetime

# 고정 경로들
XML_KR_READPATH = 'Data/Xml_Files/KR'
XML_US_READPATH = 'Data/Xml_Files/US'

# 동적 파일 경로 생성 함수들
def get_kr_xml_savepath():
    """현재 날짜 기준으로 한국 XML 파일 경로를 동적으로 생성"""
    nowYearMonth = str(datetime.today().year) + '.' + str(datetime.today().month) + '.xml'
    return './Data/Xml_Files/KR/' + nowYearMonth

def get_us_xml_savepath():
    """현재 날짜 기준으로 미국 XML 파일 경로를 동적으로 생성"""
    nowYearMonth = str(datetime.today().year) + '.' + str(datetime.today().month) + '.xml'
    return './Data/Xml_Files/US/' + nowYearMonth

# 하위 호환성을 위한 별칭 (기존 코드가 있을 경우를 대비)
XML_KR_SAVEPATH = get_kr_xml_savepath()
XML_US_SAVEPATH = get_us_xml_savepath()

JSON_HISTORY_PATH = './Data/Json_Files/history.txt'

JSON_ANALYZE_FOLDER_PATH = './Data/Json_Files/Today_Analyze'

JSON_GAME_SCORE_PATH = './Data/Json_Files/Game_Score/game-store-db.txt'