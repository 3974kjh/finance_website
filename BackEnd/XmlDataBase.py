from xml.etree.ElementTree import Element, SubElement, ElementTree
import xml.etree.ElementTree as ET
import sys, os
import setting
from datetime import datetime
import JsonDataBase

# [PyInstaller에 의해 임시폴더에서 실행될 경우 임시폴더로 접근하는 함수]
def resource_path(relative_path):
  try:
      base_path = sys._MEIPASS
  except Exception:
      base_path = os.path.abspath(".")
  return os.path.join(base_path, relative_path)

def MakeXmlFile(xml_path, Good_Invest_Real_list, stock):
    isSuccess = True

    try:
      root = Element("UESRDATA")

      #해당 월 몇번 업데이트 되었는지 카운트하는 항목 1개 생성
      element = Element(stock)
      root.append(element)
      sub_element1 = SubElement(element, "CODE")
      sub_element1.text = 'ALL'
      sub_element2 = SubElement(element, "RANKSUM")
      sub_element2.text = '0'
      sub_element3 = SubElement(element, "NAME")
      sub_element3.text = '횟수'
      sub_element4 = SubElement(element, "COUNT")
      sub_element4.text = '1'
      sub_element5 = SubElement(element, "FULLCOUNT")
      sub_element5.text = '1'

      for Tag_Name in Good_Invest_Real_list:
        element = Element(stock)
        root.append(element)
        sub_element1 = SubElement(element, "CODE")
        sub_element1.text = Tag_Name['code']
        sub_element2 = SubElement(element, "RANKSUM")
        sub_element2.text = str(Tag_Name['rank'])
        sub_element3 = SubElement(element, "NAME")
        sub_element3.text = Tag_Name['name']
        sub_element4 = SubElement(element, "COUNT")
        sub_element4.text = '1' if int(Tag_Name['rank']) <= 30 else '0'
        sub_element5 = SubElement(element, "FULLCOUNT")
        sub_element5.text = '1'

      tree = ElementTree(root)
      tree.write(
        xml_path,
        encoding="utf-8",       # UTF-8 인코딩 지정
        xml_declaration=True,   # XML 선언 자동 추가
        short_empty_elements=False  # 빈 요소 자동 닫힘 방지)
      )
    except Exception as e:
      isSuccess = False
    return isSuccess

def UpdateXmlFile(xml_path, new_list, stock):
    isSuccess = True

    try:
      with open(xml_path, 'r', encoding='utf-8') as f :
        print('success0')
        tree = ET.parse(f)
        root = tree.getroot()

      test = []

      print('success1')

      IsUpdateCount = False

      for codeInfo in new_list:
        IsInEqual = False
        for child in root.iter(stock):
          if child.find('NAME').text == '횟수' and IsUpdateCount == False:
            child.find('COUNT').text = str(1 + int(child.find('COUNT').text))
            child.find('FULLCOUNT').text = str(1 + int(child.find('FULLCOUNT').text))
            IsUpdateCount = True
            IsInEqual = True
            break
          if child.find('CODE').text == codeInfo['code']:
            child.find('RANKSUM').text = str(int(codeInfo['rank']) + int(child.find('RANKSUM').text))
            child.find('COUNT').text = str(1 + int(child.find('COUNT').text)) if int(codeInfo['rank']) <= 30 else child.find('COUNT').text
            child.find('FULLCOUNT').text = str(1 + int(child.find('FULLCOUNT').text))
            IsInEqual = True
            break
        if False == IsInEqual:
          test.append(codeInfo)
      
      print('success2')

      if len(test) > 0:
        for Tag_Name in test:
          element = Element(stock)
          root.append(element)
          sub_element1 = SubElement(element, "CODE")
          sub_element1.text = Tag_Name['code']
          sub_element2 = SubElement(element, "RANKSUM")
          sub_element2.text = str(Tag_Name['rank'])
          sub_element3 = SubElement(element, "NAME")
          sub_element3.text = Tag_Name['name']
          sub_element4 = SubElement(element, "COUNT")
          sub_element4.text = '1' if int(Tag_Name['rank']) <= 30 else '0'
          sub_element5 = SubElement(element, "FULLCOUNT")
          sub_element5.text = '1'

      print('success4')

      tree.write(
        xml_path,
        encoding="utf-8",       # UTF-8 인코딩 지정
        xml_declaration=True,   # XML 선언 자동 추가
        short_empty_elements=False  # 빈 요소 자동 닫힘 방지))
      )

      print('success5')
    except Exception as e:
      print(e)
      isSuccess = False
    return isSuccess

