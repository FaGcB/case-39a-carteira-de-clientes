export interface Paginado<T> {
  items: T[]
  total: number
  pagina: number
  tamanho: number
}

export type StatusImportacao = 'PENDENTE' | 'PROCESSANDO' | 'CONCLUIDA' | 'FALHOU'

export interface Importacao {
  id: number
  arquivo: string
  status: StatusImportacao
  total_linhas: number | null
  processadas: number
  importadas: number
  invalidas: number
  criada_em: string
  finalizada_em: string | null
  erro: string | null
}

export type ResultadoLinha = 'NOVO_CLIENTE' | 'NOVO_VINCULO' | 'ATUALIZADA' | 'SEM_MUDANCA' | 'REPETIDA'

export interface LinhaImportada {
  linha: number | null
  resultado: ResultadoLinha | null
  cliente: { id: number; nome: string; cpf: string; excluido: boolean }
  empresa: { id: number; nome_fantasia: string; cnpj: string }
  matricula: string
}

export interface LinhasImportadas extends Paginado<LinhaImportada> {
  por_resultado: Partial<Record<ResultadoLinha | 'SEM_REGISTRO', number>>
}

export interface LinhaInvalida {
  linha: number
  motivos: string[]
  cpf: string | null
  nome: string | null
}

export interface EmpresaRef {
  id: number
  cnpj: string
  razao_social: string
  nome_fantasia: string
}

export interface ClienteResumo {
  id: number
  nome: string
  cpf: string
  empresas: EmpresaRef[]
  margem_disponivel: number
  ultima_importacao_em: string
}

export interface Endereco {
  cep: string
  logradouro: string
  numero: string
  complemento: string | null
  bairro: string
  cidade: string
  uf: string
}

export interface Vinculo {
  id: number
  empresa: EmpresaRef
  matricula: string
  cargo: string
  data_admissao: string
  salario_bruto: number
  margem_disponivel: number
  importacao_id: number
}

export type Sexo = 'F' | 'M'

export interface Cliente {
  id: number
  cpf: string
  nome: string
  data_nascimento: string
  sexo: Sexo | null
  estado_civil: string | null
  email: string | null
  telefone: string | null
  endereco: Endereco
  vinculos: Vinculo[]
  criado_em: string
  atualizado_em: string
  ultima_importacao_id: number | null
}

export interface ClienteInput {
  nome: string
  data_nascimento: string
  sexo: Sexo | null
  estado_civil: string | null
  email: string | null
  telefone: string | null
  endereco: Endereco
}

export interface Empresa extends EmpresaRef {
  setor: string
  cidade: string
  uf: string
  total_vinculos: number
  margem_total: number
}

export type EmpresaInput = Pick<Empresa, 'razao_social' | 'nome_fantasia' | 'setor'>

export interface Proposta {
  cpf: string
  valor: number
  parcelas: number
  taxa_mensal: number
  gerado_em: string
}

export interface Resumo {
  clientes: number
  empresas: number
  vinculos: number
  importacoes: number
  linhas_invalidas: number
  ultima_importacao: Importacao | null
  vinculos_por_empresa: { empresa: EmpresaRef; total: number }[]
}

export type OrdemClientes = 'nome' | 'importacao'
export type Direcao = 'asc' | 'desc'

export interface FiltrosClientes {
  nome?: string
  documento?: string
  ordem: OrdemClientes
  direcao: Direcao
  pagina: number
  tamanho: number
}

export interface ErroApiBody {
  mensagem: string
  erros?: Record<string, string>
}

export interface ExclusaoImportacao {
  importacao_id: number
  arquivo: string
  vinculos_removidos: number
  clientes_removidos: number
  clientes_mantidos: number
  empresas_removidas: number
  linhas_rejeitadas_removidas: number
}

export interface VinculoDaEmpresa {
  id: number
  cliente: { id: number; nome: string; cpf: string }
  matricula: string
  cargo: string
  data_admissao: string
  salario_bruto: number
  margem_disponivel: number
}

export type CampoHistorico =
  | 'nome'
  | 'data_nascimento'
  | 'sexo'
  | 'estado_civil'
  | 'email'
  | 'telefone'
  | 'cep'
  | 'logradouro'
  | 'numero'
  | 'complemento'
  | 'bairro'
  | 'cidade'
  | 'uf'
  | 'cargo'
  | 'data_admissao'
  | 'salario_bruto'
  | 'margem_disponivel'
  | 'vinculo'

export interface Mudanca {
  campo: CampoHistorico
  rotulo: string
  contexto: string | null
  antes: string | null
  depois: string | null
}

export interface Alteracao {
  id: number
  origem: 'IMPORTACAO' | 'EDICAO'
  acao: 'CRIACAO' | 'ATUALIZACAO'
  importacao_id: number | null
  descricao: string
  mudancas: Mudanca[]
  criado_em: string
}
