import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

export function useDebounce<T>(valor: T, ms = 300): T {
  const [atrasado, setAtrasado] = useState(valor)
  useEffect(() => {
    const t = window.setTimeout(() => setAtrasado(valor), ms)
    return () => window.clearTimeout(t)
  }, [valor, ms])
  return atrasado
}

export function useContagemRegressiva(segundos: number): number {
  const [fim] = useState(() => Date.now() + segundos * 1000)
  const [agora, setAgora] = useState(() => Date.now())
  const restante = Math.max(0, Math.ceil((fim - agora) / 1000))
  useEffect(() => {
    if (restante === 0) return
    const t = window.setInterval(() => setAgora(Date.now()), 250)
    return () => window.clearInterval(t)
  }, [restante])
  return restante
}

export function useCampoDaUrl(valorUrl: string, aoConfirmar: (v: string) => void, ms = 350) {
  const [texto, setTexto] = useState(valorUrl)
  const [urlAnterior, setUrlAnterior] = useState(valorUrl)
  if (valorUrl !== urlAnterior) {
    setUrlAnterior(valorUrl)
    setTexto(valorUrl)
  }
  const confirmar = useRef(aoConfirmar)
  useEffect(() => {
    confirmar.current = aoConfirmar
  })
  const atrasado = useDebounce(texto, ms)
  useEffect(() => {
    if (atrasado !== valorUrl && atrasado === texto) confirmar.current(atrasado)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [atrasado])
  return [texto, setTexto] as const
}

export function useParametrosUrl<T extends Record<string, string>>(padroes: T) {
  const [params, setParams] = useSearchParams()

  const valores = useMemo(() => {
    const v = { ...padroes }
    for (const k of Object.keys(padroes) as (keyof T)[]) {
      const lido = params.get(k as string)
      if (lido !== null) v[k] = lido as T[keyof T]
    }
    return v
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params])

  const definir = useCallback(
    (mudancas: Partial<T>, opcoes: { substituir?: boolean } = {}) => {
      setParams(
        (atual) => {
          const novo = new URLSearchParams(atual)
          for (const [k, v] of Object.entries(mudancas)) {
            if (v === undefined || v === '' || v === padroes[k]) novo.delete(k)
            else novo.set(k, v as string)
          }
          if (!('pagina' in mudancas)) novo.delete('pagina')
          return novo
        },
        { replace: opcoes.substituir ?? false },
      )
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [setParams],
  )

  return [valores, definir] as const
}

export function inteiroPositivo(s: string | undefined, padrao = 1): number {
  const n = Number(s)
  return Number.isInteger(n) && n > 0 ? n : padrao
}

export function useTituloPagina(titulo: string) {
  useEffect(() => {
    document.title = `${titulo} · 39A`
  }, [titulo])
}
