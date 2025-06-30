import { browser } from '$app/environment';
import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ url, route }) => {
  // 로그인 페이지는 체크하지 않음
  if (url.pathname === '/login') {
    return {};
  }

  // 브라우저 환경에서만 실행
  if (browser) {
    try {
      const authData = localStorage.getItem('auth');
      
      if (!authData) {
        // 인증 데이터가 없으면 로그인 페이지로 리다이렉트
        throw redirect(303, '/login');
      }

      const auth = JSON.parse(authData);
      
      if (!auth.isAuthenticated) {
        // 인증되지 않은 경우 로그인 페이지로 리다이렉트
        throw redirect(303, '/login');
      }

      return {
        user: auth.user
      };
    } catch (error) {
      // JSON 파싱 오류나 기타 오류 시 로그인 페이지로 리다이렉트
      if (error instanceof Error && error.message.includes('redirect')) {
        throw error; // 리다이렉트 에러는 다시 던짐
      }
      localStorage.removeItem('auth'); // 잘못된 데이터 제거
      throw redirect(303, '/login');
    }
  }

  return {};
}; 