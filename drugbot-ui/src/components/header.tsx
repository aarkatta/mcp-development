"use client"

import { useState } from "react"
import Link from "next/link"
import { ModeToggle } from "@/components/mode-toggle"
import { Menu, X, Pill, MessageSquare, Info } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { usePathname } from "next/navigation"

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const pathname = usePathname()

  const navItems = [
    { href: "/", label: "Chat", icon: MessageSquare },
    { href: "/about", label: "About", icon: Info },
  ]

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center justify-between px-4">
          <motion.div
            className="flex items-center gap-2"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Link href="/" className="flex items-center gap-2" title="DrugBot - Home">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg ai-gradient-bg text-white">
                <Pill className="h-4 w-4" />
              </div>
              <span className="text-lg font-bold tracking-tight ai-gradient-text">DrugBot</span>
            </Link>
          </motion.div>

          <motion.nav
            className="hidden md:flex items-center gap-6"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            {navItems.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex flex-col items-center text-sm font-medium transition-colors hover:text-primary ${
                    isActive ? "text-primary" : "text-foreground/80"
                  }`}
                >
                  {item.label}
                  {isActive && <div className="h-0.5 w-full ai-gradient-bg mt-1" />}
                </Link>
              )
            })}
          </motion.nav>

          <motion.div
            className="flex items-center gap-3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <ModeToggle />
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </motion.div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            className="fixed inset-0 top-14 z-30 bg-background/95 backdrop-blur md:hidden"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            <nav className="flex flex-col gap-2 p-4">
              {navItems.map((item) => {
                const isActive = pathname === item.href
                const Icon = item.icon
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-accent"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                )
              })}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
