import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import UploadPage from './pages/UploadPage'
import TranslatePage from './pages/TranslatePage'
import PreviewPage from './pages/PreviewPage'
import GlossaryPage from './pages/GlossaryPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<UploadPage />} />
            <Route path="/translate/:taskId" element={<TranslatePage />} />
            <Route path="/preview/:taskId" element={<PreviewPage />} />
            <Route path="/glossaries" element={<GlossaryPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
