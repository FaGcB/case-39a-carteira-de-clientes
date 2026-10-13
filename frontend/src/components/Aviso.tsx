import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Icone } from './Icone'

export interface EstadoNavegacao {
  aviso?: string
  cpf?: string
}

export function AvisoDeNavegacao() {
  const local = useLocation()
  const navegar = useNavigate()
  const estado = local.state as EstadoNavegacao | null
  const recebido = estado?.aviso
  const [aviso, setAviso] = useState(recebido)
  const [ultimoRecebido, setUltimoRecebido] = useState(recebido)
  if (recebido !== ultimoRecebido) {
    setUltimoRecebido(recebido)
    if (recebido) setAviso(recebido)
  }

  useEffect(() => {
    if (!recebido) return
    const resto: EstadoNavegacao = { ...estado }
    delete resto.aviso
    navegar(local.pathname + local.search, { replace: true, state: Object.keys(resto).length ? resto : null })
  }, [recebido]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!aviso) return
    const t = window.setTimeout(() => setAviso(undefined), 5000)
    return () => window.clearTimeout(t)
  }, [aviso])

  if (!aviso) return null
  return (
    <div className="aviso" role="status">
      <Icone nome="ok" tamanho={18} />
      {aviso}
      <button type="button" className="aviso-fechar" onClick={() => setAviso(undefined)} aria-label="Fechar aviso">
        <Icone nome="fechar" tamanho={16} />
      </button>
    </div>
  )
}
