import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatINR(paise: number, includeSymbol: boolean = true): string {
  const isNegative = paise < 0
  const absPaise = Math.abs(paise)
  const rupeesPart = Math.floor(absPaise / 100)
  const paisePart = absPaise % 100

  const s = rupeesPart.toString()
  let formattedRupees = ""
  if (s.length <= 3) {
    formattedRupees = s
  } else {
    const lastThree = s.substring(s.length - 3)
    let remaining = s.substring(0, s.length - 3)
    const chunks: string[] = []
    while (remaining.length > 2) {
      chunks.unshift(remaining.substring(remaining.length - 2))
      remaining = remaining.substring(0, remaining.length - 2)
    }
    if (remaining.length > 0) {
      chunks.unshift(remaining)
    }
    formattedRupees = chunks.join(",") + "," + lastThree
  }

  const result = `${formattedRupees}.${paisePart.toString().padStart(2, "0")}`
  const formatted = isNegative ? `-${result}` : result
  return includeSymbol ? (isNegative ? `-₹${result}` : `₹${result}`) : formatted
}
