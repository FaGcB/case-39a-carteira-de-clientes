import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes } from 'react'

interface Base {
  rotulo: string
  erro?: string
  dica?: ReactNode
  largura?: 'cheia' | 'media' | 'curta'
}

function Moldura({ id, rotulo, erro, dica, largura = 'media', children }: Base & { id: string; children: ReactNode }) {
  return (
    <div className={`campo campo-${largura}${erro ? ' com-erro' : ''}`}>
      <label htmlFor={id}>{rotulo}</label>
      {children}
      {erro ? (
        <p className="campo-erro" id={`${id}-erro`}>
          {erro}
        </p>
      ) : dica ? (
        <p className="campo-dica" id={`${id}-dica`}>
          {dica}
        </p>
      ) : null}
    </div>
  )
}

export function Campo({ rotulo, erro, dica, largura, ...input }: Base & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId()
  return (
    <Moldura id={id} rotulo={rotulo} erro={erro} dica={dica} largura={largura}>
      <input id={id} aria-invalid={Boolean(erro)} aria-describedby={erro ? `${id}-erro` : dica ? `${id}-dica` : undefined} {...input} />
    </Moldura>
  )
}

export function Selecao({
  rotulo,
  erro,
  dica,
  largura,
  opcoes,
  ...select
}: Base & SelectHTMLAttributes<HTMLSelectElement> & { opcoes: { valor: string; rotulo: string }[] }) {
  const id = useId()
  return (
    <Moldura id={id} rotulo={rotulo} erro={erro} dica={dica} largura={largura}>
      <select id={id} aria-invalid={Boolean(erro)} aria-describedby={erro ? `${id}-erro` : undefined} {...select}>
        {opcoes.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.rotulo}
          </option>
        ))}
      </select>
    </Moldura>
  )
}
