import { request } from './http'
import type {
  Alteracao,
  Cliente,
  ClienteInput,
  ClienteResumo,
  Empresa,
  EmpresaInput,
  ExclusaoImportacao,
  FiltrosClientes,
  Importacao,
  LinhaInvalida,
  LinhasImportadas,
  ResultadoLinha,
  Paginado,
  Proposta,
  Resumo,
  VinculoDaEmpresa,
} from './types'

export const api = {
  resumo: (signal?: AbortSignal) => request<Resumo>('/api/resumo', { signal }),

  importacoes: {
    listar: (pagina: number, signal?: AbortSignal) =>
      request<Paginado<Importacao>>('/api/importacoes', {
        query: { pagina, tamanho: 10 },
        signal,
      }),
    obter: (id: number, signal?: AbortSignal) => request<Importacao>(`/api/importacoes/${id}`, { signal }),
    linhasImportadas: (id: number, pagina: number, resultado: ResultadoLinha | undefined, signal?: AbortSignal) =>
      request<LinhasImportadas>(`/api/importacoes/${id}/linhas-importadas`, { query: { pagina, tamanho: 20, resultado }, signal }),
    linhasInvalidas: (id: number, pagina: number, signal?: AbortSignal) =>
      request<Paginado<LinhaInvalida>>(`/api/importacoes/${id}/linhas-invalidas`, {
        query: { pagina, tamanho: 20 },
        signal,
      }),
    enviar: (arquivo: File) => {
      const form = new FormData()
      form.append('arquivo', arquivo)
      return request<Importacao>('/api/importacoes', { method: 'POST', form })
    },
    previaExclusao: (id: number, signal?: AbortSignal) =>
      request<ExclusaoImportacao>(`/api/importacoes/${id}/exclusao`, {
        signal,
      }),
    excluir: (id: number) =>
      request<ExclusaoImportacao>(`/api/importacoes/${id}`, {
        method: 'DELETE',
      }),
  },

  clientes: {
    listar: (f: FiltrosClientes, signal?: AbortSignal) =>
      request<Paginado<ClienteResumo>>('/api/clientes', {
        query: {
          nome: f.nome,
          documento: f.documento,
          ordem: f.ordem,
          direcao: f.direcao,
          pagina: f.pagina,
          tamanho: f.tamanho,
        },
        signal,
      }),
    obter: (id: number, signal?: AbortSignal) => request<Cliente>(`/api/clientes/${id}`, { signal }),
    atualizar: (id: number, dados: ClienteInput) => request<Cliente>(`/api/clientes/${id}`, { method: 'PUT', json: dados }),
    excluir: (id: number) => request<void>(`/api/clientes/${id}`, { method: 'DELETE' }),
    historico: (id: number, pagina: number, signal?: AbortSignal) =>
      request<Paginado<Alteracao>>(`/api/clientes/${id}/historico`, {
        query: { pagina, tamanho: 10 },
        signal,
      }),
  },

  empresas: {
    listar: (pagina: number, busca: string | undefined, signal?: AbortSignal) =>
      request<Paginado<Empresa>>('/api/empresas', {
        query: { pagina, tamanho: 20, busca },
        signal,
      }),
    obter: (id: number, signal?: AbortSignal) => request<Empresa>(`/api/empresas/${id}`, { signal }),
    vinculos: (id: number, pagina: number, nome: string | undefined, signal?: AbortSignal) =>
      request<Paginado<VinculoDaEmpresa>>(`/api/empresas/${id}/vinculos`, {
        query: { pagina, tamanho: 20, nome },
        signal,
      }),
    atualizar: (id: number, dados: EmpresaInput) => request<Empresa>(`/api/empresas/${id}`, { method: 'PUT', json: dados }),
  },

  motor: {
    proposta: (cpf: string, signal?: AbortSignal) => request<Proposta>('/api/motor/proposta', { query: { cpf }, signal }),
  },
}
