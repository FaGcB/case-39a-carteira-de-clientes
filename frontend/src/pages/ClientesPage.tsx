import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useClientes } from '../api/queries'
import type { ClienteResumo, Direcao, FiltrosClientes, OrdemClientes } from '../api/types'
import { AvisoDeNavegacao, type EstadoNavegacao } from '../components/Aviso'
import { Atualizando, Carregando, Erro, Vazio } from '../components/Estados'
import { Icone } from '../components/Icone'
import { Cabecalho } from '../components/Layout'
import { Paginacao } from '../components/Paginacao'
import { formatarCnpj, formatarCpf, formatarMoeda, formatarNumero, somenteDigitos } from '../lib/format'
import { inteiroPositivo, useCampoDaUrl, useParametrosUrl, useTituloPagina } from '../lib/hooks'

const PADROES = { nome: '', documento: '', ordem: 'nome', direcao: 'asc', pagina: '1' }
const TAMANHO = 20

function Empresas({ c, cnpjBuscado }: { c: ClienteResumo; cnpjBuscado?: string }) {
  if (c.empresas.length === 0) return <span className="texto-suave">Sem vínculo</span>
  const empresas = cnpjBuscado
    ? [...c.empresas].sort((a, b) => Number(b.cnpj === cnpjBuscado) - Number(a.cnpj === cnpjBuscado))
    : c.empresas
  const [principal, ...outras] = empresas
  return (
    <>
      <span className="multiplas" title={empresas.map((e) => `${e.nome_fantasia} (${formatarCnpj(e.cnpj)})`).join('\n')}>
        {principal.nome_fantasia}
        {outras.length > 0 && <span className="contador">+{outras.length}</span>}
      </span>
      <span className="texto-suave tabular">{formatarCnpj(principal.cnpj)}</span>
    </>
  )
}

function CabecalhoOrdenavel({
  rotulo,
  campo,
  ordem,
  direcao,
  aoOrdenar,
  classe,
}: {
  rotulo: string
  campo: OrdemClientes
  ordem: OrdemClientes
  direcao: Direcao
  aoOrdenar: (o: OrdemClientes, d: Direcao) => void
  classe?: string
}) {
  const ativo = ordem === campo
  const proxima: Direcao = ativo && direcao === 'asc' ? 'desc' : 'asc'
  return (
    <th scope="col" className={classe} aria-sort={ativo ? (direcao === 'asc' ? 'ascending' : 'descending') : 'none'}>
      <button type="button" className={`ordenar${ativo ? ' ativo' : ''} ${ativo ? direcao : ''}`} onClick={() => aoOrdenar(campo, proxima)}>
        {rotulo}
        <Icone nome="seta" tamanho={16} />
      </button>
    </th>
  )
}

