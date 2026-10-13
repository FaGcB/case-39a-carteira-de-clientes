import { Link } from 'react-router-dom'
import { useResumo } from '../api/queries'
import type { Resumo } from '../api/types'
import { Carregando, Erro } from '../components/Estados'
import { Cabecalho } from '../components/Layout'
import { ProgressoImportacao, SeloStatus } from '../components/StatusImportacao'
import { formatarDataHora, formatarNumero, formatarPercentual, plural } from '../lib/format'
import { useTituloPagina } from '../lib/hooks'

function VinculosPorEmpresa({ itens, total }: { itens: Resumo['vinculos_por_empresa']; total: number }) {
  if (itens.length === 0) return <p className="texto-suave">Nenhum vínculo na base ainda.</p>
  return (
    <ul className="participacao">
      {itens.map((i) => {
        const fracao = i.total / total
        return (
          <li key={i.empresa.id}>
            <div className="participacao-linha">
              <Link to={`/empresas/${i.empresa.id}`}>{i.empresa.nome_fantasia}</Link>
              <span className="tabular texto-suave">{plural(i.total, 'vínculo', 'vínculos')}</span>
              <span className="tabular participacao-pct">{formatarPercentual(fracao)}</span>
            </div>
            <div className="participacao-trilho" aria-hidden="true">
              <div style={{ width: `${fracao * 100}%` }} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

export function PainelPage() {
  useTituloPagina('Painel')
  const { data, isPending, isError, error, refetch } = useResumo()

  return (
    <>
      <Cabecalho titulo="Painel" subtitulo="Visão geral da base montada a partir das planilhas dos parceiros." />

      {isError ? (
        <Erro erro={error} aoTentarDeNovo={() => refetch()} />
      ) : (
        <>
          <section className="destaque" aria-label="Indicadores da base">
            <div className="destaque-principal">
              <span className="destaque-rotulo">Clientes na base</span>
              <span className="destaque-valor">
                {isPending ? <span className="esqueleto-linha curta" /> : formatarNumero(data.clientes)}
              </span>
              <div className="destaque-acoes">
                <Link to="/importacoes" className="botao botao-primario">
                  Importar planilha
                </Link>
                <Link to="/clientes" className="botao botao-escuro">
                  Ver clientes
                </Link>
              </div>
            </div>
            <dl className="destaque-numeros">
              {[
                { rotulo: 'Empresas', valor: data?.empresas, para: '/empresas' },
                { rotulo: 'Vínculos empregatícios', valor: data?.vinculos, para: '/clientes' },
                { rotulo: 'Linhas rejeitadas', valor: data?.linhas_invalidas, para: '/importacoes' },
              ].map((b) => (
                <div key={b.rotulo}>
                  <dt>{b.rotulo}</dt>
                  <dd>
                    <Link to={b.para}>{isPending ? '—' : formatarNumero(b.valor ?? 0)}</Link>
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <div className="painel-grade">
            <section className="painel">
              <div className="painel-topo">
                <div>
                  <h2>Vínculos por empresa</h2>
                  <p className="painel-sub">Participação de cada empresa na carteira</p>
                </div>
              </div>
              {isPending ? <Carregando linhas={5} /> : <VinculosPorEmpresa itens={data.vinculos_por_empresa} total={data.vinculos} />}
            </section>
            <section className="painel">
              <div className="painel-topo">
                <h2>Última importação</h2>
                <Link to="/importacoes" className="link-discreto">
                  Ver histórico
                </Link>
              </div>
              {isPending ? (
                <div className="esqueleto-linha" />
              ) : data.ultima_importacao ? (
                <Link to={`/importacoes/${data.ultima_importacao.id}`} className="ultima-importacao">
                  <div className="ultima-importacao-topo">
                    <span className="ultima-importacao-arquivo">{data.ultima_importacao.arquivo}</span>
                    <SeloStatus status={data.ultima_importacao.status} />
                  </div>
                  <ProgressoImportacao imp={data.ultima_importacao} />
                  <p className="texto-suave">
                    Enviada em {formatarDataHora(data.ultima_importacao.criada_em)} · {formatarNumero(data.ultima_importacao.importadas)}{' '}
                    importadas, {formatarNumero(data.ultima_importacao.invalidas)} rejeitadas
                  </p>
                </Link>
              ) : (
                <p className="texto-suave">Nenhuma planilha importada ainda.</p>
              )}
            </section>
          </div>
        </>
      )}
    </>
  )
}
