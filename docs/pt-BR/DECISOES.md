# Registros de decisão

Sete decisões que moldaram o site. Cada uma é uma bifurcação real no build, e cada uma trouxe um custo junto.

---

## ADR-1: Sem framework e sem bundler

**Contexto.** O site é um catálogo com muito design visual e pouco estado: galerias, modais, gaveta de compra, sacola, seletor de idioma. Precisa ir para o ar como arquivos, abrir pelo sistema de arquivos e ser editável por um engenheiro sem toolchain.

**Decisão.** HTML, CSS e JavaScript escritos à mão. Nada de framework de componentes, bundler, transpilador ou pré-processador de CSS. Os scripts são arquivos simples, carregados com `<script src>` e separados por responsabilidade: shell, interações, sacola, chat, tracking, cookies e demo de latência.

**Alternativas consideradas.** Um framework de componentes com export estático daria componentes e uma etapa de build. Um gerador de site estático com linguagem de template daria layouts, mas deixaria o roteamento e o modelo de conteúdo nas abstrações de outra pessoa. Os dois trazem uma árvore de dependências para atualizar, auditar e reaprender, e isso para um site cujo modelo de interação é um punhado de overlays.

**Consequências.** Uma página é HTML, a sua folha de estilo e os seus scripts, sem etapa de hidratação. Nada quebra num bump de dependência, porque não há dependência para atualizar. O custo é a composição manual: mexer no header é mexer no gerador, componente compartilhado é função Python, e não existe sistema de tipos nem lint para pegar um erro de digitação num nome de classe. A folha de estilo compartilhada só cresce, e nada no pipeline avisa quais regras deixaram de ser usadas.

---

## ADR-2: Geradores em Python no lugar de um CMS

**Contexto.** 45 rotas por idioma, header e rodapé compartilhados, estruturas de seção repetidas em quatro páginas de modelo e conteúdo que muda em rajadas. Um CMS colocaria banco de dados e editor entre o texto e o deploy. Quem escreve o texto é o engenheiro que publica, e toda mudança precisa ser revisável linha por linha.

**Decisão.** Cada família de página tem um script Python que lê um dicionário de conteúdo e escreve HTML. São dezesseis geradores, um módulo de shell compartilhado e um orquestrador que roda tudo em ordem. O conteúdo fica em dicionários ao lado do gerador que o consome. Dados que atravessam páginas ficam em módulos dedicados, com fonte única.

**Alternativas consideradas.** Um CMS hospedado dá editor para quem não é engenheiro, ao custo de uma API de conteúdo, um ambiente de preview e uma camada de renderização. Um gerador que parte de markdown entrega arquivos de conteúdo mais simples, mas estrutura mais fraca para páginas que são 80 por cento layout. Editar HTML à mão foi o ponto de partida e falhou pela divergência: a mesma lista de navegação era copiada em toda página.

**Consequências.** Mudança estrutural acontece uma vez, no gerador, e o diff mostra exatamente quais páginas mudaram. Revisar conteúdo é revisar código. O custo é que o modelo de conteúdo é Python: quem escreve precisa do repositório, e os dicionários não têm schema, então uma chave ausente é erro em tempo de execução durante o build. Os geradores também guardam a marcação como string, o que deixa indentação, aspas e escape na dependência de disciplina manual, não de imposição da ferramenta.

---

## ADR-3: Uma taxa de câmbio fixa para um site estático

**Contexto.** As páginas em português cotam na moeda local, as páginas em inglês cotam em dólares. Os valores aparecem nas narrativas de case, nas comparações de custo e nos cálculos de payback. Uma página estática não chama API de câmbio em tempo de requisição, e um número que muda entre duas visitas seria indefensável num estudo de caso feito para ser lido uma vez e citado.

**Decisão.** Uma taxa, definida como constante em um único módulo e aplicada em tempo de build. Os valores ficam guardados uma vez, como inteiros na moeda de operação, e são convertidos durante a geração. O arredondamento é por faixas, com o passo escolhido sobre o valor convertido para o resultado ler como número redondo. O payback sai do preço convertido dividido pela economia mensal. A formatação segue o locale: ponto como separador de milhar em português, vírgula em inglês.

**Alternativas consideradas.** Uma taxa ao vivo seria precisa e instável. Um valor em dólar fixo por case seria estável e impossível de manter, porque o valor de origem mora na narrativa. Cotar as duas moedas lado a lado seria honesto, mas dobraria a carga de leitura.

**Consequências.** Uma edição muda todos os valores convertidos de uma vez, e nenhum valor monetário é digitado à mão. A taxa é um passivo que se deteriora em silêncio; está documentada com um limiar de revisão, não com um cronograma. Os dois idiomas do mesmo case podem discordar num número derivado. Isso está aritmeticamente correto e parece inconsistência para quem troca de idioma.

---

## ADR-4: Dados estruturados gerados da mesma fonte do texto

**Contexto.** Buscadores e answer engines leem as páginas, e tipos de página diferentes pedem marcações diferentes: `Product` e `Offer` nas páginas de modelo, `Article`, `FAQPage` e `BreadcrumbList` nos cases, `CollectionPage` com `ItemList` nos índices. Escrever JSON-LD à mão em cada página garante que ele divirja do texto visível, e preço divergente entre marcação e página é risco de ação manual.

