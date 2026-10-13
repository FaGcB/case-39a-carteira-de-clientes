import type { ReactNode } from 'react'
import { mensagemDeErro } from '../lib/erros'
import { Icone } from './Icone'

export function Carregando({ linhas = 6, rotulo = 'Carregando…' }: { linhas?: number; rotulo?: string }) {
  return (
    <div className="esqueleto" role="status" aria-live="polite">
      <span className="sr-only">{rotulo}</span>
      {Array.from({ length: linhas }, (_, i) => (
        <div key={i} className="esqueleto-linha" style={{ width: `${92 - ((i * 13) % 30)}%` }} />
      ))}
    </div>
  )
}

export function Vazio({ titulo, children, acao }: { titulo: string; children?: ReactNode; acao?: ReactNode }) {
  return (
    <div className="estado estado-vazio">
      <p className="estado-titulo">{titulo}</p>
      {children && <p className="estado-texto">{children}</p>}
      {acao && <div className="estado-acao">{acao}</div>}
    </div>
  )
}

export function Erro({ erro, aoTentarDeNovo, compacto }: { erro: unknown; aoTentarDeNovo?: () => void; compacto?: boolean }) {
  return (
    <div className={`estado estado-erro${compacto ? ' compacto' : ''}`} role="alert">
      <span className="estado-icone">
        <Icone nome="alerta" />
      </span>
      <div>
        <p className="estado-titulo">{mensagemDeErro(erro)}</p>
        {aoTentarDeNovo && (
          <button type="button" className="botao botao-secundario botao-pequeno" onClick={aoTentarDeNovo}>
            <Icone nome="recarregar" tamanho={16} />
            Tentar de novo
          </button>
        )}
      </div>
    </div>
  )
}

export function Atualizando({ ativo }: { ativo: boolean }) {
  return <div className={`atualizando${ativo ? ' ativo' : ''}`} aria-hidden={!ativo} />
}
