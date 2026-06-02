import { Outlet, Link, useLocation } from 'react-router-dom'

export default function Layout() {
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-semibold text-gray-900 hover:text-blue-600 transition-colors">
            Medical Document Translator
          </Link>
          {!isHome && (
            <nav className="flex items-center gap-4">
              <Link
                to="/glossaries"
                className="text-sm text-gray-600 hover:text-blue-600 transition-colors"
              >
                Glossaries
              </Link>
              <Link
                to="/"
                className="text-sm text-gray-600 hover:text-blue-600 transition-colors"
              >
                New Translation
              </Link>
            </nav>
          )}
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
