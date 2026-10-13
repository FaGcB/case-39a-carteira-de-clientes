import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../api/http'
import { useEmpresa, useVinculosEmpresa } from '../api/queries'
import { AvisoDeNavegacao, type EstadoNavegacao } from '../components/Aviso'
import { Atualizando, Carregando, Erro, Vazio } from '../components/Estados'
import { Icone } from '../components/Icone'
import { Cabecalho } from '../components/Layout'
import { Paginacao } from '../components/Paginacao'
import { formatarCnpj, formatarCpf, formatarData, formatarMoeda, formatarNumero } from '../lib/format'
import { inteiroPositivo, useCampoDaUrl, useParametrosUrl, useTituloPagina } from '../lib/hooks'
import { NaoEncontradoPage } from './NaoEncontradoPage'

const PADROES = { nome: '', pagina: '1' }

function ClientesVinculados({ empresaId, total }: { empresaId: number; total: number }) {
  const [p, definir] = useParametrosUrl(PADROES)
  const pagina = inteiroPositivo(p.pagina)
  const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useVinculosEmpresa(
    empresaId,
    pagina,
    p.nome.trim() || undefined,
  )
  const [nome, setNome] = useCampoDaUrl(p.nome, (v) => definir({ nome: v }, { substituir: true }))

  return (
    <section className="painel" aria-labelledby="titulo-vinculados">
      <div className="painel-topo">
        <h2 id="titulo-vinculados">Clientes vinculados</h2>
        <span className="texto-suave">{formatarNumero(total)}</span>
      </div>
      {total > 0 && (
        <form className="filtros" role="search" onSubmit={(e) => e.preventDefault()}>
          <div className="campo campo-media">
            <label htmlFor="filtro-vinculado">Buscar cliente nesta empresa</label>
            <input
              id="filtro-vinculado"
              type="search"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="Nome do cliente"
              autoComplete="off"
            />
          </div>
        </form>
      )}
      <Atualizando ativo={isFetching && isPlaceholderData} />
      {isPending ? (
        <Carregando linhas={6} />
      ) : isError ? (
        <Erro erro={error} aoTentarDeNovo={() => refetch()} />
      ) : data.total === 0 ? (
        p.nome ? (
          <Vazio titulo="Nenhum cliente desta empresa com esse nome." />
        ) : (
          <Vazio titulo="Nenhum cliente vinculado a esta empresa." />
        )
      ) : (
        <>
          <div className="tabela-rolagem">
            <table className={`tabela${isPlaceholderData ? ' esmaecida' : ''}`}>
              <thead>
                <tr>
                  <th scope="col">Cliente</th>
                  <th scope="col">Cargo</th>
                  <th scope="col" className="col-opcional">
                    Matrícula
                  </th>
                  <th scope="col" className="col-opcional">
                    Admissão
                  </th>
                  <th scope="col" className="num">
                    Salário bruto
                  </th>
                  <th scope="col" className="num">
                    Margem
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((v) => (
                  <tr key={v.id}>
                    <td>
                      <Link
                        to={`/clientes/${v.cliente.id}`}
                        state={{ cpf: v.cliente.cpf } satisfies EstadoNavegacao}
                        className="celula-principal"
                      >
                        {v.cliente.nome}
                      </Link>
                      <span className="texto-suave tabular">{formatarCpf(v.cliente.cpf)}</span>
                    </td>
                    <td>{v.cargo}</td>
                    <td className="tabular col-opcional">{v.matricula}</td>
                    <td className="tabular col-opcional">{formatarData(v.data_admissao)}</td>
                    <td className="num">{formatarMoeda(v.salario_bruto)}</td>
                    <td className="num">{formatarMoeda(v.margem_disponivel)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Paginacao pagina={data.pagina} tamanho={data.tamanho} total={data.total} aoMudar={(pg) => definir({ pagina: String(pg) })} />
        </>
      )}
    </section>
  )
}

export function EmpresaFichaPage() {
  const id = Number(useParams().id)
  const { data: empresa, isPending, isError, error, refetch } = useEmpresa(id)
  useTituloPagina(empresa?.nome_fantasia ?? 'Empresa')

  if (!Number.isInteger(id) || id <= 0) return <NaoEncontradoPage />
  if (isError && error instanceof ApiError && error.status === 404) return <NaoEncontradoPage mensagem="Esta empresa não existe." />

  return (
    <>
      <Cabecalho
        voltar={{ para: '/empresas', rotulo: 'Empresas' }}
        titulo={empresa?.nome_fantasia ?? (isPending ? <span className="esqueleto-linha titulo" /> : 'Empresa')}
        subtitulo={empresa && <span className="tabular">CNPJ {formatarCnpj(empresa.cnpj)}</span>}
        acoes={
          empresa && (
            <Link to={`/empresas/${empresa.id}/editar`} className="botao botao-secundario">
              <Icone nome="editar" tamanho={16} />
              Editar
            </Link>
          )
        }
      />
      <AvisoDeNavegacao />

      {isPending ? (
        <section className="painel">
          <Carregando linhas={3} />
        </section>
      ) : isError ? (
        <Erro erro={error} aoTentarDeNovo={() => refetch()} />
      ) : (
        <>
          <section className="painel" aria-label="Dados da empresa">
            <dl className="empresa-dados">
              <div className="largo">
                <dt>Razão social</dt>
                <dd>{empresa.razao_social}</dd>
              </div>
              <div>
                <dt>Setor</dt>
                <dd>{empresa.setor || '—'}</dd>
              </div>
              <div>
                <dt>Cidade</dt>
                <dd>
                  {empresa.cidade}/{empresa.uf}
                </dd>
              </div>
              <div>
                <dt>Clientes vinculados</dt>
                <dd className="tabular">{formatarNumero(empresa.total_vinculos)}</dd>
              </div>
              <div>
                <dt>Margem disponível somada</dt>
                <dd className="tabular">{formatarMoeda(empresa.margem_total)}</dd>
              </div>
            </dl>
          </section>
          <ClientesVinculados empresaId={empresa.id} total={empresa.total_vinculos} />
        </>
      )}
    </>
  )
}
