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