const caminhos = {
  painel: 'M4 13h6V4H4v9Zm0 7h6v-5H4v5Zm10 0h6v-9h-6v9Zm0-16v5h6V4h-6Z',
  clientes:
    'M16 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm-8 0a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm0 2c-2.7 0-6 1.3-6 3.5V19h12v-2.5C14 14.3 10.7 13 8 13Zm8 0c-.3 0-.7 0-1 .1 1.2.8 2 1.9 2 3.4V19h5v-2.5c0-2.2-3.3-3.5-6-3.5Z',
  empresas: 'M4 21V5l8-2v4l8 2v12H4Zm2-2h4v-3H6v3Zm0-5h4v-3H6v3Zm0-5h4V6.5L6 7.4V9Zm6 10h6v-8l-6-1.5V19Z',
  importacoes: 'M12 3 7 8h3.5v6h3V8H17l-5-5ZM5 15v4.5c0 .8.7 1.5 1.5 1.5h11c.8 0 1.5-.7 1.5-1.5V15h-2v4H7v-4H5Z',
  busca: 'M10.5 4a6.5 6.5 0 0 1 5.2 10.4l4.4 4.4-1.4 1.4-4.4-4.4A6.5 6.5 0 1 1 10.5 4Zm0 2a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9Z',
  menu: 'M4 6h16v2H4V6Zm0 5h16v2H4v-2Zm0 5h16v2H4v-2Z',
  fechar: 'm6.4 5 5.6 5.6L17.6 5 19 6.4 13.4 12l5.6 5.6-1.4 1.4-5.6-5.6L6.4 19 5 17.6l5.6-5.6L5 6.4 6.4 5Z',
  alerta: 'M12 3 2 20h20L12 3Zm-1 6h2v5h-2V9Zm0 7h2v2h-2v-2Z',
  ok: 'm9.5 16.2-4.2-4.2-1.4 1.4 5.6 5.6 11-11-1.4-1.4-9.6 9.6Z',
  arquivo: 'M6 2h8l5 5v13c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2Zm7 1.5V8h4.5L13 3.5Z',
  voltar: 'M20 11H7.8l5.6-5.6L12 4l-8 8 8 8 1.4-1.4L7.8 13H20v-2Z',
  seta: 'M7 10l5 5 5-5H7Z',
  editar: 'M4 17.2V20h2.8l8.3-8.3-2.8-2.8L4 17.2Zm13.7-7.5c.4-.4.4-1 0-1.4l-2-2c-.4-.4-1-.4-1.4 0l-1.5 1.5 2.8 2.8 2.1-1.9Z',
  lixo: 'M7 21c-.6 0-1-.4-1-1V7H5V5h5V4h4v1h5v2h-1v13c0 .6-.4 1-1 1H7Zm2-4h2V9H9v8Zm4 0h2V9h-2v8Z',
  recarregar: 'M17.7 6.3A8 8 0 1 0 19.7 14h-2.1a6 6 0 1 1-1.4-6.2L13 11h7V4l-2.3 2.3Z',
} as const

export type NomeIcone = keyof typeof caminhos

export function Icone({ nome, tamanho = 20 }: { nome: NomeIcone; tamanho?: number }) {
  return (
    <svg width={tamanho} height={tamanho} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d={caminhos[nome]} fill="currentColor" />
    </svg>
  )
}
