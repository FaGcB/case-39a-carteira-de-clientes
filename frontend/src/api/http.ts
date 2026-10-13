import type { ErroApiBody } from './types'

const BASE_URL: string = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  readonly status: number
  readonly erros: Record<string, string>
  readonly retryAfter: number | null

  constructor(status: number, mensagem: string, erros: Record<string, string> = {}, retryAfter: number | null = null) {
    super(mensagem)
    this.name = 'ApiError'
    this.status = status
    this.erros = erros
    this.retryAfter = retryAfter
  }

  get semConexao(): boolean {
    return this.status === 0
  }
}

type ValorQuery = string | number | undefined | null

interface Opcoes {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  query?: Record<string, ValorQuery>
  json?: unknown
  form?: FormData
  signal?: AbortSignal
}

function montarUrl(caminho: string, query?: Record<string, ValorQuery>): string {
  const url = new URL(BASE_URL + caminho, window.location.origin)
  if (query) {
    for (const [chave, valor] of Object.entries(query)) {
      if (valor !== undefined && valor !== null && valor !== '') url.searchParams.set(chave, String(valor))
    }
  }
  return url.toString()
}

function lerRetryAfter(res: Response): number | null {
  const bruto = res.headers.get('Retry-After')
  if (!bruto) return null
  const segundos = Number(bruto)
  if (Number.isFinite(segundos)) return Math.max(0, Math.ceil(segundos))
  const data = Date.parse(bruto)
  return Number.isNaN(data) ? null : Math.max(0, Math.ceil((data - Date.now()) / 1000))
}

const MENSAGENS_PADRAO: Record<number, string> = {
  400: 'A requisição tem dados inválidos.',
  404: 'Registro não encontrado.',
  409: 'Este registro foi alterado por outra operação. Recarregue e tente de novo.',
  422: 'Alguns campos precisam de correção.',
  429: 'Muitas consultas em pouco tempo. Aguarde antes de tentar de novo.',
}

export async function request<T>(caminho: string, opcoes: Opcoes = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  let body: BodyInit | undefined
  if (opcoes.json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(opcoes.json)
  } else if (opcoes.form) {
    body = opcoes.form
  }

  let res: Response
  try {
    res = await fetch(montarUrl(caminho, opcoes.query), {
      method: opcoes.method ?? 'GET',
      headers,
      body,
      signal: opcoes.signal,
    })
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') throw e
    throw new ApiError(0, 'Não foi possível falar com o servidor. Verifique sua conexão e tente de novo.')
  }

  if (res.status === 204) return undefined as T

  const texto = await res.text()
  let dados: unknown = null
  if (texto) {
    try {
      dados = JSON.parse(texto)
    } catch {
      dados = null
    }
  }

  if (!res.ok) {
    const corpo = (dados ?? {}) as Partial<ErroApiBody>
    const mensagem =
      typeof corpo.mensagem === 'string' && corpo.mensagem
        ? corpo.mensagem
        : (MENSAGENS_PADRAO[res.status] ??
          (res.status >= 500 ? 'O servidor encontrou um erro. Tente de novo em instantes.' : 'Não foi possível concluir a operação.'))
    throw new ApiError(res.status, mensagem, corpo.erros ?? {}, lerRetryAfter(res))
  }

  return dados as T
}

export function ehApiError(e: unknown): e is ApiError {
  return e instanceof ApiError
}
