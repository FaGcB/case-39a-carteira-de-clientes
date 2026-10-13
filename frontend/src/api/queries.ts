import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './endpoints'
import { ApiError } from './http'
import type { ClienteInput, EmpresaInput, FiltrosClientes, ResultadoLinha } from './types'

export const chaves = {
  resumo: ['resumo'] as const,
  importacoes: (pagina: number) => ['importacoes', 'lista', pagina] as const,
  importacao: (id: number) => ['importacoes', 'detalhe', id] as const,
  linhasImportadas: (id: number, pagina: number, resultado?: ResultadoLinha) =>
    ['importacoes', 'aceitas', id, pagina, resultado ?? ''] as const,
  linhasInvalidas: (id: number, pagina: number) => ['importacoes', 'invalidas', id, pagina] as const,
  clientes: (f: FiltrosClientes) => ['clientes', 'lista', f] as const,
  cliente: (id: number) => ['clientes', 'detalhe', id] as const,
  historico: (id: number, pagina: number) => ['clientes', 'historico', id, pagina] as const,
  empresas: (pagina: number, busca?: string) => ['empresas', 'lista', pagina, busca ?? ''] as const,
  empresa: (id: number) => ['empresas', 'detalhe', id] as const,
  proposta: (cpf: string) => ['motor', 'proposta', cpf] as const,
}

const emAndamento = (status?: string) => status === 'PENDENTE' || status === 'PROCESSANDO'

export function useResumo() {
  return useQuery({
    queryKey: chaves.resumo,
    queryFn: ({ signal }) => api.resumo(signal),
  })
}

export function useImportacoes(pagina: number) {
  return useQuery({
    queryKey: chaves.importacoes(pagina),
    queryFn: ({ signal }) => api.importacoes.listar(pagina, signal),
    placeholderData: keepPreviousData,
    refetchInterval: (q) => (q.state.data?.items.some((i) => emAndamento(i.status)) ? 2000 : false),
  })
}

export function useImportacao(id: number) {
  return useQuery({
    queryKey: chaves.importacao(id),
    queryFn: ({ signal }) => api.importacoes.obter(id, signal),
    refetchInterval: (q) => (emAndamento(q.state.data?.status) ? 1000 : false),
    refetchIntervalInBackground: false,
  })
}

export function useLinhasImportadas(id: number, pagina: number, resultado: ResultadoLinha | undefined, habilitado: boolean) {
  return useQuery({
    queryKey: chaves.linhasImportadas(id, pagina, resultado),
    queryFn: ({ signal }) => api.importacoes.linhasImportadas(id, pagina, resultado, signal),
    placeholderData: keepPreviousData,
    enabled: habilitado,
  })
}

export function useLinhasInvalidas(id: number, pagina: number, habilitado: boolean) {
  return useQuery({
    queryKey: chaves.linhasInvalidas(id, pagina),
    queryFn: ({ signal }) => api.importacoes.linhasInvalidas(id, pagina, signal),
    placeholderData: keepPreviousData,
    enabled: habilitado,
  })
}

export function useEnviarImportacao() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (arquivo: File) => api.importacoes.enviar(arquivo),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['importacoes'] }),
  })
}

export function useInvalidarAposImportacao() {
  const qc = useQueryClient()
  return () =>
    Promise.all([
      qc.invalidateQueries({ queryKey: ['clientes'] }),
      qc.invalidateQueries({ queryKey: ['empresas'] }),
      qc.invalidateQueries({ queryKey: ['importacoes', 'lista'] }),
      qc.invalidateQueries({ queryKey: chaves.resumo }),
    ])
}

export function useClientes(filtros: FiltrosClientes) {
  return useQuery({
    queryKey: chaves.clientes(filtros),
    queryFn: ({ signal }) => api.clientes.listar(filtros, signal),
    placeholderData: keepPreviousData,
  })
}

export function useCliente(id: number) {
  return useQuery({
    queryKey: chaves.cliente(id),
    queryFn: ({ signal }) => api.clientes.obter(id, signal),
    retry: (falhas, erro) => !(erro instanceof ApiError && erro.status === 404) && falhas < 2,
  })
}

export function useHistoricoCliente(id: number, pagina: number) {
  return useQuery({
    queryKey: chaves.historico(id, pagina),
    queryFn: ({ signal }) => api.clientes.historico(id, pagina, signal),
    placeholderData: keepPreviousData,
  })
}

export function useAtualizarCliente(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (dados: ClienteInput) => api.clientes.atualizar(id, dados),
    onSuccess: (cliente) => {
      qc.setQueryData(chaves.cliente(id), cliente)
      return Promise.all([
        qc.invalidateQueries({ queryKey: ['clientes', 'lista'] }),
        qc.invalidateQueries({ queryKey: ['clientes', 'historico', id] }),
      ])
    },
  })
}

export function useExcluirCliente() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.clientes.excluir(id),
    onSuccess: (_, id) => {
      qc.removeQueries({ queryKey: chaves.cliente(id) })
      return Promise.all([qc.invalidateQueries({ queryKey: ['clientes', 'lista'] }), qc.invalidateQueries({ queryKey: chaves.resumo })])
    },
  })
}

export function useEmpresas(pagina: number, busca?: string) {
  return useQuery({
    queryKey: chaves.empresas(pagina, busca),
    queryFn: ({ signal }) => api.empresas.listar(pagina, busca, signal),
    placeholderData: keepPreviousData,
  })
}

export function useEmpresa(id: number) {
  return useQuery({
    queryKey: chaves.empresa(id),
    queryFn: ({ signal }) => api.empresas.obter(id, signal),
    retry: (falhas, erro) => !(erro instanceof ApiError && erro.status === 404) && falhas < 2,
  })
}

export function useAtualizarEmpresa(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (dados: EmpresaInput) => api.empresas.atualizar(id, dados),
    onSuccess: (empresa) => {
      qc.setQueryData(chaves.empresa(id), empresa)
      return Promise.all([qc.invalidateQueries({ queryKey: ['empresas', 'lista'] }), qc.invalidateQueries({ queryKey: ['clientes'] })])
    },
  })
}

export function useProposta(cpf: string | undefined) {
  return useQuery({
    queryKey: chaves.proposta(cpf ?? ''),
    queryFn: ({ signal }) => api.motor.proposta(cpf as string, signal),
    enabled: Boolean(cpf),
    retry: false,
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  })
}

export function usePreviaExclusao(id: number, habilitado: boolean) {
  return useQuery({
    queryKey: ['importacoes', 'exclusao', id],
    queryFn: ({ signal }) => api.importacoes.previaExclusao(id, signal),
    enabled: habilitado,
    staleTime: 0,
    gcTime: 0,
  })
}

export function useExcluirImportacao() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.importacoes.excluir(id),
    onSuccess: (_, id) => {
      qc.removeQueries({ queryKey: chaves.importacao(id) })
      qc.removeQueries({ queryKey: ['clientes', 'detalhe'] })
      qc.removeQueries({ queryKey: ['empresas', 'detalhe'] })
      void qc.invalidateQueries()
    },
  })
}

export function useVinculosEmpresa(id: number, pagina: number, nome: string | undefined) {
  return useQuery({
    queryKey: ['empresas', 'vinculos', id, pagina, nome ?? ''],
    queryFn: ({ signal }) => api.empresas.vinculos(id, pagina, nome, signal),
    placeholderData: keepPreviousData,
  })
}
