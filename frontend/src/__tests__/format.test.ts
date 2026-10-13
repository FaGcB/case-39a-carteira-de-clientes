import { describe, expect, it } from 'vitest'
import { calcularIdade, formatarCnpj, formatarCpf, formatarData, formatarMoeda, formatarTelefone } from '../lib/format'

describe('formatação pt-BR', () => {
  it('mascara CPF e CNPJ vindos com ou sem pontuação', () => {
    expect(formatarCpf('34603369000')).toBe('346.033.690-00')
    expect(formatarCpf('346.033.690-00')).toBe('346.033.690-00')
    expect(formatarCnpj('11444777000161')).toBe('11.444.777/0001-61')
  })
  it('formata moeda e datas sem deslocamento de fuso', () => {
    expect(formatarMoeda(4519.96).replace(/\s/g, ' ')).toBe('R$ 4.519,96')
    expect(formatarData('2026-09-14')).toBe('14/09/2026')
  })
  it('formata telefone fixo e celular', () => {
    expect(formatarTelefone('41952048500')).toBe('(41) 95204-8500')
    expect(formatarTelefone('1132345678')).toBe('(11) 3234-5678')
  })
  it('calcula idade considerando o aniversário', () => {
    const ref = new Date(2026, 9, 10)
    expect(calcularIdade('2008-10-10', ref)).toBe(18)
    expect(calcularIdade('2008-10-11', ref)).toBe(17)
  })
})
