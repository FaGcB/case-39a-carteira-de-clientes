import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/http'
import { useAtualizarCliente, useCliente } from '../api/queries'
import type { Cliente, ClienteInput, Sexo } from '../api/types'
import type { EstadoNavegacao } from '../components/Aviso'
import { Campo, Selecao } from '../components/Campo'
import { FaixaErros } from '../components/ErrosFormulario'
import { separarErros } from '../lib/erros'
import { Carregando, Erro } from '../components/Estados'
import { Cabecalho } from '../components/Layout'
import { formatarCep, formatarCpf, formatarTelefone } from '../lib/format'
import { useTituloPagina } from '../lib/hooks'
import { NaoEncontradoPage } from './NaoEncontradoPage'

const UFS = 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split(' ')
const ESTADOS_CIVIS = ['Solteiro', 'Casado', 'Divorciado', 'Viuvo', 'Uniao estavel']
const ROTULO_ESTADO_CIVIL: Record<string, string> = { Viuvo: 'Viúvo', 'Uniao estavel': 'União estável' }

const CAMPOS = [
  'nome',
  'data_nascimento',
  'sexo',
  'estado_civil',
  'email',
  'telefone',
  'endereco.cep',
  'endereco.logradouro',
  'endereco.numero',
  'endereco.complemento',
  'endereco.bairro',
  'endereco.cidade',
  'endereco.uf',
] as const

type Formulario = Record<(typeof CAMPOS)[number], string>

function paraFormulario(c: Cliente): Formulario {
  return {
    nome: c.nome,
    data_nascimento: c.data_nascimento,
    sexo: c.sexo ?? '',
    estado_civil: c.estado_civil ?? '',
    email: c.email ?? '',
    telefone: c.telefone ? formatarTelefone(c.telefone) : '',
    'endereco.cep': formatarCep(c.endereco.cep),
    'endereco.logradouro': c.endereco.logradouro,
    'endereco.numero': c.endereco.numero,
    'endereco.complemento': c.endereco.complemento ?? '',
    'endereco.bairro': c.endereco.bairro,
    'endereco.cidade': c.endereco.cidade,
    'endereco.uf': c.endereco.uf,
  }
}

function paraApi(f: Formulario): ClienteInput {
  return {
    nome: f.nome,
    data_nascimento: f.data_nascimento,
    sexo: (f.sexo || null) as Sexo | null,
    estado_civil: f.estado_civil || null,
    email: f.email.trim() || null,
    telefone: f.telefone.trim() || null,
    endereco: {
      cep: f['endereco.cep'],
      logradouro: f['endereco.logradouro'],
      numero: f['endereco.numero'],
      complemento: f['endereco.complemento'] || null,
      bairro: f['endereco.bairro'],
      cidade: f['endereco.cidade'],
      uf: f['endereco.uf'],
    },
  }
}

