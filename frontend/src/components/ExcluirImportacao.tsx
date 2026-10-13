import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useExcluirImportacao, usePreviaExclusao } from '../api/queries'
import type { ExclusaoImportacao, Importacao } from '../api/types'
import { mensagemDeErro } from '../lib/erros'
import { formatarNumero, plural } from '../lib/format'
import type { EstadoNavegacao } from './Aviso'
import { DialogoConfirmacao } from './Dialogo'
import { Icone } from './Icone'

function Previa({ p }: { p: ExclusaoImportacao }) {
  const nada = p.vinculos_removidos === 0 && p.clientes_removidos === 0 && p.empresas_removidas === 0
  return (
    <div className="previa-exclusao">
      {nada ? (
        <p>Todos os dados desta planilha também vieram de outras importações. Nenhum cliente, empresa ou vínculo sai.</p>
      ) : (
        <>
          <p>Sai só o que existia apenas nesta planilha:</p>
          <dl>
            <div>
              <dt>Clientes removidos</dt>
              <dd>{formatarNumero(p.clientes_removidos)}</dd>
            </div>
            <div>
              <dt>Vínculos removidos</dt>
              <dd>{formatarNumero(p.vinculos_removidos)}</dd>
            </div>
            <div>
              <dt>Empresas removidas</dt>
              <dd>{formatarNumero(p.empresas_removidas)}</dd>
            </div>
            <div>
              <dt>Linhas rejeitadas</dt>
              <dd>{formatarNumero(p.linhas_rejeitadas_removidas)}</dd>
            </div>
          </dl>
        </>
      )}
      {p.clientes_mantidos > 0 && (
        <p className="texto-suave">
          {plural(p.clientes_mantidos, 'cliente desta planilha continua', 'clientes desta planilha continuam')} na base, porque também{' '}
          {p.clientes_mantidos === 1 ? 'veio' : 'vieram'} de outra importação.{' '}
          {p.clientes_mantidos === 1 ? 'Os dados dele ficam' : 'Os dados deles ficam'} como estão hoje.
        </p>
      )}
    </div>
  )
}

export function ExcluirImportacao({
  importacao,
  compacto,
  destino = '/importacoes',
}: {
  importacao: Pick<Importacao, 'id' | 'arquivo' | 'status'>
  compacto?: boolean
  destino?: string
}) {
  const [aberto, setAberto] = useState(false)
  const previa = usePreviaExclusao(importacao.id, aberto)
  const excluir = useExcluirImportacao()
  const navegar = useNavigate()
  const emAndamento = importacao.status === 'PENDENTE' || importacao.status === 'PROCESSANDO'

  const fechar = () => {
    setAberto(false)
    excluir.reset()
  }

  return (
    <>
      <button
        type="button"
        className={`botao botao-perigo-suave botao-pequeno${compacto ? ' botao-icone' : ''}`}
        onClick={() => setAberto(true)}
        disabled={emAndamento}
        title={emAndamento ? 'Espere a importação terminar para apagar' : `Apagar a importação #${importacao.id}`}
        aria-label={compacto ? `Apagar a importação #${importacao.id} (${importacao.arquivo})` : undefined}
      >
        <Icone nome="lixo" tamanho={16} />
        {!compacto && 'Apagar importação'}
      </button>
      <DialogoConfirmacao
        aberto={aberto}
        titulo={`Apagar a importação #${importacao.id}?`}
        rotuloConfirmar="Apagar importação"
        perigoso
        ocupado={excluir.isPending}
        confirmarBloqueado={!previa.data}
        aoCancelar={fechar}
        aoConfirmar={() =>
          excluir.mutate(importacao.id, {
            onSuccess: (r) => {
              fechar()
              navegar(destino, {
                replace: true,
                state: {
                  aviso: `Importação #${r.importacao_id} apagada: ${plural(r.clientes_removidos, 'cliente removido', 'clientes removidos')}, ${plural(r.clientes_mantidos, 'mantido', 'mantidos')}.`,
                } satisfies EstadoNavegacao,
              })
            },
          })
        }
      >
        <p>
          Arquivo <strong>{importacao.arquivo}</strong>. Não dá para desfazer.
        </p>
        {previa.isPending ? (
          <p className="texto-suave" role="status">
            Calculando o que sai…
          </p>
        ) : previa.isError ? (
          <p className="campo-erro" role="alert">
            {mensagemDeErro(previa.error)}
          </p>
        ) : (
          <Previa p={previa.data} />
        )}
        {excluir.isError && (
          <p className="campo-erro" role="alert">
            {mensagemDeErro(excluir.error)}
          </p>
        )}
      </DialogoConfirmacao>
    </>
  )
}
