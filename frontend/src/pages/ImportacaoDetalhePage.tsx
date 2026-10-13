import { type KeyboardEvent, useEffect, useRef } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../api/http'
import { useImportacao, useInvalidarAposImportacao, useLinhasImportadas, useLinhasInvalidas } from '../api/queries'
import type { Importacao, ResultadoLinha, StatusImportacao } from '../api/types'
import { Atualizando, Carregando, Erro, Vazio } from '../components/Estados'
import { ExcluirImportacao } from '../components/ExcluirImportacao'
import { Cabecalho } from '../components/Layout'
import { Paginacao } from '../components/Paginacao'
import { ProgressoImportacao, SeloStatus } from '../components/StatusImportacao'
import { formatarCnpj, formatarCpf, formatarDataHora, formatarDocumento, formatarNumero } from '../lib/format'
import { inteiroPositivo, useParametrosUrl, useTituloPagina } from '../lib/hooks'
import { NaoEncontradoPage } from './NaoEncontradoPage'

interface PropsAba {
  id: number
  quantidade: number
  emAndamento: boolean
  pagina: number
  aoMudarPagina: (pagina: number) => void
}

const RESULTADOS: { valor: ResultadoLinha; rotulo: string; dica: string }[] = [
  { valor: 'NOVO_CLIENTE', rotulo: 'Cliente novo', dica: 'O cliente entrou na base por esta linha.' },
  { valor: 'NOVO_VINCULO', rotulo: 'Vínculo novo', dica: 'Cliente já existia; esta linha trouxe um emprego novo.' },
  { valor: 'ATUALIZADA', rotulo: 'Atualizou dados', dica: 'Mudou cadastro ou vínculo. O antes e depois está no histórico do cliente.' },
  { valor: 'SEM_MUDANCA', rotulo: 'Sem mudança', dica: 'Os dados da linha já estavam iguais na base.' },
  { valor: 'REPETIDA', rotulo: 'Repetida no arquivo', dica: 'Mesmo cliente, empresa e matrícula de uma linha anterior deste arquivo.' },
]
const ROTULO_RESULTADO = Object.fromEntries(RESULTADOS.map((r) => [r.valor, r])) as Record<ResultadoLinha, (typeof RESULTADOS)[number]>

function ehResultado(v: string): v is ResultadoLinha {
  return v in ROTULO_RESULTADO
}

