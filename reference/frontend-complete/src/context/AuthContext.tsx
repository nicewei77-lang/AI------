import { useState, type ReactNode } from 'react'
import { login as loginRequest } from '../api/auth'
import { AuthContext } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)

  async function login(email: string, password: string) {
    const result = await loginRequest(email, password)
    setToken(result.token)
  }

  function logout() {
    setToken(null)
  }

  return (
    <AuthContext.Provider
      value={{
        isLoggedIn: token !== null,
        token,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
