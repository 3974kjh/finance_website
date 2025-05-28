import type { ComponentType } from "svelte";

/**
 * 컴포넌트 생성
 * @param componentInfo
 * @param propsInfo
 * @returns
 */
export const createComponent = async (componentInfo: ComponentType, propsInfo: any = {}) => {
	let close;

	// promise 객체를 만들고 close 객체에 resolve함수를 담는다.
	const promise = new Promise<any>((resolve) => {
		close = resolve;
	});

	propsInfo['close'] = close;

	const component = new componentInfo({ target: document.body, props: propsInfo });

	return promise.finally(() => {
		component.$destroy();
	});
};

/**
 * 전체 값과 현재 값을 받아 전체 대비 현재 값의 비율을 소숫점 둘째 자리까지 계산하여 반환합니다.
 * @param total - 전체 값 (0보다 커야 함)
 * @param current - 현재 값
 * @returns 비율 (소숫점 둘째 자리까지) 또는 에러 메시지
 */
export const calculateRatio = (total: number, current: number): string => {
  if (!!!total || !!!current) {
    return '-';
  }

  // 전체 값이 0보다 작거나 같으면 에러 메시지를 반환
  if (total <= 0) {
    return '-';
  }

  // 비율 계산
  const ratio = (current / total) * 100;

  // 소숫점 둘째 자리까지 반올림하여 문자열로 반환
  return ratio.toFixed(2);
}

/**
 * 해당하는 프로퍼티 찾기
 * @param target 
 * @param candidateInfo 
 * @param sortPropertyList 
 * @returns 
 */
const findSortProperty = (target: string, candidateInfo: any, sortPropertyList: Array<string>) => {
	for (let sortProperty of sortPropertyList) {
		if (candidateInfo[sortProperty].includes(target)) {
			return sortProperty;
		}
	}

	return sortPropertyList[0];
}

/**
 * 유사도 점수 메기는 함수
 * @param target
 * @param candidate
 * @returns
 */
const calculateSimilarityScore = (target: string, candidateInfo: any, sortPropertyList: Array<string>): number => {
	let sortProperty: string = sortPropertyList[0];

	if (sortPropertyList.length > 1) {
		sortProperty = findSortProperty(target, candidateInfo, sortPropertyList);
	}
	
	// 정확히 일치하는 경우 Infinity로 설정되어 항상 최상위에 위치하도록 되어 있습니다.
	if (target === candidateInfo[sortProperty]) return Infinity;

	let score = 0;

	// 검색어가 후보 문자열에 포함되거나, 후보 문자열이 검색어에 포함될 경우 길이에 비례한 점수를 추가
	// 길이가 길수록 점수가 더 높아지므로 유사도가 높은 문자열이 상위로 올라갑니다.
	if (candidateInfo[sortProperty].includes(target)) {
			score += target.length * 10;
	} else if (target.includes(candidateInfo[sortProperty])) {
			score += candidateInfo[sortProperty].length * 8;
	}

	// 레벤슈타인 거리에 따라 점수를 감소시킵니다.
	score -= levenshteinDistance(target, candidateInfo[sortProperty]);

	return score;
}

/**
* 레벤슈타인(Levenshtein distance) 거리 계산
* 두 문자열이 더 다를수록 리턴 값이 커짐
* @param a 
* @param b
* @returns
*/
const levenshteinDistance = (firstString: string, secondString: string): number => {
	const dp: number[][] = Array(firstString.length + 1)
			.fill(null)
			.map(() => Array(secondString.length + 1).fill(0));

	for (let dp_x = 0; dp_x <= firstString.length; dp_x++) dp[dp_x][0] = dp_x;
	for (let dp_y = 0; dp_y <= secondString.length; dp_y++) dp[0][dp_y] = dp_y;

	for (let x = 1; x <= firstString.length; x++) {
			for (let y = 1; y <= secondString.length; y++) {
					const cost = firstString[x - 1] === secondString[y - 1] ? 0 : 1;
					dp[x][y] = Math.min(
							dp[x - 1][y] + 1, // Deletion
							dp[x][y - 1] + 1, // Insertion
							dp[x - 1][y - 1] + cost // Substitution
					);
			}
	}

	return dp[firstString.length][secondString.length];
}

/**
 * 프로퍼티 목록 중, 유효한 프로퍼티항목만 가져오기
 * @param itemInfo 
 * @param sortPropertyList 
 * @returns 
 */
const getExistProperty = (itemInfo: any, sortPropertyList: Array<string>) => {
	let existPropertyList: Array<string> = [];

	for (let sortProperty of sortPropertyList) {
		if (Object.keys(itemInfo).includes(sortProperty)) {
			existPropertyList.push(sortProperty);
		}
	}

	return existPropertyList;
}

