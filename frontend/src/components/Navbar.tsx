"use client";

import { useSession, signIn, signOut } from "next-auth/react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const { data: session, status } = useSession();
  const pathname = usePathname();

  return (
    <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl">📈</span>
          <span className="font-bold text-gray-900 text-sm">MF Advisor</span>
        </Link>

        {/* Nav links + auth */}
        <div className="flex items-center gap-3">
          {session && (
            <Link
              href="/dashboard"
              className={`text-sm font-medium transition-colors
                ${
                  pathname === "/dashboard"
                    ? "text-indigo-600"
                    : "text-gray-500 hover:text-gray-900"
                }`}
            >
              Watchlist
            </Link>
          )}

          {status === "loading" ? (
            <div className="h-8 w-8 rounded-full bg-gray-100 animate-pulse" />
          ) : session ? (
            <div className="flex items-center gap-2">
              {session.user?.image && (
                <img
                  src={session.user.image}
                  alt={session.user.name ?? "User"}
                  className="h-8 w-8 rounded-full border border-gray-100"
                />
              )}
              <button
                onClick={() => signOut({ callbackUrl: "/" })}
                className="text-xs text-gray-400 hover:text-gray-700 transition-colors"
              >
                Sign out
              </button>
            </div>
          ) : (
            <button
              onClick={() => signIn("google", { callbackUrl: "/dashboard" })}
              className="text-sm font-medium bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Sign in
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