def ReadXmlFile(xml_path, stock):
    path_dir = xml_path
    folder_list = os.listdir(path_dir)

    매달누적종목리스트 = {}
    # 매달누적종목리스트 Format = {'2023.03.xlsx' : {'RANKSUM' : [], 'CODE' : [], 'NAME': [], 'COUNT' : []}}

    for nowDate in folder_list:
      매달누적종목리스트[nowDate[:-4]] = {}
      매달누적종목리스트[nowDate[:-4]]['RANKSUM'] = []
      매달누적종목리스트[nowDate[:-4]]['CODE'] = []
      매달누적종목리스트[nowDate[:-4]]['NAME'] = []
      매달누적종목리스트[nowDate[:-4]]['COUNT'] = []
      매달누적종목리스트[nowDate[:-4]]['FULLCOUNT'] = []

    총누적종목리스트 = {}
    총누적종목리스트[folder_list[0][:-4]+' ~ '+folder_list[-1][:-4]] = {}
    총누적종목리스트[folder_list[0][:-4]+' ~ '+folder_list[-1][:-4]]['RANKSUM'] = []
    총누적종목리스트[folder_list[0][:-4]+' ~ '+folder_list[-1][:-4]]['CODE'] = []
    총누적종목리스트[folder_list[0][:-4]+' ~ '+folder_list[-1][:-4]]['NAME'] = []
    총누적종목리스트[folder_list[0][:-4]+' ~ '+folder_list[-1][:-4]]['COUNT'] = []
    총누적종목리스트[folder_list[0][:-4]+' ~ '+folder_list[-1][:-4]]['FULLCOUNT'] = []

    xml_stack_data_list = {}
    xml_stock_name = {}
    xml_stock_count = {}
    xml_stock_fullCount = {}

    for folder in folder_list:
      xml_file_path = path_dir + '/' + folder
      xml_new_data_list = {}
      xml_new_count = {}
      xml_new_fullCount = {}
      tree = ET.parse(xml_file_path)
      root = tree.getroot()

      for xml_data in root.iter(stock):
        xml_stock_name[xml_data.find('CODE').text] = xml_data.find('NAME').text

        if xml_data.find('CODE').text not in xml_stack_data_list:
          xml_stack_data_list[xml_data.find('CODE').text] = int(xml_data.find('RANKSUM').text)
          xml_stock_count[xml_data.find('CODE').text] = int(xml_data.find('COUNT').text)
          xml_stock_fullCount[xml_data.find('CODE').text] = int(xml_data.find('FULLCOUNT').text)
        else:
          xml_stack_data_list[xml_data.find('CODE').text] += int(xml_data.find('RANKSUM').text)
          xml_stock_count[xml_data.find('CODE').text] += int(xml_data.find('COUNT').text)
          xml_stock_fullCount[xml_data.find('CODE').text] += int(xml_data.find('FULLCOUNT').text)
        
        if xml_data.find('CODE').text not in xml_new_data_list:
          xml_new_data_list[xml_data.find('CODE').text] = int(xml_data.find('RANKSUM').text)
          xml_new_count[xml_data.find('CODE').text] = int(xml_data.find('COUNT').text)
          xml_new_fullCount[xml_data.find('CODE').text] = int(xml_data.find('FULLCOUNT').text)
        else:
          xml_new_data_list[xml_data.find('CODE').text] += int(xml_data.find('RANKSUM').text)
          xml_new_count[xml_data.find('CODE').text] += int(xml_data.find('COUNT').text)
          xml_new_fullCount[xml_data.find('CODE').text] += int(xml_data.find('FULLCOUNT').text)

      sorted_stack_xml_data = sorted(xml_stack_data_list.items(), key=lambda item:item[1])
      sorted_new_xml_data = sorted(xml_new_data_list.items(), key=lambda item:item[1])

      for item in sorted_new_xml_data:
        매달누적종목리스트[folder[:-4]]['CODE'].append(item[0])
        매달누적종목리스트[folder[:-4]]['RANKSUM'].append(item[1])
        매달누적종목리스트[folder[:-4]]['NAME'].append(xml_stock_name[item[0]])
        매달누적종목리스트[folder[:-4]]['COUNT'].append(xml_new_count[item[0]])
        매달누적종목리스트[folder[:-4]]['FULLCOUNT'].append(xml_new_fullCount[item[0]])

    for item in sorted_stack_xml_data:
      총누적종목리스트[folder_list[0][:-4]+' ~ '+folder_list[-1][:-4]]['CODE'].append(item[0])
      총누적종목리스트[folder_list[0][:-4]+' ~ '+folder_list[-1][:-4]]['RANKSUM'].append(item[1])
      총누적종목리스트[folder_list[0][:-4]+' ~ '+folder_list[-1][:-4]]['NAME'].append(xml_stock_name[item[0]])
      총누적종목리스트[folder_list[0][:-4]+' ~ '+folder_list[-1][:-4]]['COUNT'].append(xml_stock_count[item[0]])
      총누적종목리스트[folder_list[0][:-4]+' ~ '+folder_list[-1][:-4]]['FULLCOUNT'].append(xml_stock_fullCount[item[0]])

    return 매달누적종목리스트, 총누적종목리스트

def transform_data(input_data):
  result = {}
  for key, value in input_data.items():
    result[key] = []
    for i in range(len(value['CODE'])):
      result[key].append({
        'code': value['CODE'][i],
        'name': value['NAME'][i],
        'rankSum': str(value['RANKSUM'][i]),
        'count': str(value['COUNT'][i]),
        'fullCount': str(value['FULLCOUNT'][i])
      })
  return result

def saveXmlDataList(stock, financeDataList):
  isSuccess = True

  nowDate = str(datetime.today().year) + '-' + str(datetime.today().month) + '-' + str(datetime.today().day) + '.txt'
  today_analyze_file_path = setting.JSON_ANALYZE_FOLDER_PATH + '/' + nowDate

  if os.path.exists(today_analyze_file_path) == True:
    return False

  # xml파일에 선별한 종목 카운트 추가하여 저장
  if os.path.isfile(setting.XML_KR_SAVEPATH) == False:
    isSuccess = MakeXmlFile(setting.XML_KR_SAVEPATH, financeDataList, stock)
  else:
    isSuccess = UpdateXmlFile(setting.XML_KR_SAVEPATH, financeDataList, stock)

  if (isSuccess == True):
    isSuccess = JsonDataBase.SaveAnalyzeJsonFile(financeDataList)

  return isSuccess

def getXmlDataList(stock):
  매달누적종목리스트, 총누적종목리스트 = ReadXmlFile(setting.XML_KR_READPATH, stock)

  return {
    'perMonthDataList': transform_data(매달누적종목리스트),
    'allPeriodDataList': transform_data(총누적종목리스트)
  }