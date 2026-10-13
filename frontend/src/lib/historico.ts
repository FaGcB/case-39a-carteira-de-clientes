import type { Mudanca } from '../api/types'
import { formatarCep, formatarData, formatarEstadoCivil, formatarMoeda, formatarTelefone } from './format'

const SEXO: Record<string, string> = { F: 'Feminino', M: 'Masculino' }

export function formatarValorHistorico(campo: Mudanca['campo'], valor: string | null): string {
  if (valor === null || valor === '') return '(vazio)'
  switch (campo) {
    case 'telefone':
      return formatarTelefone(valor)
    case 'cep':
      return formatarCep(valor)
    case 'salario_bruto':
    case 'margem_disponivel':
      return formatarMoeda(Number(valor))
    case 'data_nascimento':
    case 'data_admissao':
      return formatarData(valor)
    case 'sexo':
      return SEXO[valor] ?? valor
    case 'estado_civil':
      return formatarEstadoCivil(valor)
    default:
      return valor
  }
}