**Decisão.** Os dados estruturados saem de funções Python que recebem os mesmos argumentos da marcação visível, incluindo o módulo de preços e os dados de case. As ofertas de produto são montadas a partir do módulo de preços, então o preço no JSON-LD e o preço impresso não podem divergir. A marcação de FAQ nasce da mesma lista que renderiza as perguntas visíveis. Cards sociais e URLs canônicas entram numa etapa de pós-processamento, para que nenhuma família de página possa esquecê-los.

**Alternativas consideradas.** Um bloco `Organization` genérico em toda página é fácil e inútil. JSON-LD escrito à mão por página é expressivo e inverificável neste número de páginas. Uma etapa de validação de schema no pipeline foi considerada e não está implementada.

**Consequências.** A consistência é estrutural, não revisada: a marcação não consegue afirmar um preço que a página não mostra. O custo é o acoplamento, porque mexer no formato do módulo de preços afeta o construtor de dados estruturados, e o JSON-LD é tão correto quanto o Python que o monta. Nada valida a saída contra schema.org antes do deploy, então um bloco malformado vai para o ar e só aparece num relatório do search console.

---

## ADR-5: Um chassi em CSS como fallback para renders ausentes

**Contexto.** Fotos e renders de produto chegam tarde e mudam com frequência. O hero depende de um PNG transparente que o script de parallax move. Arquivo ausente deixaria um buraco na seção mais importante da página, e o design não pode esperar pelos assets.

**Decisão.** Todo hero mantém o `<img>` como alvo do parallax, com o id na própria imagem. Um handler de erro inline revela um chassi desenhado em CSS, posicionado onde a imagem estaria. Um observer pequeno espelha o transform da imagem no chassi, e o movimento sobrevive à substituição sem tocar no script de interação. `width` e `height` explícitos reservam o espaço nos dois casos.

**Alternativas consideradas.** Imagem de placeholder é uma caixa cinza com cara de defeito. Bloquear o build por causa de um asset ausente interrompe o trabalho de conteúdo por uma dependência de design. Tirar o parallax quando a imagem falta perde o movimento em torno do qual a seção foi desenhada.

**Consequências.** A página fica apresentável antes de os assets existirem, e o parallax tem um único caminho de código. O custo é uma segunda representação do produto em CSS, que precisa ser mantida junto com os renders, e uma restrição de marcação que sobrevive ao motivo dela: o id não pode migrar para um wrapper, e o chassi precisa continuar sendo o irmão anterior da imagem. O observer também roda em toda mutação de estilo da imagem.

---

## ADR-6: O sitemap é gerado a partir dos arquivos publicados

**Contexto.** O sitemap precisa listar exatamente as URLs indexáveis, com alternates `hreflang`. Lista mantida à mão fica errada no instante em que alguém adiciona uma página, e par `hreflang` errado é pior que nenhum, porque diz aos buscadores que duas páginas são traduções uma da outra quando não são.

**Decisão.** Uma etapa de pós-processamento percorre as árvores de idioma atrás de arquivos `index.html`, pula o que tiver meta robots `noindex`, pula a pasta arquivada e pareia o restante pela chave de identidade, com um mapa de alias explícito para os slugs traduzidos. O `x-default` aponta para a URL em inglês. A data de modificação vem dos dados estruturados da página quando existem; quando não, vem do git: a página leva a data de hoje se a cópia de trabalho difere do último commit, e a data do commit se não difere.

**Alternativas consideradas.** Um manifesto de rotas mantido à mão é simples e desatualiza. Derivar o sitemap dos registros dos geradores acerta as páginas geradas, mas fica cego para todo o resto da árvore, inclusive páginas adicionadas por outros meios.

**Consequências.** O sitemap descreve o que está publicado, e uma página `noindex` sai do índice sozinha, sem uma segunda edição. O custo é a dependência de ordem: a etapa só está correta porque roda depois de todos os geradores, e uma página gerada mas não registrada no pipeline fica fora do sitemap sem aviso, ainda que continue acessível. O mapa de alias é uma exceção manual, que precisa de atualização a cada slug traduzido novo.

---

## ADR-7: Uma barra de região apoiada em session storage, não em geolocalização

**Contexto.** O site tem duas árvores de idioma e duas moedas, e recebe visitantes dos dois públicos. Um redirect automático por endereço IP erra para quem viaja, para quem usa VPN e para qualquer um que abra um link compartilhado a partir do outro idioma.

**Decisão.** Uma barra de região aparece uma vez por sessão, no primeiro carregamento, e oferece oito regiões mapeadas para dois destinos. A opção inicial segue o idioma da página. Trocar o select não navega: a troca acontece num botão de continuar explícito, que preserva query string e âncora para que um link de checkout mantenha a seleção de produto. A dispensa fica em session storage, não em cookie, então não precisa de consentimento.

**Alternativas consideradas.** Redirect por geo-IP é invisível quando acerta e irritante quando erra. Um seletor de idioma permanente só no header é menos descobrível para quem chega pela primeira vez comparando preços. Um cookie exigiria tratamento de consentimento para uma preferência que não precisa durar mais que a sessão.

**Consequências.** O visitante escolhe, a escolha é reversível e nada fica guardado entre sessões. O custo é uma decisão extra antes do conteúdo na primeira visita, e uma interação de teclado que precisou de um botão de continuar separado para não navegar enquanto se percorrem as opções com Tab. A lista de regiões é um mapeamento fixo, então mercado novo é mudança de conteúdo, não de configuração.