export function ClientesPage() {
  useTituloPagina('Clientes')
  const [p, definir] = useParametrosUrl(PADROES)
  const filtros: FiltrosClientes = {
    nome: p.nome.trim() || undefined,
    documento: p.documento.trim() || undefined,
    ordem: p.ordem === 'importacao' ? 'importacao' : 'nome',
    direcao: p.direcao === 'desc' ? 'desc' : 'asc',
    pagina: inteiroPositivo(p.pagina),
    tamanho: TAMANHO,
  }
  const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useClientes(filtros)

  const [nome, setNome] = useCampoDaUrl(p.nome, (v) => definir({ nome: v }, { substituir: true }))
  const [documento, setDocumento] = useCampoDaUrl(p.documento, (v) => definir({ documento: v }, { substituir: true }))
  const temFiltro = Boolean(filtros.nome || filtros.documento)
  const digitosBusca = somenteDigitos(filtros.documento ?? '')
  const cnpjBuscado = digitosBusca.length === 14 ? digitosBusca : undefined

  useEffect(() => {
    if (data && data.total > 0 && data.items.length === 0 && filtros.pagina > 1) {
      definir({ pagina: String(Math.ceil(data.total / TAMANHO)) }, { substituir: true })
    }
  }, [data, filtros.pagina, definir])

  return (
    <>
      <Cabecalho titulo="Clientes" subtitulo="Busque por nome, CPF ou pelo CNPJ da empresa em que a pessoa trabalha." />
      <AvisoDeNavegacao />

      <section className="painel">
        <form className="filtros" role="search" onSubmit={(e) => e.preventDefault()}>
          <div className="campo campo-media">
            <label htmlFor="filtro-nome">Nome</label>
            <input
              id="filtro-nome"
              type="search"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="Ex.: jose ferreira"
              autoComplete="off"
            />
          </div>
          <div className="campo campo-media">
            <label htmlFor="filtro-doc">CPF ou CNPJ</label>
            <input
              id="filtro-doc"
              type="search"
              inputMode="numeric"
              value={documento}
              onChange={(e) => setDocumento(e.target.value)}
              placeholder="Com ou sem pontuação"
              autoComplete="off"
            />
          </div>
          {temFiltro && (
            <button
              type="button"
              className="botao botao-fantasma"
              onClick={() => {
                setNome('')
                setDocumento('')
                definir({ nome: '', documento: '' })
              }}
            >
              Limpar filtros
            </button>
          )}
        </form>

        <div className="resultado-total" aria-live="polite">
          {data && !isError && (
            <>
              {formatarNumero(data.total)} {data.total === 1 ? 'cliente encontrado' : 'clientes encontrados'}
              {temFiltro && ' com esses filtros'}
            </>
          )}
        </div>

        <Atualizando ativo={isFetching && isPlaceholderData} />
        {isPending ? (
          <Carregando linhas={8} rotulo="Carregando clientes…" />
        ) : isError ? (
          <Erro erro={error} aoTentarDeNovo={() => refetch()} />
        ) : data.total === 0 ? (
          temFiltro ? (
            <Vazio
              titulo="Nenhum cliente encontrado com esses filtros."
              acao={
                <button type="button" className="botao botao-secundario" onClick={() => definir({ nome: '', documento: '' })}>
                  Limpar filtros
                </button>
              }
            >
              A busca por nome ignora acentos e maiúsculas. Para CNPJ, use os 14 dígitos.
            </Vazio>
          ) : (
            <Vazio
              titulo="A base de clientes ainda está vazia."
              acao={
                <Link to="/importacoes" className="botao botao-primario">
                  Importar planilha
                </Link>
              }
            >
              Importe uma planilha de parceiro para começar.
            </Vazio>
          )
        ) : (
          <>
            <div className="tabela-rolagem">
              <table className={`tabela tabela-clientes${isPlaceholderData ? ' esmaecida' : ''}`}>
                <thead>
                  <tr>
                    <CabecalhoOrdenavel
                      rotulo="Nome"
                      campo="nome"
                      ordem={filtros.ordem}
                      direcao={filtros.direcao}
                      aoOrdenar={(o, d) => definir({ ordem: o, direcao: d })}
                    />
                    <th scope="col">CPF</th>
                    <th scope="col">Empresa</th>
                    <th scope="col" className="num">
                      <span title="Soma das margens de todos os vínculos">Margem disponível</span>
                    </th>
                    <CabecalhoOrdenavel
                      rotulo="Importado"
                      campo="importacao"
                      ordem={filtros.ordem}
                      direcao={filtros.direcao}
                      aoOrdenar={(o, d) => definir({ ordem: o, direcao: d })}
                      classe="col-opcional"
                    />
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((c) => (
                    <tr key={c.id}>
                      <td>
                        <Link
                          to={`/clientes/${c.id}`}
                          state={{ cpf: c.cpf } satisfies EstadoNavegacao}
                          className="link-linha celula-principal"
                        >
                          {c.nome}
                        </Link>
                      </td>
                      <td className="tabular">{formatarCpf(c.cpf)}</td>
                      <td>
                        <Empresas c={c} cnpjBuscado={cnpjBuscado} />
                      </td>
                      <td className="num">{formatarMoeda(c.margem_disponivel)}</td>
                      <td className="col-opcional texto-suave">{new Date(c.ultima_importacao_em).toLocaleDateString('pt-BR')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Paginacao pagina={data.pagina} tamanho={data.tamanho} total={data.total} aoMudar={(pg) => definir({ pagina: String(pg) })} />
          </>
        )}
      </section>
    </>
  )
}
