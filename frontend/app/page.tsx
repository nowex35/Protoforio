"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import { useRouter } from "next/navigation"
// カスタムCheckboxItemコンポーネント
const CustomCheckboxItem = ({
  id,
  label,
  onChange,
}: { id: string; label: string; onChange: (checked: boolean) => void }) => (
  <div className="flex items-center space-x-2">
    <Checkbox id={id} onCheckedChange={onChange} className="peer sr-only" />
    <Label
      htmlFor={id}
      className="flex-1 rounded-lg border border-gray-700 p-4 hover:bg-gray-800 peer-data-[state=checked]:border-indigo-500 peer-data-[state=checked]:bg-indigo-500/20 transition-all duration-200 ease-in-out cursor-pointer"
    >
      {label}
    </Label>
  </div>
)

// カスタムRadioGroupItemコンポーネント
const CustomRadioGroupItem = ({ value, id, label }: { value: string; id: string; label: string }) => (
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

export default function ProtoforioPage() {
  const [freeText, setFreeText] = useState("")
  const [engineerType, setEngineerType] = useState<string>("") // 単一選択用
  const [programmingLanguage, setProgrammingLanguage] = useState("")
  const [technologyPreference, setTechnologyPreference] = useState("")
  const [interestFields, setInterestFields] = useState<string[]>([])

  const router = useRouter()

  const handleInterestFieldChange = (checked: boolean, field: string) => {
    setInterestFields((prev) =>
      checked ? [...prev, field] : prev.filter((f) => f !== field)
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
  
    const payload = { freeText, engineerType, programmingLanguage, technologyPreference, interestFields }
  
    try {
      const response = await fetch('/api/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })
  
      const result = await response.json()
      console.log('送信結果:', result)
      alert('送信成功: ' + result.message)
      router.push('/success')
    } catch (error) {
      console.error('送信エラー:', error)
      alert('送信に失敗しました')
    }
  }
  
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-2xl mx-auto"
      >
        <h1 className="text-4xl font-bold mb-8 text-center text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
          Protoforio
        </h1>
        <form onSubmit={handleSubmit} className="space-y-8">
          <div>
            <Label htmlFor="project-idea" className="text-lg mb-2 block">
              あなたのプロジェクトアイデアを教えてください
            </Label>
            <Textarea
              id="project-idea"
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              className="w-full h-32 bg-gray-800 border-gray-700 focus:ring-blue-500 focus:border-blue-500"
              placeholder="例：天気予報アプリ、タスク管理ツール、etc..."
            />
          </div>

          {/* Q1: どんなエンジニアになりたい？（単一選択） */}
          <div>
            <Label className="text-lg mb-2 block">Q1: どんなエンジニアになりたいですか？（単一選択）</Label>
            <RadioGroup
              value={engineerType}
              onValueChange={setEngineerType}
              className="flex flex-col space-y-2"
            >
              {["フロントエンド", "バックエンド", "AI"].map((type) => (
                <CustomRadioGroupItem key={type} value={type.toLowerCase()} id={type.toLowerCase()} label={type} />
              ))}
            </RadioGroup>
          </div>

          <div>
            <Label className="text-lg mb-2 block">Q2: 興味のある言語は？</Label>
            <RadioGroup
              value={programmingLanguage}
              onValueChange={setProgrammingLanguage}
              className="grid grid-cols-2 gap-2"
            >
              {["Python", "C", "Java", "Ruby", "PHP", "JavaScript", "TypeScript", "Go", "Rust", "わからない"].map(
                (lang) => (
                  <CustomRadioGroupItem key={lang} value={lang.toLowerCase()} id={lang.toLowerCase()} label={lang} />
                ),
              )}
            </RadioGroup>
          </div>

          {programmingLanguage === "わからない" && (
            <div>
              <Label className="text-lg mb-2 block">Q2.5: どんな技術がよいですか？</Label>
              <RadioGroup
                value={technologyPreference}
                onValueChange={setTechnologyPreference}
                className="flex flex-col space-y-2"
              >
                <CustomRadioGroupItem value="modern" id="modern" label="モダンな技術" />
                <CustomRadioGroupItem value="legacy" id="legacy" label="レガシーな技術" />
              </RadioGroup>
            </div>
          )}

<div>
            <Label className="text-lg mb-2 block">Q3: 自分に興味のある分野は？（複数選択可）</Label>
            <div className="grid grid-cols-2 gap-2">
              {[
                "旅行",
                "ゲーム",
                "音楽",
                "映画",
                "スポーツ",
                "健康",
                "お金",
                "恋愛",
                "経済",
                "政治",
                "歴史",
                "宗教",
                "ボランティア",
                "SDGs",
              ].map((field) => (
                <CustomCheckboxItem
                  key={field}
                  id={field.toLowerCase()}
                  label={field}
                  onChange={(checked) => handleInterestFieldChange(checked, field.toLowerCase())}
                />
              ))}
            </div>
          </div>

          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300 ease-in-out transform hover:-translate-y-1 hover:shadow-lg"
            >
              アイデアを送信
            </Button>
          </motion.div>
        </form>
      </motion.div>
    </div>
  )
}
