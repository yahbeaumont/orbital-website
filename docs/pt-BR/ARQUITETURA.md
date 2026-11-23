# Arquitetura

## Contexto

O site é uma superfície de marketing e produto para uma marca de hardware que vende máquinas que rodam modelos de pesos abertos localmente. Ele publica 45 rotas por idioma, em português e inglês, a partir de um único repositório, no Firebase Hosting. Nada na página é renderizado sob demanda: o visitante recebe um arquivo gerado na máquina de build.

Duas coisas decorrem disso. Primeiro, toda decisão no nível da página, roteamento, pareamento de idiomas, URL canônica, dados estruturados, preço, precisa ser resolvida antes do deploy. Segundo, o único código de runtime é a pequena quantidade de JavaScript no navegador e as funções serverless por trás dos caminhos de compra e de suporte.

## Componentes e responsabilidades

**Módulos de conteúdo.** O texto vive em dicionários Python, uma subárvore por locale, no módulo que é dono da família de página. Dados que atravessam páginas vivem em módulos dedicados: preços e identidade de produto em um, velocidades de geração dos modelos em outro, entradas de case e as suas relações em um terceiro, conversão de moeda em um quarto. Esses módulos contêm apenas dados, nenhuma marcação.

**Shell compartilhado.** Um módulo expõe o header, o rodapé, a barra de região, a gaveta de compra e o conjunto de ícones como funções. Treze dos dezesseis geradores de página o importam. Rótulos de navegação, links jurídicos e o seletor de idioma existem, portanto, uma vez, e uma mudança chega a todas as páginas no próximo build.

**Geradores de página.** Dezesseis scripts, um por família de página: home, produtos, linha compacta, especificações, sistema operacional, Ultra, modelos, sobre, hubs, cases, growth, demo, latência, jurídico, composição de notebook e injeção de tags. Cada um lê o seu dicionário de conteúdo, chama as funções do shell e escreve `index.html` na árvore de idioma. Um gerador é o único lugar onde a estrutura daquela família é definida.

**Pós-processamento.** Cinco scripts rodam depois dos geradores. Um troca as imagens de interface pelas variantes em inglês. Um adiciona cards sociais às páginas que não os têm. Um anexa um hash de conteúdo a toda referência de CSS e JavaScript. Um reconstrói `sitemap.xml` e `robots.txt` a partir dos arquivos publicados. Um regenera o mapa de redirects.

**Orquestrador.** O `tools/build_all.py` roda os dezesseis geradores e as cinco etapas de pós-processamento como subprocessos, em ordem fixa, e encerra no primeiro status diferente de zero. Ele é o contrato de "o que é um build".

**Camada de hospedagem.** O Firebase Hosting serve o diretório de saída, termina o TLS, aplica os headers de segurança e de cache e avalia as regras de redirect. A sua lista de ignore na publicação é a fronteira entre o repositório e a superfície pública.

**Functions.** Três functions HTTPS na mesma região cuidam da criação da sessão de pagamento, da consulta de status do pedido e do webhook do provedor de pagamento, além do envio de e-mail e do encaminhamento de analytics. Elas guardam todos os segredos de que o produto precisa.

## Fronteiras e contratos

*Do repositório para a superfície pública.* A configuração de hospedagem publica a raiz do repositório mas ignora ferramental, documentação, functions, arquivos de ambiente, arquivos zip, markdown e metadados do repositório. Tudo que não está nessa lista é público por padrão, e é por isso que a lista é tratada como um controle de segurança e não como arrumação.

*Do build para o navegador.* Os geradores são donos da marcação. Os scripts do navegador nunca constroem uma seção da página, eles apenas alteram estado que a marcação já declara: classes para animação de reveal, um transform para parallax, `aria-hidden` para overlays. Uma página sem o seu script é legível e navegável.

*Do navegador para as functions.* O navegador envia um identificador de produto, uma quantidade e um endereço. Ele nunca envia um preço, uma moeda ou um total. A função resolve esses valores a partir do seu próprio catálogo e rejeita identificadores que não conhece.

