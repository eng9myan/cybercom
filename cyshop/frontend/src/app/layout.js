import './globals.css'

export const metadata = {
  title: 'Cyshop — AI-native Commerce OS',
  description: 'Multi-tenant commerce OS with an AI copilot for CRM, orders, inventory, and customer portal.',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  themeColor: '#0a0a0f',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}
