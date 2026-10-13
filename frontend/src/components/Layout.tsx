import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { somenteDigitos } from '../lib/format'
import { Icone, type NomeIcone } from './Icone'

const itens: { para: string; rotulo: string; icone: NomeIcone; fim?: boolean }[] = [
  { para: '/', rotulo: 'Painel', icone: 'painel', fim: true },
  { para: '/clientes', rotulo: 'Clientes', icone: 'clientes' },
  { para: '/empresas', rotulo: 'Empresas', icone: 'empresas' },
  { para: '/importacoes', rotulo: 'Importações', icone: 'importacoes' },
]

function BuscaGlobal() {
  const [termo, setTermo] = useState('')
  const navegar = useNavigate()
  const enviar = (e: FormEvent) => {
    e.preventDefault()
    const t = termo.trim()
    if (!t) return
    const digitos = somenteDigitos(t)
    const ehDocumento = digitos.length >= 3 && digitos.length >= t.replace(/[\s.\-/]/g, '').length
    navegar(`/clientes?${new URLSearchParams(ehDocumento ? { documento: t } : { nome: t })}`)
    setTermo('')
  }
  return (
    <form className="busca-global" role="search" onSubmit={enviar}>
      <Icone nome="busca" tamanho={18} />
      <label htmlFor="busca-global" className="sr-only">
        Buscar cliente por nome, CPF ou CNPJ
      </label>
      <input
        id="busca-global"
        type="search"
        placeholder="Nome, CPF ou CNPJ"
        value={termo}
        onChange={(e) => setTermo(e.target.value)}
        autoComplete="off"
      />
    </form>
  )
}

export function Layout() {
  const [menuAberto, setMenuAberto] = useState(false)
  const { pathname } = useLocation()
  const [caminhoAnterior, setCaminhoAnterior] = useState(pathname)
  if (pathname !== caminhoAnterior) {
    setCaminhoAnterior(pathname)
    setMenuAberto(false)
  }

  return (
    <div className="app">
      <a className="pular" href="#conteudo">
        Ir para o conteúdo
      </a>
      <aside className={`lateral${menuAberto ? ' aberta' : ''}`} aria-label="Navegação principal">
        <div className="marca">
          <img className="marca-logo" src="/logo-39a-branco.png" alt="" width="28" height="28" />
          <span className="marca-nome">
            39A
            <small>Carteira de clientes</small>
          </span>
          <button type="button" className="lateral-fechar" onClick={() => setMenuAberto(false)} aria-label="Fechar menu">
            <Icone nome="fechar" />
          </button>
        </div>
        <nav>
          <ul className="navegacao">
            {itens.map((i) => (
              <li key={i.para}>
                <NavLink to={i.para} end={i.fim} className={({ isActive }) => `navegacao-item${isActive ? ' ativo' : ''}`}>
                  <Icone nome={i.icone} />
                  {i.rotulo}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="lateral-rodape">
          <p className="lateral-rodape-titulo">Nova planilha de parceiro?</p>
          <p>Importe o arquivo e acompanhe o resultado linha a linha.</p>
          <Link to="/importacoes" className="botao botao-primario botao-pequeno">
            Importar planilha
          </Link>
        </div>
      </aside>
      {menuAberto && <div className="veu" onClick={() => setMenuAberto(false)} aria-hidden="true" />}

      <div className="principal">
        <header className="topo">
          <button type="button" className="topo-menu" onClick={() => setMenuAberto(true)} aria-label="Abrir menu">
            <Icone nome="menu" />
          </button>
          <BuscaGlobal />
          <div className="topo-usuario" aria-label="Usuário conectado">
            <span className="avatar" aria-hidden="true">
              TC
            </span>
            <span className="topo-usuario-nome">
              Time comercial
              <small>Crédito consignado</small>
            </span>
          </div>
        </header>
        <main id="conteudo" className="conteudo" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export function Cabecalho({
  titulo,
  subtitulo,
  acoes,
  voltar,
}: {
  titulo: ReactNode
  subtitulo?: ReactNode
  acoes?: ReactNode
  voltar?: { para: string; rotulo: string }
}) {
  return (
    <div className="cabecalho">
      <div>
        {voltar && (
          <Link className="voltar" to={voltar.para}>
            <Icone nome="voltar" tamanho={16} />
            {voltar.rotulo}
          </Link>
        )}
        <h1>{titulo}</h1>
        {subtitulo && <p className="cabecalho-sub">{subtitulo}</p>}
      </div>
      {acoes && <div className="cabecalho-acoes">{acoes}</div>}
    </div>
  )
}
