import { useRef, useState, type DragEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/http'
import { useEnviarImportacao, useImportacoes } from '../api/queries'
import { AvisoDeNavegacao } from '../components/Aviso'
import { ExcluirImportacao } from '../components/ExcluirImportacao'
import { Atualizando, Carregando, Erro, Vazio } from '../components/Estados'
import { Icone } from '../components/Icone'
import { Cabecalho } from '../components/Layout'
import { Paginacao } from '../components/Paginacao'
import { ProgressoImportacao, SeloStatus } from '../components/StatusImportacao'
import { formatarDataHora, formatarNumero } from '../lib/format'
import { inteiroPositivo, useParametrosUrl, useTituloPagina } from '../lib/hooks'

function EnvioDeArquivo() {
  const enviar = useEnviarImportacao()
  const navegar = useNavigate()
  const input = useRef<HTMLInputElement>(null)
  const [arrastando, setArrastando] = useState(false)

  const iniciar = (arquivo: File | undefined) => {
    if (!arquivo || enviar.isPending) return
    enviar.mutate(arquivo, {
      onSuccess: (imp) => navegar(`/importacoes/${imp.id}`),
    })
  }

  const soltar = (e: DragEvent) => {
    e.preventDefault()
    setArrastando(false)
    iniciar(e.dataTransfer.files[0])
  }

  const erro = enviar.error
  const mensagemErro = erro instanceof ApiError ? (erro.erros.arquivo ?? erro.message) : erro ? 'Não foi possível enviar o arquivo.' : null

  return (
    <section className="painel">
      <div
        className={`envio${arrastando ? ' arrastando' : ''}${enviar.isPending ? ' enviando' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setArrastando(true)
        }}
        onDragLeave={() => setArrastando(false)}
        onDrop={soltar}
      >
        <span className="envio-icone">
          <Icone nome="arquivo" tamanho={28} />
        </span>
        <div className="envio-texto">
          <p className="envio-titulo">{enviar.isPending ? 'Enviando arquivo…' : 'Arraste a planilha do parceiro para cá'}</p>
          <p className="texto-suave">
            Aceita .xlsx ou .csv separado por ponto e vírgula. O processamento continua mesmo se você sair desta tela.
          </p>
        </div>
        <button type="button" className="botao botao-primario" onClick={() => input.current?.click()} disabled={enviar.isPending}>
          Escolher arquivo
        </button>
        <input
          ref={input}
          type="file"
          accept=".xlsx,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
          className="sr-only"
          tabIndex={-1}
          aria-hidden="true"
          onChange={(e) => {
            iniciar(e.target.files?.[0])
            e.target.value = ''
          }}
        />
      </div>
      {mensagemErro && (
        <p className="campo-erro" role="alert">
          {mensagemErro}
        </p>
      )}
    </section>
  )
}

export function ImportacoesPage() {
  useTituloPagina('Importações')
  const [params, definir] = useParametrosUrl({ pagina: '1' })
  const pagina = inteiroPositivo(params.pagina)
  const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useImportacoes(pagina)

  return (
    <>
      <Cabecalho titulo="Importações" subtitulo="Envie as planilhas dos parceiros e acompanhe o resultado de cada carga." />
      <AvisoDeNavegacao />
      <EnvioDeArquivo />

      <section className="painel">
        <div className="painel-topo">
          <h2>Histórico</h2>
        </div>
        <Atualizando ativo={isFetching && isPlaceholderData} />
        {isPending ? (
          <Carregando linhas={4} />
        ) : isError ? (
          <Erro erro={error} aoTentarDeNovo={() => refetch()} />
        ) : data.total === 0 ? (
          <Vazio titulo="Nenhuma planilha importada ainda.">Envie o primeiro arquivo acima para montar a base de clientes.</Vazio>
        ) : (
          <>
            <div className="tabela-rolagem">
              <table className="tabela">
                <thead>
                  <tr>
                    <th scope="col">Arquivo</th>
                    <th scope="col">Enviada em</th>
                    <th scope="col">Situação</th>
                    <th scope="col" className="num">
                      Importadas
                    </th>
                    <th scope="col" className="num">
                      Rejeitadas
                    </th>
                    <th scope="col">
                      <span className="sr-only">Ações</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((imp) => (
                    <tr key={imp.id}>
                      <td>
                        <Link to={`/importacoes/${imp.id}`} className="link-linha">
                          <span className="arquivo-nome">{imp.arquivo}</span>
                          <span className="texto-suave">#{imp.id}</span>
                        </Link>
                        {(imp.status === 'PROCESSANDO' || imp.status === 'PENDENTE') && <ProgressoImportacao imp={imp} />}
                      </td>
                      <td>{formatarDataHora(imp.criada_em)}</td>
                      <td>
                        <SeloStatus status={imp.status} />
                      </td>
                      <td className="num">
                        {imp.importadas > 0 ? (
                          <Link to={`/importacoes/${imp.id}?aba=aceitas`} aria-label={`${imp.importadas} linhas aceitas de ${imp.arquivo}`}>
                            {formatarNumero(imp.importadas)}
                          </Link>
                        ) : (
                          '0'
                        )}
                      </td>
                      <td className="num">
                        {imp.invalidas > 0 ? (
                          <Link
                            to={`/importacoes/${imp.id}?aba=rejeitadas`}
                            aria-label={`${imp.invalidas} linhas rejeitadas de ${imp.arquivo}`}
                          >
                            {formatarNumero(imp.invalidas)}
                          </Link>
                        ) : (
                          '0'
                        )}
                      </td>
                      <td className="acoes-linha">
                        <ExcluirImportacao importacao={imp} compacto />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Paginacao pagina={data.pagina} tamanho={data.tamanho} total={data.total} aoMudar={(p) => definir({ pagina: String(p) })} />
          </>
        )}
      </section>
    </>
  )
}