function LinhasAceitas({
  id,
  quantidade,
  emAndamento,
  pagina,
  aoMudarPagina,
  resultado,
  aoFiltrar,
}: PropsAba & {
  resultado: ResultadoLinha | undefined
  aoFiltrar: (r: ResultadoLinha | undefined) => void
}) {
  const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useLinhasImportadas(
    id,
    pagina,
    resultado,
    quantidade > 0,
  )

  const quantidadeAnterior = useRef(quantidade)
  useEffect(() => {
    if (quantidade !== quantidadeAnterior.current && quantidade > 0) void refetch()
    quantidadeAnterior.current = quantidade
  }, [quantidade, refetch])

  if (quantidade === 0)
    return <Vazio titulo={emAndamento ? 'Nenhuma linha aceita até agora.' : 'Nenhuma linha desta planilha foi aceita.'} />
  if (isPending) return <Carregando linhas={5} />
  if (isError) return <Erro erro={error} aoTentarDeNovo={() => refetch()} />

  const contagem = data.por_resultado
  const semRegistro = contagem.SEM_REGISTRO ?? 0
  return (
    <>
      <Atualizando ativo={isFetching && isPlaceholderData} />
      {semRegistro > 0 ? (
        <p className="aviso-suave">
          Esta importação é anterior ao registro por linha: aparecem os vínculos que ela trouxe, sem o número da linha da planilha.
        </p>
      ) : (
        <div className="filtro-chips" role="group" aria-label="Filtrar linhas aceitas">
          <button type="button" className="chip" aria-pressed={!resultado} onClick={() => aoFiltrar(undefined)}>
            Todas <span className="chip-num">{formatarNumero(quantidade)}</span>
          </button>
          {RESULTADOS.filter((r) => (contagem[r.valor] ?? 0) > 0 || r.valor === resultado).map((r) => (
            <button
              key={r.valor}
              type="button"
              className="chip"
              aria-pressed={resultado === r.valor}
              title={r.dica}
              onClick={() => aoFiltrar(resultado === r.valor ? undefined : r.valor)}
            >
              {r.rotulo} <span className="chip-num">{formatarNumero(contagem[r.valor] ?? 0)}</span>
            </button>
          ))}
        </div>
      )}
      {data.items.length === 0 ? (
        <Vazio titulo="Nenhuma linha com este resultado." />
      ) : (
        <>
          <div className="tabela-rolagem">
            <table className="tabela">
              <thead>
                <tr>
                  <th scope="col" className="num">
                    Linha
                  </th>
                  <th scope="col">Cliente</th>
                  <th scope="col">Empresa</th>
                  <th scope="col">Matrícula</th>
                  <th scope="col">Resultado</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((l, i) => (
                  <tr key={l.linha ?? `v${i}`}>
                    <td className="num">{l.linha ?? '—'}</td>
                    <td>
                      {l.cliente.excluido ? (
                        <span className="celula-principal">
                          {l.cliente.nome} <span className="etiqueta-suave">excluído</span>
                        </span>
                      ) : (
                        <Link to={`/clientes/${l.cliente.id}`} state={{ cpf: l.cliente.cpf }} className="celula-principal link-linha">
                          {l.cliente.nome}
                        </Link>
                      )}
                      <span className="texto-suave tabular">{formatarCpf(l.cliente.cpf)}</span>
                    </td>
                    <td>
                      <Link to={`/empresas/${l.empresa.id}`} className="celula-principal link-linha">
                        {l.empresa.nome_fantasia}
                      </Link>
                      <span className="texto-suave tabular">{formatarCnpj(l.empresa.cnpj)}</span>
                    </td>
                    <td className="tabular">{l.matricula}</td>
                    <td>
                      {l.resultado ? (
                        <span className={`resultado resultado-${l.resultado.toLowerCase()}`} title={ROTULO_RESULTADO[l.resultado].dica}>
                          {ROTULO_RESULTADO[l.resultado].rotulo}
                        </span>
                      ) : (
                        <span className="texto-suave">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Paginacao pagina={data.pagina} tamanho={data.tamanho} total={data.total} aoMudar={aoMudarPagina} />
        </>
      )}
    </>
  )
}

type Aba = 'aceitas' | 'rejeitadas'

function LinhasDaImportacao({ imp, emAndamento }: { imp: Importacao; emAndamento: boolean }) {
  const [params, definir] = useParametrosUrl({ aba: 'aceitas', pagina: '1', resultado: '' })
  const aba: Aba = params.aba === 'rejeitadas' ? 'rejeitadas' : 'aceitas'
  const pagina = inteiroPositivo(params.pagina)
  const resultado = ehResultado(params.resultado) ? params.resultado : undefined
  const abas: { id: Aba; rotulo: string; quantidade: number }[] = [
    { id: 'aceitas', rotulo: 'Aceitas', quantidade: imp.importadas },
    { id: 'rejeitadas', rotulo: 'Rejeitadas', quantidade: imp.invalidas },
  ]
  const refs = useRef<Record<Aba, HTMLButtonElement | null>>({ aceitas: null, rejeitadas: null })

  const trocar = (nova: Aba) => definir({ aba: nova, resultado: '' }, { substituir: true })
  const aoTeclar = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    const nova: Aba = aba === 'aceitas' ? 'rejeitadas' : 'aceitas'
    trocar(nova)
    refs.current[nova]?.focus()
  }
  const props = { id: imp.id, emAndamento, pagina, aoMudarPagina: (p: number) => definir({ pagina: String(p) }) }

  return (
    <section className="painel" aria-label="Linhas da planilha">
      <div className="abas" role="tablist" aria-label="Linhas da planilha" onKeyDown={aoTeclar}>
        {abas.map((a) => (
          <button
            key={a.id}
            ref={(el) => {
              refs.current[a.id] = el
            }}
            type="button"
            role="tab"
            id={`aba-${a.id}`}
            aria-selected={aba === a.id}
            aria-controls={`painel-${a.id}`}
            tabIndex={aba === a.id ? 0 : -1}
            className={`aba aba-${a.id}`}
            onClick={() => trocar(a.id)}
          >
            {a.rotulo} <span className="aba-num">{formatarNumero(a.quantidade)}</span>
          </button>
        ))}
      </div>
      <div role="tabpanel" id={`painel-${aba}`} aria-labelledby={`aba-${aba}`} className="aba-painel">
        {aba === 'aceitas' ? (
          <LinhasAceitas {...props} quantidade={imp.importadas} resultado={resultado} aoFiltrar={(r) => definir({ resultado: r ?? '' })} />
        ) : (
          <LinhasRejeitadas {...props} quantidade={imp.invalidas} />
        )}
      </div>
    </section>
  )
}

function LinhasRejeitadas({ id, quantidade, emAndamento, pagina, aoMudarPagina }: PropsAba) {
  const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useLinhasInvalidas(id, pagina, quantidade > 0)

  const quantidadeAnterior = useRef(quantidade)
  useEffect(() => {
    if (quantidade !== quantidadeAnterior.current && quantidade > 0) void refetch()
    quantidadeAnterior.current = quantidade
  }, [quantidade, refetch])

  return (
    <>
      <Atualizando ativo={isFetching && isPlaceholderData} />
      {quantidade === 0 ? (
        <Vazio titulo={emAndamento ? 'Nenhuma linha rejeitada até agora.' : 'Todas as linhas foram aceitas.'} />
      ) : isPending ? (
        <Carregando linhas={5} />
      ) : isError ? (
        <Erro erro={error} aoTentarDeNovo={() => refetch()} />
      ) : (
        <>
          <div className="tabela-rolagem">
            <table className="tabela">
              <thead>
                <tr>
                  <th scope="col" className="num">
                    Linha
                  </th>
                  <th scope="col">Cliente na planilha</th>
                  <th scope="col">Motivo</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((l) => (
                  <tr key={l.linha}>
                    <td className="num">{l.linha}</td>
                    <td>
                      <span className="celula-principal">{l.nome || <em className="texto-suave">sem nome</em>}</span>
                      <span className="texto-suave">{l.cpf ? formatarDocumento(l.cpf) : 'sem CPF'}</span>
                    </td>
                    <td>
                      <ul className="motivos">
                        {l.motivos.map((m) => (
                          <li key={m}>{m}</li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Paginacao pagina={data.pagina} tamanho={data.tamanho} total={data.total} aoMudar={aoMudarPagina} />
        </>
      )}
    </>
  )
}

export function ImportacaoDetalhePage() {
  const id = Number(useParams().id)
  useTituloPagina(`Importação #${id}`)
  const { data: imp, isPending, isError, error, refetch } = useImportacao(id)
  const invalidar = useInvalidarAposImportacao()

  const statusAnterior = useRef<StatusImportacao | undefined>(undefined)
  useEffect(() => {
    const anterior = statusAnterior.current
    statusAnterior.current = imp?.status
    if ((anterior === 'PROCESSANDO' || anterior === 'PENDENTE') && imp && (imp.status === 'CONCLUIDA' || imp.status === 'FALHOU')) {
      void invalidar()
    }
  }, [imp, invalidar])

  if (!Number.isInteger(id) || id <= 0) return <NaoEncontradoPage />
  if (isError && error instanceof ApiError && error.status === 404) return <NaoEncontradoPage mensagem="Esta importação não existe." />

  const emAndamento = imp?.status === 'PROCESSANDO' || imp?.status === 'PENDENTE'

  return (
    <>
      <Cabecalho
        voltar={{ para: '/importacoes', rotulo: 'Importações' }}
        titulo={imp ? imp.arquivo : `Importação #${id}`}
        subtitulo={imp ? `Importação #${imp.id} · enviada em ${formatarDataHora(imp.criada_em)}` : undefined}
        acoes={
          imp && (
            <div className="cabecalho-status">
              <SeloStatus status={imp.status} />
              <ExcluirImportacao importacao={imp} />
            </div>
          )
        }
      />

      {isPending ? (
        <section className="painel">
          <Carregando linhas={3} />
        </section>
      ) : isError ? (
        <Erro erro={error} aoTentarDeNovo={() => refetch()} />
      ) : (
        <>
          <section className="painel" aria-live="polite">
            <ProgressoImportacao imp={imp} detalhado />
            {emAndamento && <p className="texto-suave">Atualiza sozinho a cada segundo. Pode sair desta tela: o processamento continua.</p>}
            {imp.status === 'CONCLUIDA' && <p className="texto-suave">Concluída em {formatarDataHora(imp.finalizada_em)}.</p>}
            {imp.status === 'FALHOU' && (
              <p className="campo-erro" role="alert">
                {imp.erro ?? 'O processamento foi interrompido.'} Envie o arquivo de novo: linhas já importadas não serão duplicadas.
              </p>
            )}
          </section>
          <LinhasDaImportacao imp={imp} emAndamento={emAndamento} />
        </>
      )}
    </>
  )
}
