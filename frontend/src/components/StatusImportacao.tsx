import type { Importacao, StatusImportacao } from '../api/types'
import { formatarNumero } from '../lib/format'

const rotulos: Record<StatusImportacao, string> = {
  PENDENTE: 'Na fila',
  PROCESSANDO: 'Processando',
  CONCLUIDA: 'Concluída',
  FALHOU: 'Falhou',
}

export function SeloStatus({ status }: { status: StatusImportacao }) {
  return <span className={`selo selo-${status.toLowerCase()}`}>{rotulos[status]}</span>
}

export function ProgressoImportacao({ imp, detalhado }: { imp: Importacao; detalhado?: boolean }) {
  const total = imp.total_linhas ?? 0
  const pct = total > 0 ? Math.min(100, (imp.processadas / total) * 100) : 0
  const pctImportadas = total > 0 ? (imp.importadas / total) * 100 : 0
  const pctInvalidas = total > 0 ? (imp.invalidas / total) * 100 : 0
  return (
    <div className="progresso">
      <div
        className="progresso-trilho"
        role="progressbar"
        aria-label="Linhas processadas"
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={imp.processadas}
        aria-valuetext={`${imp.processadas} de ${total} linhas`}
      >
        <div className="progresso-ok" style={{ width: `${pctImportadas}%` }} />
        <div className="progresso-invalidas" style={{ width: `${pctInvalidas}%` }} />
      </div>
      {detalhado && (
        <dl className="progresso-numeros">
          <div>
            <dt>Total de linhas</dt>
            <dd>{total ? formatarNumero(total) : '—'}</dd>
          </div>
          <div>
            <dt>Processadas</dt>
            <dd>
              {formatarNumero(imp.processadas)}
              <small> {Math.floor(pct)}%</small>
            </dd>
          </div>
          <div>
            <dt>
              <i className="ponto ponto-ok" /> Importadas
            </dt>
            <dd>{formatarNumero(imp.importadas)}</dd>
          </div>
          <div>
            <dt>
              <i className="ponto ponto-invalidas" /> Inválidas
            </dt>
            <dd>{formatarNumero(imp.invalidas)}</dd>
          </div>
        </dl>
      )}
    </div>
  )
}
