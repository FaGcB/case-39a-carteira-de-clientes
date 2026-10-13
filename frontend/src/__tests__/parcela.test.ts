import { describe, expect, it } from 'vitest'
import { arredondar2, avaliarMargem, calcularParcela } from '../lib/parcela'

describe('calcularParcela', () => {
  it('aplica a tabela Price com o exemplo do case', () => {
    expect(calcularParcela(27400, 0.0231, 60)).toBe(848.5)
  })

  it('é estável para os extremos das faixas do motor', () => {
    expect(calcularParcela(1000, 0.0149, 12)).toBe(91.62)
    expect(calcularParcela(60000, 0.0329, 84)).toBe(2113.34)
  })

  it('com taxa zero divide o valor igualmente', () => {
    expect(calcularParcela(1200, 0, 12)).toBe(100)
  })

  it('rejeita número de parcelas inválido', () => {
    expect(() => calcularParcela(1000, 0.02, 0)).toThrow(RangeError)
    expect(() => calcularParcela(1000, 0.02, 1.5)).toThrow(RangeError)
  })
})

describe('arredondar2', () => {
  it('arredonda meio para cima sem erro de ponto flutuante', () => {
    expect(arredondar2(1.005)).toBe(1.01)
    expect(arredondar2(2.675)).toBe(2.68)
  })
})

describe('avaliarMargem', () => {
  it('compara com a maior margem individual, não com a soma', () => {
    expect(avaliarMargem(500, [300, 400])).toEqual({ situacao: 'excede', margemReferencia: 400 })
    expect(avaliarMargem(350, [300, 400])).toEqual({ situacao: 'cabe', margemReferencia: 400 })
  })
  it('sinaliza cliente sem vínculo', () => {
    expect(avaliarMargem(100, []).situacao).toBe('sem-vinculo')
  })
})
