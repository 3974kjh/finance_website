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

def ReadGameScores(game_type=""):
  """게임 스코어 데이터 조회"""
  if not os.path.exists(setting.JSON_GAME_SCORE_PATH):
    # 파일이 없으면 초기 구조 생성
    initial_data = {
      "SnakeGame": [],
      "SpaceShootingGame": []
    }
    SaveGameScoreFile(initial_data)
    return initial_data
  
  try:
    with open(setting.JSON_GAME_SCORE_PATH, "r", encoding="utf-8") as f:
      data = json.load(f)
    
    # 특정 게임 타입이 요청되면 해당 데이터만 반환
    if game_type and game_type in data:
      return {game_type: data[game_type]}
    
    return data
  except Exception as e:
    print(f"ReadGameScores 오류: {e}")
    return {"SnakeGame": [], "SpaceShootingGame": []}

def SaveGameScore(game_type, user_id, mode, score):
  """게임 스코어 저장"""
  try:
    # 기존 데이터 읽기
    current_data = ReadGameScores()
    
    # 게임 타입이 없으면 초기화
    if game_type not in current_data:
      current_data[game_type] = []
    
    # 새 스코어 데이터 생성
    new_score = {
      "id": user_id,
      "mode": mode,
      "score": score,
      "timestamp": datetime.now().isoformat()
    }
    
    # 기존 데이터에 추가
    current_data[game_type].append(new_score)
    
    # 점수순으로 정렬 (내림차순)
    current_data[game_type].sort(key=lambda x: x["score"], reverse=True)
    
    # 파일에 저장
    return SaveGameScoreFile(current_data)
    
  except Exception as e:
    print(f"SaveGameScore 오류: {e}")
    return False

def SaveGameScoreFile(data):
  """게임 스코어 파일 저장"""
  try:
    # 디렉토리가 없으면 생성
    os.makedirs(os.path.dirname(setting.JSON_GAME_SCORE_PATH), exist_ok=True)
    
    # JSON 포맷으로 저장
    with open(setting.JSON_GAME_SCORE_PATH, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=2)
    return True
  except Exception as e:
    print(f"SaveGameScoreFile 오류: {e}")
    return False

def GetGameRanking(game_type, mode="", limit=10):
  """게임 랭킹 조회 (점수 순으로 정렬된 상위 N개)"""
  try:
    all_scores = ReadGameScores(game_type)
    
    if game_type not in all_scores:
      return []
    
    scores = all_scores[game_type]
    
    # 모드가 지정되면 해당 모드만 필터링
    if mode:
      scores = [score for score in scores if score.get("mode", "") == mode]
    
    # 점수순으로 정렬 (내림차순)
    scores.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # 상위 limit개만 반환
    return scores[:limit]
    
  except Exception as e:
    print(f"GetGameRanking 오류: {e}")
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