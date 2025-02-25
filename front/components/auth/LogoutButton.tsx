"use client";

import { useRouter } from "next/navigation";

export default function LogoutButton() {
  const router = useRouter();

  const logout = () => {
    localStorage.removeItem("accessToken"); // ローカルストレージから削除
    router.replace("/login"); // ログインページへリダイレクト
  };

  return (
    <button
      onClick={logout}
      className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded transition duration-300"
    >
      ログアウト
    </button>
  );
}
