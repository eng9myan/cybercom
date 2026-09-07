import './globals.css'
import { I18nProvider } from '@/lib/i18n'
import LocaleBoot from '@/components/LocaleBoot'

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
    <html lang="en" dir="ltr">
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&display=swap"
        />
      </head>
      <body className="antialiased">
        <I18nProvider>
          <LocaleBoot />
          {children}
        </I18nProvider>
      </body>
    </html>
  )
}