function FormularioCliente({ cliente }: { cliente: Cliente }) {
  const [form, setForm] = useState<Formulario>(() => paraFormulario(cliente))
  const salvar = useAtualizarCliente(cliente.id)
  const navegar = useNavigate()
  const { porCampo, gerais } = separarErros(salvar.error, CAMPOS)

  const [corrigidos, setCorrigidos] = useState<Set<string>>(new Set())
  const erroDe = (c: (typeof CAMPOS)[number]) => (corrigidos.has(c) ? undefined : porCampo[c])

  const props = (c: (typeof CAMPOS)[number]) => ({
    name: c,
    value: form[c],
    erro: erroDe(c),
    onChange: (e: { target: { value: string } }) => {
      setForm((f) => ({ ...f, [c]: e.target.value }))
      setCorrigidos((s) => new Set(s).add(c))
    },
  })

  const enviar = (e: FormEvent) => {
    e.preventDefault()
    setCorrigidos(new Set())
    salvar.mutate(paraApi(form), {
      onSuccess: () => navegar(`/clientes/${cliente.id}`, { state: { aviso: 'Alterações salvas.' } satisfies EstadoNavegacao }),
    })
  }

  return (
    <form className="formulario" onSubmit={enviar} noValidate>
      <FaixaErros erro={salvar.error} porCampo={porCampo} gerais={gerais} />

      <fieldset className="painel">
        <legend>Dados cadastrais</legend>
        <div className="grade-campos">
          <Campo
            rotulo="CPF"
            value={formatarCpf(cliente.cpf)}
            readOnly
            disabled
            dica="O CPF identifica o cliente e não pode ser alterado."
            largura="media"
          />
          <Campo rotulo="Nome completo" {...props('nome')} largura="cheia" autoComplete="off" />
          <Campo rotulo="Data de nascimento" type="date" {...props('data_nascimento')} largura="curta" />
          <Selecao
            rotulo="Sexo"
            {...props('sexo')}
            largura="curta"
            opcoes={[
              { valor: '', rotulo: 'Não informado' },
              { valor: 'F', rotulo: 'Feminino' },
              { valor: 'M', rotulo: 'Masculino' },
            ]}
          />
          <Selecao
            rotulo="Estado civil"
            {...props('estado_civil')}
            largura="curta"
            opcoes={[
              { valor: '', rotulo: 'Não informado' },
              ...ESTADOS_CIVIS.map((v) => ({ valor: v, rotulo: ROTULO_ESTADO_CIVIL[v] ?? v })),
            ]}
          />
          <Campo rotulo="E-mail" type="email" {...props('email')} largura="media" />
          <Campo rotulo="Telefone" type="tel" inputMode="tel" {...props('telefone')} largura="curta" placeholder="(11) 91234-5678" />
        </div>
      </fieldset>

      <fieldset className="painel">
        <legend>Endereço</legend>
        <div className="grade-campos">
          <Campo rotulo="CEP" inputMode="numeric" {...props('endereco.cep')} largura="curta" placeholder="00000-000" />
          <Campo rotulo="Logradouro" {...props('endereco.logradouro')} largura="cheia" />
          <Campo rotulo="Número" {...props('endereco.numero')} largura="curta" />
          <Campo rotulo="Complemento" {...props('endereco.complemento')} largura="media" />
          <Campo rotulo="Bairro" {...props('endereco.bairro')} largura="media" />
          <Campo rotulo="Cidade" {...props('endereco.cidade')} largura="media" />
          <Selecao rotulo="UF" {...props('endereco.uf')} largura="curta" opcoes={UFS.map((u) => ({ valor: u, rotulo: u }))} />
        </div>
      </fieldset>

      <div className="formulario-acoes">
        <Link to={`/clientes/${cliente.id}`} className="botao botao-secundario">
          Cancelar
        </Link>
        <button type="submit" className="botao botao-primario" disabled={salvar.isPending}>
          {salvar.isPending ? 'Salvando…' : 'Salvar alterações'}
        </button>
      </div>
    </form>
  )
}

export function ClienteEditarPage() {
  const id = Number(useParams().id)
  const { data, isPending, isError, error, refetch } = useCliente(id)
  useTituloPagina(data ? `Editar ${data.nome}` : 'Editar cliente')

  if (isError && error instanceof ApiError && error.status === 404)
    return <NaoEncontradoPage mensagem="Este cliente não existe ou foi excluído." />

  return (
    <>
      <Cabecalho
        voltar={{ para: `/clientes/${id}`, rotulo: 'Ficha do cliente' }}
        titulo={data ? `Editar ${data.nome}` : 'Editar cliente'}
      />
      {isPending ? (
        <section className="painel">
          <Carregando linhas={6} />
        </section>
      ) : isError ? (
        <Erro erro={error} aoTentarDeNovo={() => refetch()} />
      ) : (
        <FormularioCliente key={data.id} cliente={data} />
      )}
    </>
  )
}
