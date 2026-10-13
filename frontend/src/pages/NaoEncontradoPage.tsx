import { Link, isRouteErrorResponse, useRouteError } from 'react-router-dom'
import { Vazio } from '../components/Estados'
import { useTituloPagina } from '../lib/hooks'

export function NaoEncontradoPage({ mensagem = 'Esta página não existe.' }: { mensagem?: string }) {
  useTituloPagina('Não encontrado')
  return (
    <section className="painel">
      <Vazio
        titulo={mensagem}
        acao={
          <Link to="/clientes" className="botao botao-secundario">
            Ir para clientes
          </Link>
        }
      >
        Confira o endereço ou volte para a lista.
      </Vazio>
    </section>
  )
}

export function ErroInesperadoPage() {
  const erro = useRouteError()
  if (isRouteErrorResponse(erro) && erro.status === 404) return <NaoEncontradoPage />
  console.error(erro)
  return (
    <div className="erro-geral">
      <h1>Algo deu errado nesta tela.</h1>
      <p>Recarregue a página. Se o problema continuar, avise o time de tecnologia.</p>
      <button type="button" className="botao botao-primario" onClick={() => window.location.reload()}>
        Recarregar página
      </button>
    </div>
  )
}
