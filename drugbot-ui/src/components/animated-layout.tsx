"use client"

import { type ReactNode, useEffect, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { usePathname } from "next/navigation"

interface AnimatedLayoutProps {
  children: ReactNode
}

export default function AnimatedLayout({ children }: AnimatedLayoutProps) {
  const pathname = usePathname()
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)")
    setPrefersReducedMotion(mediaQuery.matches)

    const handleChange = () => setPrefersReducedMotion(mediaQuery.matches)
    mediaQuery.addEventListener("change", handleChange)
    return () => mediaQuery.removeEventListener("change", handleChange)
  }, [])

  const fadeVariants = {
    initial: { opacity: 0 },
    animate: { opacity: 1, transition: { duration: 0.4, ease: "easeInOut" } },
    exit: { opacity: 0, transition: { duration: 0.3, ease: "easeInOut" } },
  }

  const noneVariants = {
    initial: { opacity: 1 },
    animate: { opacity: 1 },
    exit: { opacity: 1 },
  }

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        initial="initial"
        animate="animate"
        exit="exit"
        variants={prefersReducedMotion ? noneVariants : fadeVariants}
        className="flex-1 flex flex-col"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}