/**
* 검색어와 유사도가 높은 순으로 목록 정렬하는 함수
* @param target
* @param list
* @returns
*/
export const sortBySimilarity = (target: string, list: Array<any>, sortPropertyList: Array<string>): Array<any> => {
	if (list.length < 1 || sortPropertyList.length < 1) {
		return [];
	}

	// 프로퍼티 목록 중, 유효한 프로퍼티항목만 가져오기
	sortPropertyList = getExistProperty(list[0], sortPropertyList);

	if (sortPropertyList.length < 1) {
		return sortPropertyList;
	}

	// 리스트는 점수를 기준으로 내림차순으로 정렬
	return list.sort((first: any, second: any) => calculateSimilarityScore(target, second, sortPropertyList) - calculateSimilarityScore(target, first, sortPropertyList));
}

/**
 * 숫자나 문자값을 받아 소수점 셋째 자리에서 반올림하여 둘째 자리까지 표시하고, 둘째 자리가 0이면 생략하는 함수
 * @param value 
 * @returns 
 */
export const formatCostValue = (value: number | string | any): string | null => {
	if (!!value === false) {
		return null;
	}

  // 입력값을 숫자로 변환
  const num = typeof value === 'string' ? parseFloat(value) : value;

  // NaN 체크
  if (isNaN(num)) {
    return null;
  }

  // 소수점 셋째 자리에서 반올림
  const rounded = Math.round(num * 100) / 100;

  // 정수부와 소수부 분리
  const [integerPart, decimalPart] = rounded.toString().split('.');

  // 소수부가 없거나 '0'인 경우 정수부만 반환
  if (!decimalPart || parseInt(decimalPart) === 0) {
    return integerPart;
  }

  // 소수 둘째 자리가 0인 경우 첫째 자리만 표시
  if (decimalPart.length === 1 || decimalPart[1] === '0') {
    return `${integerPart}.${decimalPart[0]}`;
  }

  // 소수 둘째 자리까지 표시
  return `${integerPart}.${decimalPart}`;
}

/**
 * 숫자나 문자값을 가져와서 세 자리마다 쉼표를 넣어 가격을 보기 쉽게 만드는 함수
 * @param value 
 * @returns 
 */
export const formatIncludeComma = (value: number | string | any): string | null => {
	if (!!value === false) {
		return null;
	}

  // 입력값을 문자열로 변환
  let priceString = typeof value === 'number' ? value.toString() : value;

  // 숫자가 아닌 문자 제거 (소수점은 유지)
  priceString = priceString.replace(/[^\d.-]/g, '');

  // 유효한 숫자인지 확인
  if (isNaN(parseFloat(priceString))) {
    return null;
  }

  // 정수부와 소수부 분리
  const [integerPart, decimalPart] = priceString.split('.');

  // 정수부에 쉼표 추가
  const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');

  // 소수부가 있으면 다시 붙이기
  return decimalPart ? `${formattedInteger}.${decimalPart}` : formattedInteger;
}

/**
 * 현재 일자 'yyyy년 mm월 dd일'로 리턴해주는 함수
 * @returns 
 */
export const getTodayDateFormatted = (): string => {
  const today = new Date();
  const year = today.getFullYear();
  const month = (today.getMonth() + 1).toString().padStart(2, '0');
  const day = today.getDate().toString().padStart(2, '0');

  return `${year}년 ${month}월 ${day}일`;
}

/**
 * 현재 일자 'yyyy.mm.dd'로 리턴해주는 함수
 * @returns 
 */
export const getTodayDateDotFormatted = (isDateTime: boolean = false, today: Date = new Date()): string => {
  const year = today.getFullYear();
  const month = (today.getMonth() + 1).toString().padStart(2, '0');
  const day = today.getDate().toString().padStart(2, '0');

  const hour = today.getHours().toString().padStart(2, '0');
  const minute = today.getMinutes().toString().padStart(2, '0');

	return isDateTime ? `${year}.${month}.${day} ${hour}:${minute}` : `${year}.${month}.${day}`;
}

/**
 * 현재 일자 'yyyy-mm-dd'로 리턴해주는 함수
 * @returns 
 */
export const getTodayDateDashFormatted = (): string => {
  const today = new Date();
  const year = today.getFullYear();
  const month = (today.getMonth() + 1).toString().padStart(2, '0');
  const day = today.getDate().toString().padStart(2, '0');

  return `${year}-${month}-${day}`;
}