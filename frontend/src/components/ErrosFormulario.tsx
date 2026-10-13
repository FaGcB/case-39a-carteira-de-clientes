import { useEffect, useRef } from 'react'
import { Icone } from './Icone'

export function FaixaErros({ erro, porCampo, gerais }: { erro: unknown; porCampo: Record<string, string>; gerais: string[] }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (erro) ref.current?.focus()
  }, [erro])
  if (!erro) return null
  const qtdCampos = Object.keys(porCampo).length
  return (
    <div className="faixa-erro" role="alert" tabIndex={-1} ref={ref}>
      <Icone nome="alerta" tamanho={18} />
      <div>
        {qtdCampos > 0 && (
          <p>
            {qtdCampos === 1 ? 'Um campo precisa de correção.' : `${qtdCampos} campos precisam de correção.`} Veja as mensagens abaixo de
            cada um.
          </p>
        )}
        {gerais.map((g) => (
          <p key={g}>{g}</p>
        ))}
      </div>
    </div>
  )
}
