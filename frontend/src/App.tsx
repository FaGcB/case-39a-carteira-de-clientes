import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { ApiError } from './api/http'
import { Layout } from './components/Layout'
import { ClienteEditarPage } from './pages/ClienteEditarPage'
import { ClienteFichaPage } from './pages/ClienteFichaPage'
import { ClientesPage } from './pages/ClientesPage'
import { EmpresaEditarPage } from './pages/EmpresaEditarPage'
import { EmpresaFichaPage } from './pages/EmpresaFichaPage'
import { EmpresasPage } from './pages/EmpresasPage'
import { ImportacaoDetalhePage } from './pages/ImportacaoDetalhePage'
import { ImportacoesPage } from './pages/ImportacoesPage'
import { ErroInesperadoPage, NaoEncontradoPage } from './pages/NaoEncontradoPage'
import { PainelPage } from './pages/PainelPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      refetchOnWindowFocus: false,
      retry: (falhas, erro) => !(erro instanceof ApiError && erro.status >= 400 && erro.status < 500) && falhas < 1,
    },
  },
})

const router = createBrowserRouter([
  {
    element: <Layout />,
    errorElement: <ErroInesperadoPage />,
    children: [
      { path: '/', element: <PainelPage /> },
      { path: '/clientes', element: <ClientesPage /> },
      { path: '/clientes/:id', element: <ClienteFichaPage /> },
      { path: '/clientes/:id/editar', element: <ClienteEditarPage /> },
      { path: '/empresas', element: <EmpresasPage /> },
      { path: '/empresas/:id', element: <EmpresaFichaPage /> },
      { path: '/empresas/:id/editar', element: <EmpresaEditarPage /> },
      { path: '/importacoes', element: <ImportacoesPage /> },
      { path: '/importacoes/:id', element: <ImportacaoDetalhePage /> },
      { path: '*', element: <NaoEncontradoPage /> },
    ],
  },
])

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}
