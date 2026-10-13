export const somenteDigitos = (s: string): string => s.replace(/\D/g, '')

export function formatarCpf(cpf: string): string {
  const d = somenteDigitos(cpf)
  if (d.length !== 11) return cpf
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`
}

export function formatarCnpj(cnpj: string): string {
  const d = somenteDigitos(cnpj)
  if (d.length !== 14) return cnpj
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`
}

export function formatarDocumento(doc: string): string {
  const d = somenteDigitos(doc)
  return d.length === 14 ? formatarCnpj(d) : formatarCpf(d)
}

export function formatarCep(cep: string): string {
  const d = somenteDigitos(cep)
  return d.length === 8 ? `${d.slice(0, 5)}-${d.slice(5)}` : cep
}

export function formatarTelefone(tel: string | null): string {
  if (!tel) return '—'
  const d = somenteDigitos(tel)
  if (d.length === 11) return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`
  if (d.length === 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`
  return tel
}

const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
export const formatarMoeda = (v: number): string => brl.format(v)

const pct = new Intl.NumberFormat('pt-BR', { style: 'percent', minimumFractionDigits: 2, maximumFractionDigits: 2 })
export const formatarPercentual = (v: number): string => pct.format(v)

const inteiro = new Intl.NumberFormat('pt-BR')
export const formatarNumero = (v: number): string => inteiro.format(v)

export function formatarData(iso: string | null | undefined): string {
  if (!iso) return '—'
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  if (m) return `${m[3]}/${m[2]}/${m[1]}`
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('pt-BR')
}

export function formatarDataHora(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function calcularIdade(nascimentoIso: string, referencia: Date = new Date()): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(nascimentoIso)
  if (!m) return null
  const [ano, mes, dia] = [Number(m[1]), Number(m[2]), Number(m[3])]
  let idade = referencia.getFullYear() - ano
  const mesRef = referencia.getMonth() + 1
  if (mesRef < mes || (mesRef === mes && referencia.getDate() < dia)) idade--
  return idade
}

export function plural(n: number, singular: string, pluralForm: string): string {
  return `${formatarNumero(n)} ${n === 1 ? singular : pluralForm}`
}

const ESTADO_CIVIL: Record<string, string> = {
  solteiro: 'Solteiro(a)',
  casado: 'Casado(a)',
  divorciado: 'Divorciado(a)',
  viuvo: 'Viúvo(a)',
  'uniao estavel': 'União estável',
}
export function formatarEstadoCivil(v: string | null): string {
  if (!v) return '—'
  const chave = v
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
  return ESTADO_CIVIL[chave] ?? v
}
