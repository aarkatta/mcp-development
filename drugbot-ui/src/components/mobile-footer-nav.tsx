"use client"

import { MessageSquare, Info, Pill } from "lucide-react"
import { usePathname } from "next/navigation"
import { motion } from "framer-motion"
import Link from "next/link"

export default function MobileFooterNav() {
  const pathname = usePathname()

  const navItems = [
    { href: "/", label: "Chat", icon: MessageSquare },
    { href: "/about", label: "About", icon: Info },
  ]

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 bg-background border-t z-30">
      <div className="flex items-center justify-around">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`relative flex flex-1 flex-col items-center justify-center py-2 transition-colors ${
                isActive ? "text-primary" : "text-muted-foreground"
              }`}
            >
              <Icon className="h-5 w-5" />
              <span className="text-xs mt-1">{item.label}</span>
              {isActive && (
                <motion.div
                  className="absolute bottom-0 h-0.5 w-8 ai-gradient-bg"
                  layoutId="mobile-nav-indicator"
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
              )}
            </Link>
          )
        })}
      </div>
    </div>
  )
}
