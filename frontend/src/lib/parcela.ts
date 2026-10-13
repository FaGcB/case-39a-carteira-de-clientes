export function arredondar2(v: number): number {
  return (Math.sign(v) * Math.round((Math.abs(v) + Number.EPSILON) * 100)) / 100
}

export function calcularParcela(valor: number, taxaMensal: number, parcelas: number): number {
  if (!Number.isFinite(valor) || !Number.isFinite(taxaMensal) || !Number.isInteger(parcelas) || parcelas <= 0) {
    throw new RangeError('Valor, taxa e número de parcelas precisam ser válidos.')
  }
  if (taxaMensal === 0) return arredondar2(valor / parcelas)
  return arredondar2((valor * taxaMensal) / (1 - Math.pow(1 + taxaMensal, -parcelas)))
}

export type SituacaoMargem = 'cabe' | 'excede' | 'sem-vinculo'

export function avaliarMargem(parcela: number, margens: number[]): { situacao: SituacaoMargem; margemReferencia: number | null } {
  if (margens.length === 0) return { situacao: 'sem-vinculo', margemReferencia: null }
  const maior = Math.max(...margens)
  return { situacao: parcela <= maior ? 'cabe' : 'excede', margemReferencia: maior }
}