*Do provedor de pagamento para as functions.* O webhook verifica a assinatura contra o corpo bruto da requisição antes de qualquer efeito. Uma requisição sem assinatura ou com assinatura divergente não tem efeito colateral nenhum.

*Da imagem para o fallback.* O parallax mira um `<img>` por id. Se a imagem falha, um handler inline revela um chassi em CSS que é o irmão anterior da imagem, e um observer copia o transform da imagem para o chassi. Os ids ficam na imagem, não em um wrapper, e essa é uma regra que as outras marcações precisam respeitar.

## Uma requisição pelo site

Um visitante requisita uma página de produto. O CDN responde com um arquivo gerado em tempo de build; não há render na origem. O documento declara o seu idioma, a URL canônica e três alternates `hreflang`, e carrega dados estruturados `Product` e `Offer` cujo preço veio do módulo de preços durante o build. CSS e JavaScript chegam com um hash de conteúdo na query string, então um navegador que guarda uma cópia antiga busca a nova depois de um deploy. O navegador roda o script de shell para a barra de região e o header, e o script de interação para reveals, modais e a gaveta de compra. Escolher um produto escreve apenas identificadores e quantidades no local storage. Confirmar uma compra navega para a página de checkout, que chama a função de pagamento; a função valida a requisição, resolve os preços no servidor, cria uma sessão hospedada e devolve uma URL de redirect. A página de confirmação lê depois o status do pedido por meio de uma segunda função, que devolve um endereço de e-mail mascarado.

Uma execução de build segue a mesma lógica ao contrário. Um módulo de conteúdo muda, o `build_all.py` regenera todas as páginas, as etapas de pós-processamento recarimbam os assets e reconstroem o sitemap a partir do que existe em disco, e a saída é publicada.

## Modelo de dados conceitual

*Locale.* Duas instâncias, `pt-br` e `en`, cada uma com um prefixo de URL, uma moeda e um conjunto de rotas.

*Rota.* Um caminho dentro de um locale, materializado como um diretório com um `index.html`. Uma rota carrega um tipo de página, uma URL canônica, um flag `noindex` opcional e uma chave de identidade usada para o pareamento.

*Par de locale.* Duas rotas, uma por locale, que compartilham uma chave de identidade. A chave normalmente é o caminho; um pequeno mapa de alias trata slugs que diferem entre idiomas. Um par pode estar incompleto, e um par incompleto não gera alternate `hreflang`.

*Produto.* Um identificador, um nome de exibição, um nome de modelo, um conjunto de especificações e um preço por moeda. Referenciado pelo catálogo, pelas páginas de modelo, pela tabela de comparação, pela gaveta, pela sacola e pelos dados estruturados.

*Entrada de case.* Um slug, um setor, uma narrativa, um conjunto de métricas, uma citação opcional, uma lista de FAQ e dois links de relação escolhidos pelo problema em comum.

*Documento jurídico.* Um slug, um corpo aprovado, uma data de vigência e um locale. O gerador pagina e marca; ele não reescreve.

## Decisões de deploy

A saída é commitada no repositório, porque o site é o artefato e o diff é a revisão. O deploy é um release de hospedagem desse diretório, com as regras de header e de redirect aplicadas a partir da configuração. A política de cache é deliberadamente conservadora: HTML e assets revalidam, com a invalidação de assets feita pelo hash de conteúdo e não pela duração do cache. Páginas arquivadas permanecem na árvore mas ficam fora do sitemap e recebem `noindex` por uma regra de header.

## Limites conhecidos

O pipeline não tem modo incremental, então cada execução reescreve todas as páginas e os diffs são grandes. O HTML é produzido por concatenação de strings sem nenhum validador no pipeline, então marcação malformada é pega no navegador. A dependência de ordem é implícita: o sitemap só está correto porque roda depois dos geradores. O mapa de alias para slugs traduzidos é mantido à mão. Os dados estruturados são gerados a partir dos mesmos módulos do texto visível, o que os mantém consistentes, mas nada valida o resultado contra um schema antes do deploy.
