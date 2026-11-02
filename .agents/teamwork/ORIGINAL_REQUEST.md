# Original User Request

## Initial Request — 2026-11-02T19:42:17Z

Implementar para produção as duas frentes no projeto Montanha Media Lab: Motor de Text-to-Speech Neural (TTS estilo Clipchamp) e Reestruturação da Interface do Editor estilo Clipchamp, com testes ponta a ponta automatizados no Microsoft Edge e sincronização com Git.

Working directory: C:\Users\Administrator\Documents\Projetos\montanha-media-lab
Integrity mode: development

## Requirements

### R1. Motor de Text-to-Speech Neural (TTS estilo Clipchamp)
Integrar `edge-tts` no backend `server.py` com suporte a vozes brasileiras (`pt-BR-FranciscaNeural`, `pt-BR-AntonioNeural`, etc.), controle de ritmo/velocidade e tom. Criar endpoint `POST /api/tts` que recebe texto, voz e velocidade, gera o arquivo `.mp3` na pasta de mídia e retorna a URL/caminho para carregar na timeline de áudio. Implementar painel de configuração no frontend com seletor de voz, teste prévio (preview) e botão "Adicionar à Timeline".

### R2. Reestruturação da Interface do Editor estilo Clipchamp
Implementar dock vertical esquerdo com ícones finos (~56px) para Minha Mídia, Gravar & Criar (TTS), Legendas e Áudio, com gaveta expansível lateral para cada ferramenta selecionada, mantendo o player e a timeline limpos e centralizados. Implementar barra superior da timeline ultra-minimalista contendo apenas Dividir/Tesoura, Desfazer, Refazer e Play. Implementar menu de contexto acionado com o botão direito do mouse nos clipes da timeline com suporte a atalhos de teclado e às seguintes operações:
- Duplicar (Ctrl+D), Copiar (Ctrl+C), Colar (Ctrl+V), Excluir (Del)
- Dividir (S), Congelar Quadro (F), Renomear
- Submenu Áudio: Ativar Mudo, Desanexar
- Submenu Sugestões de IA: Recortar Pausas e Silêncios com detecção automática de silêncio e divisão funcional dos clipes
Implementar dock retrátil à direita para propriedades do elemento selecionado (Volume, Velocidade, Legendas).

### R3. Compatibilidade e Infraestrutura
Manter compatibilidade com execução tanto local no Windows (porta 4190 / Túnel Cloudflare) quanto no celular via Termux (porta 8080 padrão), sem adicionar dependências externas desnecessárias.

### R4. Verificação Ponta a Ponta e Versionamento
Criar e executar uma suíte de testes ponta a ponta automatizados com Playwright no Microsoft Edge cobrindo o fluxo de geração de TTS, adição à timeline e as interações da nova interface do editor. Sincronizar o repositório com `git push origin main`.

## Acceptance Criteria

### Geração e Integração de TTS
- [ ] Endpoint `POST /api/tts` processa requisições com texto, voz brasileira selecionada e velocidade, gerando o arquivo `.mp3` na pasta de mídia e retornando a URL/caminho acessível.
- [ ] Frontend exibe painel de TTS com catálogo de vozes brasileiras, controle de velocidade e botão de teste prévio (preview) reproduzível.
- [ ] Botão "Adicionar à Timeline" insere o áudio gerado diretamente como um clipe na trilha de áudio da timeline.

### Interface do Editor
- [ ] Dock lateral esquerdo possui largura de ~56px com ícones finos para Minha Mídia, Gravar & Criar (TTS), Legendas e Áudio.
- [ ] Seleção de cada ferramenta abre gaveta lateral expansível mantendo player e timeline centralizados.
- [ ] Barra superior da timeline apresenta layout ultra-minimalista com apenas Dividir/Tesoura, Desfazer, Refazer e Play funcionais.
- [ ] Clique com o botão direito sobre clipe da timeline exibe menu de contexto com todas as opções especificadas e atalhos de teclado ativos (Ctrl+D, Ctrl+C, Ctrl+V, Del, S, F).
- [ ] Opção "Sugestões de IA > Recortar Pausas e Silêncios" detecta trechos de silêncio no clipe e executa a divisão funcional na timeline.
- [ ] Dock retrátil à direita exibe controles ajustáveis de Volume, Velocidade e Legendas para o elemento selecionado.

### Compatibilidade e Verificação
- [ ] Aplicação inicia e opera corretamente nas portas 4190 (Windows) e 8080 (Termux).
- [ ] Suíte Playwright automatizada executa no Microsoft Edge e valida com sucesso os fluxos de TTS e navegação da interface.
- [ ] Código comitido e enviado com sucesso ao branch principal via `git push origin main`.
