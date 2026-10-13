import { formatarNumero } from '../lib/format'

interface Props {
  pagina: number
  tamanho: number
  total: number
  aoMudar: (pagina: number) => void
}

export function Paginacao({ pagina, tamanho, total, aoMudar }: Props) {
  const ultima = Math.max(1, Math.ceil(total / tamanho))
  if (total === 0) return null
  const inicio = (pagina - 1) * tamanho + 1
  const fim = Math.min(total, pagina * tamanho)
  return (
    <nav className="paginacao" aria-label="Paginação">
      <span className="paginacao-info">
        {formatarNumero(inicio)}–{formatarNumero(fim)} de {formatarNumero(total)}
      </span>
      <div className="paginacao-botoes">
        <button type="button" className="botao botao-secundario botao-pequeno" disabled={pagina <= 1} onClick={() => aoMudar(pagina - 1)}>
          Anterior
        </button>
        <span className="paginacao-pagina" aria-current="page">
          Página {pagina} de {ultima}
        </span>
        <button
          type="button"
          className="botao botao-secundario botao-pequeno"
          disabled={pagina >= ultima}
          onClick={() => aoMudar(pagina + 1)}
        >
          Próxima
        </button>
      </div>
    </nav>
  )
}
