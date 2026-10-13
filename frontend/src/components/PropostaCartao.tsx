import { ApiError } from '../api/http'
import { useProposta } from '../api/queries'
import type { Vinculo } from '../api/types'
import { formatarCpf, formatarDataHora, formatarMoeda, formatarPercentual } from '../lib/format'
import { useContagemRegressiva } from '../lib/hooks'
import { avaliarMargem, calcularParcela } from '../lib/parcela'
import { mensagemDeErro } from '../lib/erros'
import { Icone } from './Icone'

function LimiteAtingido({ segundos, aoTentar }: { segundos: number | null; aoTentar: () => void }) {
  const restante = useContagemRegressiva(segundos ?? 60)
  return (
    <div className="proposta-aviso" role="alert">
      <p className="proposta-aviso-titulo">O motor de crédito está no limite de consultas.</p>
      <p>
        Ele aceita até 10 consultas por minuto.{' '}
        {restante > 0 ? `Você pode consultar de novo em ${restante}s.` : 'Já pode consultar de novo.'}
      </p>
      <button type="button" className="botao botao-claro botao-pequeno" onClick={aoTentar} disabled={restante > 0}>
        {restante > 0 ? `Consultar em ${restante}s` : 'Consultar de novo'}
      </button>
    </div>
  )
}

export function PropostaCartao({ cpf, vinculos }: { cpf: string | undefined; vinculos: Vinculo[] | undefined }) {
  const { data, isPending, isFetching, isError, error, refetch, errorUpdatedAt } = useProposta(cpf)

  let corpo
  if (isPending || (isFetching && isError)) {
    corpo = (
      <div className="proposta-carregando" role="status">
        <span className="girador" aria-hidden="true" />
        Consultando o motor de crédito…
      </div>
    )
  } else if (isError && error instanceof ApiError && error.status === 429) {
    corpo = <LimiteAtingido key={errorUpdatedAt} segundos={error.retryAfter} aoTentar={() => refetch()} />
  } else if (isError) {
    corpo = (
      <div className="proposta-aviso" role="alert">
        <p className="proposta-aviso-titulo">Não foi possível buscar a proposta.</p>
        <p>{mensagemDeErro(error)}</p>
        <button type="button" className="botao botao-claro botao-pequeno" onClick={() => refetch()}>
          Consultar de novo
        </button>
      </div>
    )
  } else {
    const parcela = calcularParcela(data.valor, data.taxa_mensal, data.parcelas)
    const margem = vinculos
      ? avaliarMargem(
          parcela,
          vinculos.map((v) => v.margem_disponivel),
        )
      : null
    const uso = margem?.margemReferencia ? Math.min(100, (parcela / margem.margemReferencia) * 100) : 0
    corpo = (
      <>
        <div className="proposta-cartao">
          <div className="proposta-cartao-topo">
            <span>Valor liberado</span>
            <span className="proposta-cartao-marca">Consignado</span>
          </div>
          <p className="proposta-cartao-valor">{formatarMoeda(data.valor)}</p>
          <div className="proposta-cartao-rodape tabular">
            <span>CPF {formatarCpf(data.cpf)}</span>
            <span>{data.parcelas}x</span>
          </div>
        </div>

        <dl className="proposta-valores">
          <div>
            <dt>Parcela</dt>
            <dd>
              {data.parcelas} × {formatarMoeda(parcela)}
            </dd>
          </div>
          <div>
            <dt>Taxa</dt>
            <dd>{formatarPercentual(data.taxa_mensal)} a.m.</dd>
          </div>
        </dl>

        {margem === null ? (
          <p className="proposta-margem-texto">Carregando vínculos para comparar com a margem…</p>
        ) : margem.situacao === 'sem-vinculo' ? (
          <p className="proposta-margem-texto">Cliente sem vínculo ativo: não há margem para comparar.</p>
        ) : (
          <div className={`proposta-margem ${margem.situacao}`}>
            <div className="proposta-margem-topo">
              <span>Comprometimento da margem</span>
              <span className="tabular">
                {formatarMoeda(parcela)} de {formatarMoeda(margem.margemReferencia!)}
              </span>
            </div>
            <div className="proposta-margem-trilho" aria-hidden="true">
              <div style={{ width: `${uso}%` }} />
            </div>
            {margem.situacao === 'excede' ? (
              <p className="proposta-margem-alerta" role="alert">
                <Icone nome="alerta" tamanho={16} />A parcela passa a maior margem disponível em{' '}
                {formatarMoeda(parcela - margem.margemReferencia!)}. Esta proposta não pode ser averbada como está.
              </p>
            ) : (
              <p className="proposta-margem-texto">
                <Icone nome="ok" tamanho={16} />
                Cabe na margem do vínculo com maior folga.
              </p>
            )}
          </div>
        )}
        <p className="proposta-rodape">Gerada em {formatarDataHora(data.gerado_em)}</p>
      </>
    )
  }

  return (
    <section className="proposta" aria-labelledby="titulo-proposta" aria-busy={isFetching}>
      <div className="proposta-topo">
        <h2 id="titulo-proposta">Proposta de crédito</h2>
        <span className="proposta-origem">Motor de crédito</span>
      </div>
      {corpo}
    </section>
  )
}
