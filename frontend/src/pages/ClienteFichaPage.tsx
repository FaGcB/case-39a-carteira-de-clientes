import { useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/http'
import { useCliente, useExcluirCliente } from '../api/queries'
import type { Cliente } from '../api/types'
import { AvisoDeNavegacao, type EstadoNavegacao } from '../components/Aviso'
import { DialogoConfirmacao } from '../components/Dialogo'
import { Carregando, Erro } from '../components/Estados'
import { mensagemDeErro } from '../lib/erros'
import { HistoricoCliente } from '../components/HistoricoCliente'
import { Icone } from '../components/Icone'
import { Cabecalho } from '../components/Layout'
import { PropostaCartao } from '../components/PropostaCartao'
import {
  calcularIdade,
  formatarCep,
  formatarCnpj,
  formatarCpf,
  formatarData,
  formatarDataHora,
  formatarEstadoCivil,
  formatarMoeda,
  formatarTelefone,
} from '../lib/format'
import { useTituloPagina } from '../lib/hooks'
import { NaoEncontradoPage } from './NaoEncontradoPage'

const SEXO = { F: 'Feminino', M: 'Masculino' } as const

function DadosCadastrais({ c }: { c: Cliente }) {
  const e = c.endereco
  return (
    <section className="painel" aria-labelledby="titulo-dados">
      <div className="painel-topo">
        <h2 id="titulo-dados">Dados cadastrais</h2>
      </div>
      <dl className="ficha-dados">
        <div>
          <dt>CPF</dt>
          <dd className="tabular">{formatarCpf(c.cpf)}</dd>
        </div>
        <div>
          <dt>Nascimento</dt>
          <dd>
            {formatarData(c.data_nascimento)}
            <span className="texto-suave"> · {calcularIdade(c.data_nascimento)} anos</span>
          </dd>
        </div>
        <div>
          <dt>Sexo</dt>
          <dd>{c.sexo ? SEXO[c.sexo] : '—'}</dd>
        </div>
        <div>
          <dt>Estado civil</dt>
          <dd>{formatarEstadoCivil(c.estado_civil)}</dd>
        </div>
        <div>
          <dt>Telefone</dt>
          <dd className="tabular">{formatarTelefone(c.telefone)}</dd>
        </div>
        <div className="largo">
          <dt>E-mail</dt>
          <dd>{c.email ?? '—'}</dd>
        </div>
      </dl>
      <h3 className="subtitulo-secao">Endereço</h3>
      <address className="ficha-endereco">
        {e.logradouro}, {e.numero}
        {e.complemento ? ` — ${e.complemento}` : ''}
        <br />
        {e.bairro} · {e.cidade}/{e.uf}
        <br />
        <span className="tabular">CEP {formatarCep(e.cep)}</span>
      </address>
    </section>
  )
}

function Vinculos({ c }: { c: Cliente }) {
  return (
    <section className="painel" aria-labelledby="titulo-vinculos">
      <div className="painel-topo">
        <h2 id="titulo-vinculos">Vínculos empregatícios</h2>
        <span className="texto-suave">{c.vinculos.length}</span>
      </div>
      {c.vinculos.length === 0 ? (
        <p className="texto-suave">Nenhum vínculo registrado para este cliente.</p>
      ) : (
        <div className="tabela-rolagem">
          <table className="tabela">
            <thead>
              <tr>
                <th scope="col">Empresa</th>
                <th scope="col">Cargo</th>
                <th scope="col">Matrícula</th>
                <th scope="col">Admissão</th>
                <th scope="col" className="num">
                  Salário bruto
                </th>
                <th scope="col" className="num">
                  Margem
                </th>
              </tr>
            </thead>
            <tbody>
              {c.vinculos.map((v) => (
                <tr key={v.id}>
                  <td>
                    <Link to={`/empresas/${v.empresa.id}`} className="celula-principal link-linha" title={v.empresa.razao_social}>
                      {v.empresa.nome_fantasia}
                    </Link>
                    <span className="texto-suave tabular">{formatarCnpj(v.empresa.cnpj)}</span>
                  </td>
                  <td>{v.cargo}</td>
                  <td className="tabular">{v.matricula}</td>
                  <td className="tabular">{formatarData(v.data_admissao)}</td>
                  <td className="num">{formatarMoeda(v.salario_bruto)}</td>
                  <td className="num">{formatarMoeda(v.margem_disponivel)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export function ClienteFichaPage() {
  const id = Number(useParams().id)
  const local = useLocation()
  const navegar = useNavigate()
  const { data: cliente, isPending, isError, error, refetch } = useCliente(id)
  const excluir = useExcluirCliente()
  const [confirmando, setConfirmando] = useState(false)
  useTituloPagina(cliente?.nome ?? 'Ficha do cliente')

  const cpf = cliente?.cpf ?? (local.state as EstadoNavegacao | null)?.cpf

  if (!Number.isInteger(id) || id <= 0) return <NaoEncontradoPage />
  if (isError && error instanceof ApiError && error.status === 404)
    return <NaoEncontradoPage mensagem="Este cliente não existe ou foi excluído." />

  return (
    <>
      <Cabecalho
        voltar={{ para: '/clientes', rotulo: 'Clientes' }}
        titulo={cliente?.nome ?? (isPending ? <span className="esqueleto-linha titulo" /> : 'Ficha do cliente')}
        subtitulo={cliente && <span className="tabular">CPF {formatarCpf(cliente.cpf)}</span>}
        acoes={
          cliente && (
            <>
              <Link to={`/clientes/${cliente.id}/editar`} className="botao botao-secundario">
                <Icone nome="editar" tamanho={16} />
                Editar
              </Link>
              <button type="button" className="botao botao-perigo-suave" onClick={() => setConfirmando(true)}>
                <Icone nome="lixo" tamanho={16} />
                Excluir
              </button>
            </>
          )
        }
      />
      <AvisoDeNavegacao />

      <div className="ficha-grade">
        <div className="ficha-coluna">
          {isPending ? (
            <section className="painel">
              <Carregando linhas={7} rotulo="Carregando ficha…" />
            </section>
          ) : isError ? (
            <Erro erro={error} aoTentarDeNovo={() => refetch()} />
          ) : (
            <DadosCadastrais c={cliente} />
          )}
        </div>
        <PropostaCartao cpf={cpf} vinculos={cliente?.vinculos} />
      </div>

      {cliente && <Vinculos c={cliente} />}
      {cliente && <HistoricoCliente clienteId={cliente.id} />}
      {cliente && (
        <p className="ficha-meta">
          Na base desde {formatarDataHora(cliente.criado_em)} · atualizado em {formatarDataHora(cliente.atualizado_em)}
          {cliente.ultima_importacao_id && (
            <>
              {' '}
              · última carga: <Link to={`/importacoes/${cliente.ultima_importacao_id}`}>importação #{cliente.ultima_importacao_id}</Link>
            </>
          )}
        </p>
      )}

      <DialogoConfirmacao
        aberto={confirmando}
        titulo="Excluir este cliente?"
        rotuloConfirmar="Excluir cliente"
        perigoso
        ocupado={excluir.isPending}
        aoCancelar={() => {
          setConfirmando(false)
          excluir.reset()
        }}
        aoConfirmar={() =>
          excluir.mutate(id, {
            onSuccess: () =>
              navegar('/clientes', {
                state: { aviso: `Cadastro de ${cliente?.nome ?? 'cliente'} excluído da carteira.` } satisfies EstadoNavegacao,
              }),
          })
        }
      >
        <p>
          <strong>{cliente?.nome}</strong> deixa de aparecer na busca e nas listagens. O histórico de vínculos e importações fica guardado.
        </p>
        {excluir.isError && (
          <p className="campo-erro" role="alert">
            {mensagemDeErro(excluir.error)}
          </p>
        )}
      </DialogoConfirmacao>
    </>
  )
}
