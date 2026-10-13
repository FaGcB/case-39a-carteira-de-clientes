import { Link } from 'react-router-dom'
import { useEmpresas } from '../api/queries'
import { AvisoDeNavegacao } from '../components/Aviso'
import { Atualizando, Carregando, Erro, Vazio } from '../components/Estados'
import { Cabecalho } from '../components/Layout'
import { Paginacao } from '../components/Paginacao'
import { formatarCnpj, formatarNumero } from '../lib/format'
import { inteiroPositivo, useCampoDaUrl, useParametrosUrl, useTituloPagina } from '../lib/hooks'

export function EmpresasPage() {
  useTituloPagina('Empresas')
  const [p, definir] = useParametrosUrl({ busca: '', pagina: '1' })
  const pagina = inteiroPositivo(p.pagina)
  const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useEmpresas(pagina, p.busca.trim() || undefined)

  const [texto, setTexto] = useCampoDaUrl(p.busca, (v) => definir({ busca: v }, { substituir: true }))

  return (
    <>
      <Cabecalho
        titulo="Empresas"
        subtitulo="Empregadores que aparecem nas planilhas. Corrija aqui nomes que chegaram com grafias diferentes."
      />
      <AvisoDeNavegacao />
      <section className="painel">
        <form className="filtros" role="search" onSubmit={(e) => e.preventDefault()}>
          <div className="campo campo-media">
            <label htmlFor="busca-empresa">Razão social, nome fantasia ou CNPJ</label>
            <input id="busca-empresa" type="search" value={texto} onChange={(e) => setTexto(e.target.value)} autoComplete="off" />
          </div>
        </form>
        <div className="resultado-total" aria-live="polite">
          {data && !isError && `${formatarNumero(data.total)} ${data.total === 1 ? 'empresa' : 'empresas'}`}
        </div>
        <Atualizando ativo={isFetching && isPlaceholderData} />
        {isPending ? (
          <Carregando linhas={6} />
        ) : isError ? (
          <Erro erro={error} aoTentarDeNovo={() => refetch()} />
        ) : data.total === 0 ? (
          p.busca ? (
            <Vazio titulo="Nenhuma empresa encontrada com essa busca." />
          ) : (
            <Vazio
              titulo="Nenhuma empresa cadastrada ainda."
              acao={
                <Link to="/importacoes" className="botao botao-primario">
                  Importar planilha
                </Link>
              }
            >
              As empresas são criadas a partir das planilhas importadas.
            </Vazio>
          )
        ) : (
          <>
            <div className="tabela-rolagem">
              <table className={`tabela${isPlaceholderData ? ' esmaecida' : ''}`}>
                <thead>
                  <tr>
                    <th scope="col">Empresa</th>
                    <th scope="col">CNPJ</th>
                    <th scope="col" className="col-opcional">
                      Setor
                    </th>
                    <th scope="col" className="col-opcional">
                      Cidade
                    </th>
                    <th scope="col" className="num">
                      Vínculos
                    </th>
                    <th scope="col">
                      <span className="sr-only">Ações</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((e) => (
                    <tr key={e.id}>
                      <td>
                        <Link to={`/empresas/${e.id}`} className="celula-principal">
                          {e.nome_fantasia}
                        </Link>
                        <span className="texto-suave">{e.razao_social}</span>
                      </td>
                      <td className="tabular">{formatarCnpj(e.cnpj)}</td>
                      <td className="col-opcional">{e.setor}</td>
                      <td className="col-opcional">
                        {e.cidade}/{e.uf}
                      </td>
                      <td className="num">
                        <Link to={`/empresas/${e.id}`} title="Ver clientes desta empresa">
                          {formatarNumero(e.total_vinculos)}
                        </Link>
                      </td>
                      <td className="acoes-linha">
                        <Link to={`/empresas/${e.id}/editar`} className="botao botao-fantasma botao-pequeno">
                          Editar
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Paginacao pagina={data.pagina} tamanho={data.tamanho} total={data.total} aoMudar={(pg) => definir({ pagina: String(pg) })} />
          </>
        )}
      </section>
    </>
  )
}
