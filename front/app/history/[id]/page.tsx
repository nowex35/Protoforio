'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
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

interface JwtPayload {
  userId: string
}

export default function RecommendationDetailPage() {
  const { accessToken, setAccessToken, setUser } = useAuth()
  const router = useRouter()
  const { id } = useParams() as { id: string }
  const [data, setData] = useState<RecommendationData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return

    const fetchDetail = async () => {
      try {
        const response = await fetch(`${API_URL}/recommendations/${id}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
          }
        })
        if (!response.ok) {
          throw new Error("詳細情報の取得に失敗しました")
        }
        const detailData = await response.json()
        setData(detailData)
      } catch (err: unknown) {
        setError((err as Error).message || "エラーが発生しました")
        //router.push('/history')
      } finally {
        setIsLoading(false)
      }
    }
    fetchDetail()
  }, [id, accessToken])

  useEffect(() => {
    const fetchToken = async () => {
      try {
        const response = await fetch(`${AUTH_URL}/auth/refresh`, {
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
  
  if (isLoading) return <p className="text-center mt-8">読み込み中...</p>
  if (error) return <p className="text-center mt-8 text-red-500">{error}</p>

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-3xl mx-auto"
      >
        <Card className="bg-gray-800 text-gray-100">
          <CardHeader>
            <CardTitle className="text-3xl">{data?.title}</CardTitle>
            <CardDescription className="text-gray-400">
              詳細情報
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4">{data?.description}</p>
            <div className="mb-4">
              <h3 className="text-xl font-semibold mb-2">学習ロードマップ</h3>
              <ol className="list-decimal list-inside">
                {data?.roadmap.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>
            <div className="mb-4">
              <h3 className="text-xl font-semibold mb-2">使用する技術</h3>
              <ul className="list-disc list-inside">
                {data?.technologies.map((tech, idx) => (
                  <li key={idx}>{tech}</li>
                ))}
              </ul>
            </div>
            <div className="mb-4">
              <h3 className="text-xl font-semibold mb-2">期待される効果</h3>
              <ul className="list-disc list-inside">
                {data?.outcomes.map((outcome, idx) => (
                  <li key={idx}>{outcome}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex justify-center mt-8"
        >
          <Button
            onClick={() => router.back()}
            className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300 ease-in-out"
          >
            戻る
          </Button>
        </motion.div>
      </motion.div>
    </div>
  )
}