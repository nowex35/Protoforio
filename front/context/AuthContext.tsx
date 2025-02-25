"use client";
import { createContext, useContext, useState, ReactNode } from "react"

interface UserType {
  userId: string
}

interface AuthContextType {
  accessToken: string | null
  setAccessToken: (token: string | null) => void
  user: UserType | null
  setUser: (user: UserType | null) => void
}

const AuthContext = createContext<AuthContextType>({
  accessToken: null,
  setAccessToken: () => {},
  user: null,
  setUser: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [user, setUser] = useState<UserType | null>(null)
  return (
    <AuthContext.Provider value={{ accessToken, setAccessToken, user, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext)
}