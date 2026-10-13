import { useEffect, useId, useRef, type ReactNode } from 'react'

interface Props {
  aberto: boolean
  titulo: string
  children: ReactNode
  rotuloConfirmar: string
  perigoso?: boolean
  ocupado?: boolean
  confirmarBloqueado?: boolean
  aoConfirmar: () => void
  aoCancelar: () => void
}

export function DialogoConfirmacao({
  aberto,
  titulo,
  children,
  rotuloConfirmar,
  perigoso,
  ocupado,
  confirmarBloqueado,
  aoConfirmar,
  aoCancelar,
}: Props) {
  const ref = useRef<HTMLDialogElement>(null)
  const idTitulo = useId()
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (aberto && !d.open) d.showModal()
    if (!aberto && d.open) d.close()
  }, [aberto])

  return (
    <dialog
      ref={ref}
      className="dialogo"
      aria-labelledby={idTitulo}
      onCancel={(e) => {
        e.preventDefault()
        if (!ocupado) aoCancelar()
      }}
    >
      <h2 id={idTitulo} className="dialogo-titulo">
        {titulo}
      </h2>
      <div className="dialogo-corpo">{children}</div>
      <div className="dialogo-acoes">
        <button type="button" className="botao botao-secundario" onClick={aoCancelar} disabled={ocupado} autoFocus>
          Cancelar
        </button>
        <button
          type="button"
          className={`botao ${perigoso ? 'botao-perigo' : 'botao-primario'}`}
          onClick={aoConfirmar}
          disabled={ocupado || confirmarBloqueado}
        >
          {ocupado ? 'Aguarde…' : rotuloConfirmar}
        </button>
      </div>
    </dialog>
  )
}
