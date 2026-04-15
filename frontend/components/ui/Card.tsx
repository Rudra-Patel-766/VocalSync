import React from 'react'
import { clsx } from 'clsx'

interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className }: CardProps) {
  const classes = clsx(
    'bg-white rounded-xl shadow-sm border border-gray-200',
    className
  )

  return <div className={classes}>{children}</div>
}

export function CardHeader({ children, className }: CardProps) {
  const classes = clsx('px-6 py-4 border-b border-gray-200', className)
  return <div className={classes}>{children}</div>
}

export function CardTitle({ children, className }: CardProps) {
  const classes = clsx('text-lg font-semibold text-gray-900', className)
  return <h3 className={classes}>{children}</h3>
}

export function CardDescription({ children, className }: CardProps) {
  const classes = clsx('text-sm text-gray-600 mt-1', className)
  return <p className={classes}>{children}</p>
}

export function CardContent({ children, className }: CardProps) {
  const classes = clsx('px-6 py-4', className)
  return <div className={classes}>{children}</div>
}

export function CardFooter({ children, className }: CardProps) {
  const classes = clsx('px-6 py-4 border-t border-gray-200', className)
  return <div className={classes}>{children}</div>
}
