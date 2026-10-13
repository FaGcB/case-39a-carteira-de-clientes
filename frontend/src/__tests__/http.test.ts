import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, request } from '../api/http'

afterEach(() => vi.unstubAllGlobals())

function responder(status: number, corpo: unknown, headers: Record<string, string> = {}) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(corpo === null ? null : JSON.stringify(corpo), { status, headers })))
}

describe('request', () => {
  it('transforma 429 em ApiError com Retry-After em segundos', async () => {
    responder(429, { mensagem: 'Limite atingido' }, { 'Retry-After': '17' })
    const erro = (await request('/api/motor/proposta').catch((e) => e)) as ApiError
    expect(erro).toBeInstanceOf(ApiError)
    expect(erro.status).toBe(429)
    expect(erro.retryAfter).toBe(17)
    expect(erro.message).toBe('Limite atingido')
  })

  it('preserva erros por campo de um 422', async () => {
    responder(422, { mensagem: 'Corrija', erros: { 'endereco.cep': 'CEP precisa ter 8 dígitos.' } })
    const erro = (await request('/api/clientes/1', { method: 'PUT', json: {} }).catch((e) => e)) as ApiError
    expect(erro.erros['endereco.cep']).toBe('CEP precisa ter 8 dígitos.')
  })

  it('usa mensagem legível quando o servidor não manda corpo', async () => {
    responder(500, null)
    const erro = (await request('/api/clientes').catch((e) => e)) as ApiError
    expect(erro.message).toMatch(/servidor encontrou um erro/)
  })

  it('falha de rede vira status 0 com mensagem para o usuário', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    const erro = (await request('/api/clientes').catch((e) => e)) as ApiError
    expect(erro.semConexao).toBe(true)
  })
})
