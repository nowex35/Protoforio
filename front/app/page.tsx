"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Checkbox } from "@/components/ui/checkbox"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import type React from "react"
import { useAuth } from "@/context/AuthContext"
const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL
const API_URL = process.env.NEXT_PUBLIC_API_URL

interface RecommendationResponse {
  title: string
  description: string
  roadmap: string[]
  technologies: string[]
  outcomes: string[]
}

// カスタムラジオグループアイテム（ラベル付き）
const CustomRadioGroupItem = ({
  value,
  id,
  label,
}: {
  value: string
  id: string
  label: string
}) => (
  <div className="flex items-center space-x-2">
    <RadioGroupItem value={value} id={id} className="peer sr-only" />
    <Label
      htmlFor={id}
      className="flex-1 rounded-lg border border-gray-700 p-4 hover:bg-gray-800 peer-data-[state=checked]:border-blue-500 peer-data-[state=checked]:bg-blue-500/20 transition-all duration-200 ease-in-out cursor-pointer"
    >
      {label}
    </Label>
  </div>
)

// カスタムチェックボックスアイテム
const CustomCheckboxItem = ({
  id,
  label,
  onChange,
  checked,
}: {
  id: string
  label: string
  onChange: (checked: boolean) => void
  checked: boolean
}) => (
  <div className="flex items-center space-x-2">
    <Checkbox id={id} checked={checked} onCheckedChange={onChange} className="peer sr-only" />
    <Label
      htmlFor={id}
      className="flex-1 rounded-lg border border-gray-700 p-4 hover:bg-gray-800 peer-data-[state=checked]:border-indigo-500 peer-data-[state=checked]:bg-indigo-500/20 transition-all duration-200 ease-in-out cursor-pointer"
    >
      {label}
    </Label>
  </div>
)

