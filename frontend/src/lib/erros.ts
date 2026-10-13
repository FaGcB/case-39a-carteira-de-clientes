import { ApiError } from '../api/http'

export function mensagemDeErro(erro: unknown): string {
  if (erro instanceof ApiError) return erro.message
  return 'Algo deu errado ao carregar os dados. Tente de novo.'
}

export function separarErros(erro: unknown, camposDaTela: readonly string[]) {
  if (!erro) return { porCampo: {} as Record<string, string>, gerais: [] as string[] }
  if (!(erro instanceof ApiError)) return { porCampo: {}, gerais: ['Não foi possível salvar. Tente de novo.'] }
  const porCampo: Record<string, string> = {}
  const gerais: string[] = []
  for (const [campo, msg] of Object.entries(erro.erros)) {
    if (camposDaTela.includes(campo)) porCampo[campo] = msg
    else gerais.push(msg)
  }
  if (Object.keys(porCampo).length === 0 && gerais.length === 0) gerais.push(erro.message)
  return { porCampo, gerais }
}
