import { describe, expect, it } from 'vitest'
import { formatarValorHistorico as f } from '../lib/historico'

describe('formatarValorHistorico', () => {
  it('mostra vazio de forma explícita', () => {
    expect(f('email', null)).toBe('(vazio)')
    expect(f('complemento', '')).toBe('(vazio)')
  })

  it('formata cada campo como na ficha', () => {
    expect(f('telefone', '11988887777')).toBe('(11) 98888-7777')
    expect(f('cep', '01310100')).toBe('01310-100')
    expect(f('margem_disponivel', '510.00').replace(/\s/g, ' ')).toBe('R$ 510,00')
    expect(f('data_admissao', '2019-03-01')).toBe('01/03/2019')
    expect(f('sexo', 'F')).toBe('Feminino')
    expect(f('nome', 'Maria')).toBe('Maria')
  })
})
