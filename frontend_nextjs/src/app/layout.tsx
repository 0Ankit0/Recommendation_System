import './globals.css'

export const metadata = {
  title: 'Recommendation System (Next.js)'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
