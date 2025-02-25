"use client";

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"

const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL


export default function AuthCallback() {
  const router = useRouter()
  const { setAccessToken } = useAuth()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | boolean>(false)

  useEffect(() => {
    const fetchToken = async () => {
    try {

      const response = await fetch(`${AUTH_URL}/auth/token`, {
        method: "GET",
        credentials: "include",
      })
      console.log()

      if (!response.ok) {
        throw new Error("Failed to fetch token")
      }
      const data = await response.json()
      const accessToken = data.accessToken
      setAccessToken(accessToken)
      router.replace("/")
    } catch (err) {
      setError(err instanceof Error ? err.message : "不明なエラー")
      router.replace("/login")
    } finally {
      setLoading(false)
    }
  }

  fetchToken()
  }, [router, setAccessToken])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">
        <h1 className="text-xl">ログイン処理中...</h1>
      </div>
    );
  }
  if (error) {
    return <p className="text-red-500 text-center mt-5">エラー: {error}</p>;
  }
  return null;
}
