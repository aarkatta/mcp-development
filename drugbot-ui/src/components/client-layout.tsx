"use client"

import { Suspense, type ReactNode } from "react"
import Header from "@/components/header"
import AnimatedLayout from "@/components/animated-layout"
import MobileFooterNav from "@/components/mobile-footer-nav"

interface ClientLayoutProps {
  children: ReactNode
}

export default function ClientLayout({ children }: ClientLayoutProps) {
  return (
    <div className="flex flex-col min-h-screen">
      <Suspense>
        <Header />
      </Suspense>
      <AnimatedLayout>
        <main id="main-content" className="flex-1 flex flex-col">
          {children}
        </main>
      </AnimatedLayout>
      <MobileFooterNav />
      <footer className="hidden md:block py-4 border-t">
        <div className="container flex items-center justify-center">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} DrugBot. Powered by FDA OpenData &amp; MCP. Not a substitute for professional medical advice.
          </p>
        </div>
      </footer>
    </div>
  )
}
