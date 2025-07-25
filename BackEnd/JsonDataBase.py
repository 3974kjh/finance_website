import os, setting, json
from datetime import datetime

def ReadHistoryJsonFile():
  if not os.path.exists(setting.JSON_HISTORY_PATH):
    return {}
  try:
    with open(setting.JSON_HISTORY_PATH, "r", encoding="utf-8") as f:
      data = json.load(f)
    return data
  except Exception as e:
    return {}
  
def SaveHistoryJsonFile(data):
  try:
    # JSON 포맷을 txt 파일로 저장
    with open(setting.JSON_HISTORY_PATH, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=2)
    return True
  except Exception as e:
    return False

def ReadAnalyzeJsonFile():
  nowDate = str(datetime.today().year) + '-' + str(datetime.today().month) + '-' + str(datetime.today().day) + '.txt'
  today_analyze_file_path = setting.JSON_ANALYZE_FOLDER_PATH + '/' + nowDate

  if not os.path.exists(today_analyze_file_path):
    return []
  try:
    with open(today_analyze_file_path, "r", encoding="utf-8") as f:
      data = json.load(f)
    return data
  except Exception as e:
    return []

def ReadLatestAnalyzeJsonFile():
  """Today_Analyze 폴더에서 가장 최신 분석 파일을 찾아서 데이터와 날짜를 반환"""
  try:
    if not os.path.exists(setting.JSON_ANALYZE_FOLDER_PATH):
      return {"data": [], "date": None}
    
    # 폴더 내 모든 .txt 파일 찾기
    txt_files = []
    for entry in os.scandir(setting.JSON_ANALYZE_FOLDER_PATH):
      if entry.is_file() and entry.name.endswith('.txt'):
        txt_files.append(entry.name)
    
    if not txt_files:
      return {"data": [], "date": None}
    
    # 파일명을 날짜순으로 정렬 (가장 최신이 마지막)
    txt_files.sort()
    latest_file = txt_files[-1]
    
    # 파일명에서 날짜 추출 (예: 2024-1-15.txt -> 2024-1-15)
    analyze_date = latest_file.replace('.txt', '')
    
    # 파일 내용 읽기
    latest_file_path = os.path.join(setting.JSON_ANALYZE_FOLDER_PATH, latest_file)
    with open(latest_file_path, "r", encoding="utf-8") as f:
      data = json.load(f)
    
    return {"data": data, "date": analyze_date}
    
  except Exception as e:
    print(f"ReadLatestAnalyzeJsonFile 오류: {e}")
    return {"data": [], "date": None}
  
def SaveAnalyzeJsonFile(data):
  nowDate = str(datetime.today().year) + '-' + str(datetime.today().month) + '-' + str(datetime.today().day) + '.txt'
  today_analyze_file_path = setting.JSON_ANALYZE_FOLDER_PATH + '/' + nowDate

  try:
    for entry in os.scandir(setting.JSON_ANALYZE_FOLDER_PATH):
      if entry.is_file():
        os.remove(entry.path)

    # JSON 포맷을 txt 파일로 저장
    with open(today_analyze_file_path, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=2)
    return True
  except Exception as e:
    print(e)
    return False

# print(SaveHistoryJsonFile({}))
# print(ReadHistoryJsonFile())

# print(SaveAnalyzeJsonFile([]))
# print(ReadAnalyzeJsonFile())