export default function ProtoforioPage() {
  const [showAuthButton, setShowAuthButton] = useState(false)
  const [engineerType, setEngineerType] = useState("")
  const [programmingLanguage, setProgrammingLanguage] = useState("")
  const [learningPreference, setLearningPreference] = useState("")
  const [interestFields, setInterestFields] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null)
  const recommendationRef = useRef<HTMLDivElement>(null)
  const router = useRouter();

  const { accessToken, setAccessToken ,user, setUser } = useAuth()

  
  const handleInterestFieldChange = (checked: boolean, field: string) => {
    setInterestFields((prev) => (checked ? [...prev, field] : prev.filter((f) => f !== field)))
  }
  
  useEffect(() => {
      const fetchToken = async () => {
      
      const response = await fetch(`${AUTH_URL}/auth/refresh`, {
        method: "GET",
        credentials: "include",
      })

      if (!response.ok) {
        setAccessToken(null)
      }
      const data = await response.json()
      const Token = data.accessToken
      setAccessToken(Token)
      const me_response = await fetch(`${AUTH_URL}/auth/me`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${Token}`,
        },
      })
      if (!me_response.ok) {
        setUser(null)
      }
      const me_data = await me_response.json()
      const user_id = me_data.userId
      setUser({ userId: user_id })
      router.replace("/")
    }
  
    fetchToken()
    }, [router, setAccessToken, setUser])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setErrorMessage("")
    setRecommendation(null)

    // バリデーションチェック
    if (!engineerType) {
      setErrorMessage("エンジニアのタイプを選択してください。")
      setIsLoading(false)
      return
    }
    if (programmingLanguage === "わからない" && !learningPreference) {
      setErrorMessage("「わからない」を選んだ場合、学習方針を選択してください。")
      setIsLoading(false)
      return
    }
    
    // フォームデータにユーザー情報を含める
    const formData: {
      engineerType: string
      programmingLanguage: string
      learningPreference: string
      interestFields: string[];
      accessToken?: string
    } = {
      engineerType,
      programmingLanguage,
      learningPreference,
      interestFields,
    }
    if (accessToken) {
      formData["accessToken"] = accessToken
    }
    try {
      const response = await fetch(`${API_URL}/submit_deepseek`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      })
    
      if (!response.ok) {
        throw new Error("APIリクエストが失敗しました")
      }
    
      const recommendationData = await response.json()
      setRecommendation(recommendationData)
    
      // 結果表示のためスクロール
      setTimeout(() => {
        if (recommendationRef.current) {
          const offset = 50;
          const elementPosition = recommendationRef.current.getBoundingClientRect().top + window.scrollY
          window.scrollTo({ top: elementPosition - offset, behavior: "smooth" })
        }
      }, 300)
    } catch (error) {
      setErrorMessage("データの取得に失敗しました。")
      console.error("エラー:", error)
    } finally {
      setIsLoading(false)
    }
  };

  const sendLoginPage = () => {
    router.replace("/login")
  }
  const logout = async () => {
    try {
      await fetch(`${AUTH_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      })

      setAccessToken(null)
      setUser(null)
      router.replace("/")
    } catch (error) {
      console.error("Failed to logout:", error)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => setShowAuthButton(true), 1000)
    return () => clearTimeout(timer)
  }, [])
  
  useEffect(() => {
    setProgrammingLanguage("")
  }, [engineerType])

  const getTooltipText = (type: string) => {
    switch (type) {
      case "フロントエンド":
        return "フロントエンド開発者はユーザーが直接触れる部分を担当します。"
      case "バックエンド":
        return "バックエンド開発者はサーバーやデータベース処理を担当します。"
      case "AI":
        return "AIエンジニアは人工知能や機械学習のモデルを開発します。"
      case "モバイルエンジニア":
        return "モバイルエンジニアはスマートフォンアプリの開発を行います。"
      default:
        return ""
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8 relative">
      {/* Floating auth button */}
      <AnimatePresence>
        {showAuthButton && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
            className="fixed top-4 right-4 z-50"
          >
            <Button
              variant="outline"
              onClick={user ? logout : sendLoginPage}
              className="bg-transparent border-2 border-purple-500 text-purple-400 hover:bg-gradient-to-r hover:from-blue-500 hover:to-purple-600 hover:text-white transition-all duration-300 rounded-full px-6 py-2 text-lg font-semibold shadow-lg hover:shadow-purple-500/50"
            >
              {user ? "ログアウト" : "ログイン"}
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ユーザーがログインしているときだけ、画面右下に履歴ボタンを固定表示 */}
      {user && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
          className="fixed bottom-4 right-4 z-40"
        >
          <Button
            variant="outline"
            onClick={() => router.push("/history")}
            className="bg-transparent border-2 border-purple-500 text-purple-400 hover:bg-gradient-to-r hover:from-blue-500 hover:to-purple-600 hover:text-white transition-all duration-300 rounded-full px-6 py-2 text-lg font-semibold shadow-lg hover:shadow-purple-500/50"
          >
            履歴を確認
          </Button>
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-2xl mx-auto"
      >
        <h1 className="text-4xl font-bold text-center mb-8 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
          Protoforio
        </h1>

        {errorMessage && <div className="text-red-500 text-center">{errorMessage}</div>}
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Q1: どんなエンジニアになりたいか */}
          <div>
            <Label className="text-lg mb-2 block">Q1: どんなエンジニアになりたいですか？</Label>
            <RadioGroup value={engineerType} onValueChange={setEngineerType} className="grid grid-cols-2 gap-2">
              {["フロントエンド", "バックエンド", "AI", "モバイルエンジニア"].map((type) => (
                <div className="tooltip" key={type}>
                  <CustomRadioGroupItem key={type} value={type.toLowerCase()} id={type.toLowerCase()} label={type} />
                  <span className="tooltiptext">{getTooltipText(type)}</span>
                </div>
                
              ))}
            </RadioGroup>
          </div>

          {/* Q2: 興味のある言語 */}
          <div>
            <Label className="text-lg mb-2 block">Q2: 興味のある言語・フレームワークは？</Label>
            <RadioGroup
                value={programmingLanguage}
                onValueChange={setProgrammingLanguage}
                className="grid grid-cols-2 gap-2"
              >
          {(() => {
            switch (engineerType) {
              case "フロントエンド":
                return (
                  <>
                    {["JavaScript", "TypeScript", "HTML/CSS", "React", "Vue.js", "Svelte", "わからない"].map((lang) => (
                    <CustomRadioGroupItem key={lang} value={lang.toLowerCase()} id={lang.toLowerCase()} label={lang} />
                    ))}
                  </>
                )
              case "バックエンド":
                return (
                  <>
                    {["Python", "JavaScript", "Java", "C#", "Ruby", "Go", "PHP", "Node.js", "わからない"].map((lang) => (
                    <CustomRadioGroupItem key={lang} value={lang.toLowerCase()} id={lang.toLowerCase()} label={lang} />
                    ))}
                  </>
                )
              case "ai":
                return (
                  <>
                    {["Python", "R", "Julia", "JavaScript", "C++", "わからない"].map((lang) => (
                    <CustomRadioGroupItem key={lang} value={lang.toLowerCase()} id={lang.toLowerCase()} label={lang} />
                    ))}
                  </>
                )

              case "モバイルエンジニア":
                return (
                  <>
                    {["Swift", "Kotlin", "Dart", "Java", "React Native", "わからない"].map((lang) => (
                    <CustomRadioGroupItem key={lang} value={lang.toLowerCase()} id={lang.toLowerCase()} label={lang} />
                    ))}
                  </>
                )
              default:
                return (
                  <>
                    {["Python", "JavaScript", "Java", "C", "Ruby", "Go", "PHP", "Swift", "Kotlin", "わからない"].map((lang) => (
                    <CustomRadioGroupItem key={lang} value={lang.toLowerCase()} id={lang.toLowerCase()} label={lang} />
                    ))}
                  </>
                )
            }
          }
          )()}
            </RadioGroup>
          </div>
            

          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            transition={{ duration: 0.3 }}
            className="mt-4"
          >
            <Label className="text-lg mb-2 block">Q3: どんな学習方針がよいですか？</Label>
            <RadioGroup
              value={learningPreference}
              onValueChange={setLearningPreference}
              className="grid grid-cols-2 gap-2"
            >
              <CustomRadioGroupItem value="beginner" id="beginner" label="初心者向け" />
              <CustomRadioGroupItem value="stepup" id="stepup" label="ステップアップ" />
            </RadioGroup>
          </motion.div>

          {/* Q4: 興味のある分野（複数選択可） */}
          <div>
            <Label className="text-lg mb-2 block">Q4: 自分に興味のある分野は？（複数選択可）</Label>
            <div className="grid grid-cols-2 gap-2">
              {["健康", "医療", "ゲーム", "スポーツ", "政治", "教育", "環境", "ビジネス"].map((field) => (
                <CustomCheckboxItem
                  key={field}
                  id={field.toLowerCase()}
                  label={field}
                  checked={interestFields.includes(field)}
                  onChange={(checked) => handleInterestFieldChange(checked, field)}
                />
              ))}
            </div>
          </div>

          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300 ease-in-out transform hover:-translate-y-1 hover:shadow-lg"
            >
              {isLoading ? "読み込み中..." : "プロジェクトを見つける"}
            </Button>
          </motion.div>
        </form>

        {/* API のレスポンスを表示 */}
        {recommendation && (
          <motion.div
            ref={recommendationRef}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mt-16"
          >
            <h2 className="text-3xl font-bold text-center mb-4">おすすめのプロジェクト</h2>
            <Card className="bg-gray-800 text-gray-100 p-6">
              <CardHeader>
                <CardTitle className="text-2xl">{recommendation.title}</CardTitle>
                <CardDescription className="text-gray-400">{recommendation.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div>
                  <h3 className="text-xl font-semibold mb-2">学習ロードマップ</h3>
                  <ol className="list-decimal list-inside space-y-2">
                    {recommendation.roadmap.map((step: string, index: number) => (
                      <li key={index}>{step}</li>
                    ))}
                  </ol>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">使用する技術</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {recommendation.technologies.map((tech: string, index: number) => (
                      <li key={index}>{tech}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">期待される効果</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {recommendation.outcomes.map((outcome: string, index: number) => (
                      <li key={index}>{outcome}</li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}

