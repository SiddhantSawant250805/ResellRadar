import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'ResellRadar // Data Ingestion Control Panel',
  description: 'Technical telemetry console for mining second-hand marketplace listings into HDFS',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-surface text-on-surface antialiased min-h-screen flex flex-col telemetry-grid custom-scrollbar">
        {children}
      </body>
    </html>
  )
}
