import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export interface User {
  id?: string;
  email?: string;
  name?: string;
  [key: string]: any;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
}

// 로그인 상태를 관리하는 store
function createAuthStore() {
  // 초기값 설정
  const initialValue: AuthState = {
    isAuthenticated: false,
    user: null,
    token: null
  };

  const { subscribe, set } = writable<AuthState>(initialValue);

  return {
    subscribe,
    
    // 로그인 함수
    login: (userInfo: User, token: string) => {
      const authData: AuthState = {
        isAuthenticated: true,
        user: userInfo,
        token: token
      };
      
      // localStorage에 저장 (브라우저 환경에서만)
      if (browser) {
        localStorage.setItem('auth', JSON.stringify(authData));
      }
      
      set(authData);
    },
    
    // 로그아웃 함수
    logout: () => {
      const authData: AuthState = {
        isAuthenticated: false,
        user: null,
        token: null
      };
      
      // localStorage에서 제거 (브라우저 환경에서만)
      if (browser) {
        localStorage.removeItem('auth');
      }
      
      set(authData);
    },
    
    // 로그인 상태 복원 함수
    initialize: () => {
      if (browser) {
        try {
          const stored = localStorage.getItem('auth');
          if (stored) {
            const authData: AuthState = JSON.parse(stored);
            if (authData && typeof authData === 'object' && 'isAuthenticated' in authData) {
              set(authData);
            }
          }
        } catch (error) {
          console.error('Failed to parse auth data from localStorage:', error);
          // 잘못된 데이터가 있으면 제거
          localStorage.removeItem('auth');
        }
      }
    }
  };
}

export const auth = createAuthStore(); 