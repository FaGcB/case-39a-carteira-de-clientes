import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/http'
import { useAtualizarEmpresa, useEmpresa } from '../api/queries'
import type { Empresa, EmpresaInput } from '../api/types'
import type { EstadoNavegacao } from '../components/Aviso'
import { Campo } from '../components/Campo'
import { FaixaErros } from '../components/ErrosFormulario'
import { separarErros } from '../lib/erros'
import { Carregando, Erro } from '../components/Estados'
import { Cabecalho } from '../components/Layout'
import { formatarCnpj, plural } from '../lib/format'
import { useTituloPagina } from '../lib/hooks'
import { NaoEncontradoPage } from './NaoEncontradoPage'

const CAMPOS = ['razao_social', 'nome_fantasia', 'setor'] as const

function FormularioEmpresa({ empresa }: { empresa: Empresa }) {
  const [form, setForm] = useState<EmpresaInput>({
    razao_social: empresa.razao_social,
    nome_fantasia: empresa.nome_fantasia,
    setor: empresa.setor,
  })
  const salvar = useAtualizarEmpresa(empresa.id)
  const navegar = useNavigate()
  const { porCampo, gerais } = separarErros(salvar.error, CAMPOS)
  const [corrigidos, setCorrigidos] = useState<Set<string>>(new Set())

  const props = (c: (typeof CAMPOS)[number]) => ({
    value: form[c],
    erro: corrigidos.has(c) ? undefined : porCampo[c],
    onChange: (e: { target: { value: string } }) => {
      setForm((f) => ({ ...f, [c]: e.target.value }))
      setCorrigidos((s) => new Set(s).add(c))
    },
  })

  const enviar = (e: FormEvent) => {
    e.preventDefault()
    setCorrigidos(new Set())
    salvar.mutate(form, {
      onSuccess: () =>
        navegar(`/empresas/${empresa.id}`, { state: { aviso: `${form.nome_fantasia} atualizada.` } satisfies EstadoNavegacao }),
    })
  }

  return (
    <form className="formulario" onSubmit={enviar} noValidate>
      <FaixaErros erro={salvar.error} porCampo={porCampo} gerais={gerais} />
      <fieldset className="painel">
        <legend>Dados da empresa</legend>
        <div className="grade-campos">
          <Campo
            rotulo="CNPJ"
            value={formatarCnpj(empresa.cnpj)}
            readOnly
            disabled
            largura="media"
            dica="O CNPJ identifica a empresa e não pode ser alterado."
          />
          <Campo rotulo="Razão social" {...props('razao_social')} largura="cheia" />
          <Campo rotulo="Nome fantasia" {...props('nome_fantasia')} largura="media" />
          <Campo rotulo="Setor" {...props('setor')} largura="media" />
        </div>
        <p className="texto-suave">
          A mudança vale para {plural(empresa.total_vinculos, 'vínculo', 'vínculos')} e aparece em todas as fichas ligadas a esta empresa.
        </p>
      </fieldset>
      <div className="formulario-acoes">
        <Link to={`/empresas/${empresa.id}`} className="botao botao-secundario">
          Cancelar
        </Link>
        <button type="submit" className="botao botao-primario" disabled={salvar.isPending}>
          {salvar.isPending ? 'Salvando…' : 'Salvar alterações'}
        </button>
      </div>
    </form>
  )
}

export function EmpresaEditarPage() {
  const id = Number(useParams().id)
  const { data, isPending, isError, error, refetch } = useEmpresa(id)
  useTituloPagina(data ? `Editar ${data.nome_fantasia}` : 'Editar empresa')

  if (isError && error instanceof ApiError && error.status === 404) return <NaoEncontradoPage mensagem="Esta empresa não existe." />

  return (
    <>
      <Cabecalho
        voltar={{ para: `/empresas/${id}`, rotulo: data?.nome_fantasia ?? 'Empresa' }}
        titulo={data ? `Editar ${data.nome_fantasia}` : 'Editar empresa'}
      />
      {isPending ? (
        <section className="painel">
          <Carregando linhas={4} />
        </section>
      ) : isError ? (
        <Erro erro={error} aoTentarDeNovo={() => refetch()} />
      ) : (
        <FormularioEmpresa key={data.id} empresa={data} />
      )}
    </>
  )
}
