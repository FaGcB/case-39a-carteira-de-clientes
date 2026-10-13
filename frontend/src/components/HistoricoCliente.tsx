import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useHistoricoCliente } from '../api/queries'
import type { Alteracao } from '../api/types'
import { formatarDataHora } from '../lib/format'
import { formatarValorHistorico } from '../lib/historico'
import { Carregando, Erro } from './Estados'
import { Paginacao } from './Paginacao'

function Titulo({ a }: { a: Alteracao }) {
  if (a.origem === 'EDICAO') return <>Edição manual</>
  const texto = a.acao === 'CRIACAO' ? `Cliente criado · ${a.descricao}` : a.descricao
  if (a.importacao_id === null)
    return (
      <>
        {texto} <span className="etiqueta-suave">importação apagada</span>
      </>
    )
  return <Link to={`/importacoes/${a.importacao_id}`}>{texto}</Link>
}

function Entrada({ a }: { a: Alteracao }) {
  return (
    <li className={`historico-item historico-${a.origem.toLowerCase()}`}>
      <div className="historico-topo">
        <strong>
          <Titulo a={a} />
        </strong>
        <time className="texto-suave tabular" dateTime={a.criado_em}>
          {formatarDataHora(a.criado_em)}
        </time>
      </div>
      {a.mudancas.length > 0 && (
        <ul className="historico-mudancas">
          {a.mudancas.map((m, i) => (
            <li key={i}>
              <span className="historico-rotulo">
                {m.rotulo}
                {m.contexto && <span className="texto-suave"> · {m.contexto}</span>}
              </span>
              {m.campo === 'vinculo' ? (
                <span className="historico-novo">{m.depois}</span>
              ) : (
                <span className="historico-valores">
                  <s className="historico-antes">{formatarValorHistorico(m.campo, m.antes)}</s>
                  <span aria-hidden="true">→</span>
                  <span className="sr-only">passou para</span>
                  <span className="historico-depois">{formatarValorHistorico(m.campo, m.depois)}</span>
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </li>
  )
}

export function HistoricoCliente({ clienteId }: { clienteId: number }) {
  const [pagina, setPagina] = useState(1)
  const { data, isPending, isError, error, refetch } = useHistoricoCliente(clienteId, pagina)

  return (
    <section className="painel" aria-labelledby="titulo-historico">
      <div className="painel-topo">
        <h2 id="titulo-historico">Histórico de alterações</h2>
        {data && <span className="texto-suave">{data.total}</span>}
      </div>
      {isPending ? (
        <Carregando linhas={3} rotulo="Carregando histórico…" />
      ) : isError ? (
        <Erro erro={error} aoTentarDeNovo={() => refetch()} compacto />
      ) : data.items.length === 0 ? (
        <p className="texto-suave">Nenhuma alteração registrada.</p>
      ) : (
        <>
          <ol className="historico">
            {data.items.map((a) => (
              <Entrada key={a.id} a={a} />
            ))}
          </ol>
          {data.total > data.tamanho && <Paginacao pagina={pagina} tamanho={data.tamanho} total={data.total} aoMudar={setPagina} />}
        </>
      )}
    </section>
  )
}
