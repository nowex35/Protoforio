'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { jwtDecode } from 'jwt-decode'

const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL
const API_URL = process.env.NEXT_PUBLIC_API_URL

interface RecommendationData {
  title: string
  description: string
  roadmap: string[]
  outcomes: string[]
  technologies: string[]
}

interface HistoryItem {
  id: number | string
  created_at: string
  user_id: string
  recommendation: RecommendationData
}

interface JwtPayload {
  userId: string
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { accessToken, setAccessToken, user, setUser } = useAuth()
  const router = useRouter()

  // トークン取得
  useEffect(() => {
    const fetchToken = async () => {
      try {
        const response = await fetch(`${AUTH_URL}/auth/token`, {
          method: 'GET',
          credentials: 'include',
        })
        if (!response.ok) {
          setAccessToken(null)
          return
        }
        const data = await response.json()
        const token = data.accessToken
        setAccessToken(token)
      } catch (error) {
        console.error('Error fetching token:', error)
      }
    }
    fetchToken()
  }, [setAccessToken])

  // ユーザー情報のセット
  useEffect(() => {
    if (!accessToken) return
    try {
      const decoded = jwtDecode<JwtPayload>(accessToken)
      setUser({ userId: decoded.userId })
    } catch (error) {
      console.error('JWT decode error:', error)
    }
  }, [accessToken, setUser])

  // 履歴の取得
  useEffect(() => {
    if (!user) return
    const fetchHistory = async () => {
      try {
        const response = await fetch(`${API_URL}/history`,{
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'AUTHORIZATION': `Bearer ${accessToken}`,
          },
        })
        if (!response.ok) {
          throw new Error('Failed to fetch history')
        }
        const data = await response.json()
        // バックエンドは { history: [...] } の形式で返す前提
        setHistory(data.history)
      } catch (error) {
        console.error('Error fetching history:', error)
      } finally {
        setIsLoading(false)
      }
    }
    fetchHistory()
  }, [user, accessToken])

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-3xl mx-auto"
      >
        <h1 className="text-4xl font-bold mb-8 text-center text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
          レコメンデーション履歴
        </h1>
        
        {isLoading ? (
          <p className="text-center">読み込み中...</p>
        ) : (
          <div className="space-y-4">
            {history.map((item) => (
              <Card key={item.id} className="bg-gray-800 text-gray-100">
                <CardHeader>
                  <CardTitle className="text-xl">{item.recommendation.title}</CardTitle>
                  <CardDescription className="text-gray-400">
                    {new Date(item.created_at).toLocaleDateString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p>{item.recommendation.description}</p>
                  <div className="mt-4">
                    <Link href={`/history/${item.id}`} passHref>
                      <Button className="bg-blue-600 hover:bg-blue-700">
                        詳細を見る
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex justify-center mt-8"
        >
          <Button
            onClick={() => router.push('/')}
            className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300 ease-in-out transform hover:-translate-y-1 hover:shadow-lg"
          >
            トップページに戻る
          </Button>
        </motion.div>
      </motion.div>
    </div>
  )
}