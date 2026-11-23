# Registros de decisão

Sete decisões que moldaram o site. Cada uma é uma bifurcação real no build, com o custo que veio junto com a escolha.

---

## ADR-1: Sem framework e sem bundler

**Contexto.** O site é um catálogo com design visual pesado e pouco estado: galerias, modais, uma gaveta de compra, uma sacola, um seletor de idioma. Ele precisa ser publicável como arquivos, abrível pelo sistema de arquivos e editável por um engenheiro sem toolchain.

**Decisão.** HTML, CSS e JavaScript escritos à mão. Sem framework de componentes, sem bundler, sem transpilador, sem pré-processador de CSS. Os scripts são arquivos simples carregados com `<script src>`, divididos por responsabilidade: shell, interações, sacola, chat, tracking, cookies, demo de latência.

**Alternativas consideradas.** Um framework de componentes com export estático daria componentes e uma etapa de build. Um gerador de site estático com linguagem de template daria layouts mas manteria o roteamento e o modelo de conteúdo nas abstrações de outra pessoa. Os dois acrescentam uma árvore de dependências que precisa ser atualizada, auditada e reaprendida, para um site cujo modelo de interação é um punhado de overlays.

**Consequências.** Uma página é HTML mais a sua folha de estilo e os seus scripts, sem etapa de hidratação. Nada quebra em um bump de dependência porque não há dependências para atualizar. O custo é que a composição é manual: uma mudança no header é uma mudança no gerador, um componente compartilhado é uma função Python, e não há sistema de tipos nem lint pegando um erro de digitação em um nome de classe. A folha de estilo compartilhada não para de crescer, e nada no pipeline informa quais regras deixaram de ser usadas.

---

## ADR-2: Geradores em Python em vez de um CMS

**Contexto.** 45 rotas por idioma, com header e rodapé compartilhados, estruturas de seção repetidas em quatro páginas de modelo, e conteúdo que muda em rajadas. Um CMS colocaria um banco de dados e um editor entre o texto e o deploy. O texto é escrito pelo engenheiro que o publica, e toda mudança deveria ser revisável linha por linha.

**Decisão.** Cada família de página tem um script Python que lê um dicionário de conteúdo e escreve HTML. Dezesseis geradores, um módulo de shell compartilhado, um orquestrador que os roda em ordem. O conteúdo vive em dicionários ao lado do gerador que o consome. Dados que atravessam páginas vivem em módulos dedicados com uma fonte única.

**Alternativas consideradas.** Um CMS hospedado dá um editor para quem não é engenheiro, ao custo de uma API de conteúdo, um ambiente de preview e uma camada de renderização. Um gerador baseado em markdown dá arquivos de conteúdo mais simples mas estrutura mais fraca para páginas que são 80 por cento layout. Editar HTML à mão foi o ponto de partida e falhou na divergência: a mesma lista de navegação era copiada em todas as páginas.

**Consequências.** Mudança estrutural acontece uma vez, no gerador, e o diff mostra exatamente quais páginas mudaram. A revisão de conteúdo é uma revisão de código. O custo é que o modelo de conteúdo é Python: quem escreve precisa do repositório, e os dicionários não têm schema, então uma chave faltando é um erro em tempo de execução durante o build. Os geradores também guardam a marcação como strings, o que significa que indentação, aspas e escape são disciplinas manuais e não coisas impostas.

---

## ADR-3: Uma taxa de câmbio fixa para um site estático

**Contexto.** As páginas em português cotam os preços na moeda local, as páginas em inglês cotam em dólares. Os valores são usados nas narrativas de case, nas comparações de custo e nos cálculos de payback. Uma página estática não pode chamar uma API de câmbio em tempo de requisição, e um número que muda entre duas visitas seria indefensável em um estudo de caso feito para ser lido uma vez e citado.

**Decisão.** Uma taxa, definida como constante em um único módulo, aplicada em tempo de build. Os valores são guardados uma vez como inteiros na moeda de operação e convertidos durante a geração. O arredondamento é por faixas, com o passo escolhido sobre o valor convertido para que os resultados leiam como números redondos. O payback é calculado a partir do preço convertido dividido pela economia mensal. A formatação segue o locale: ponto como separador de milhar em português, vírgula em inglês.

**Alternativas consideradas.** Uma taxa ao vivo seria precisa e instável. Um valor em dólar fixo por case seria estável e impossível de manter, porque o valor de origem vive na narrativa. Cotar as duas moedas lado a lado seria honesto mas dobra a carga de leitura.

**Consequências.** Uma edição muda todo valor convertido de forma consistente, e nenhum valor monetário é digitado à mão. A taxa é um passivo que se deteriora em silêncio; ela está documentada com um limiar de revisão e não com um cronograma. Os dois idiomas do mesmo case podem discordar em um número derivado, o que está aritmeticamente correto e parece inconsistência para um leitor que troca de idioma.

---

## ADR-4: Dados estruturados gerados da mesma fonte do texto

**Contexto.** Buscadores e answer engines leem as páginas, e tipos de página diferentes merecem marcações diferentes: `Product` e `Offer` para páginas de modelo, `Article`, `FAQPage` e `BreadcrumbList` para cases, `CollectionPage` com `ItemList` para índices. Escrever JSON-LD à mão por página garante que ele divirja do texto visível, e uma divergência de preço entre marcação e página é um risco de ação manual.

**Decisão.** Os dados estruturados são produzidos por funções Python que recebem os mesmos argumentos da marcação visível, incluindo o módulo de preços e os dados de case. As ofertas de produto são montadas a partir do módulo de preços, então o preço no JSON-LD e o preço impresso não podem divergir. A marcação de FAQ é gerada a partir da mesma lista que renderiza as perguntas visíveis. Cards sociais e URLs canônicas são adicionados por uma etapa de pós-processamento, para que nenhuma família de página possa esquecê-los.

**Alternativas consideradas.** Um bloco `Organization` genérico em toda página é fácil e inútil. JSON-LD escrito à mão por página é expressivo e inverificável neste número de páginas. Uma etapa de validação de schema no pipeline foi considerada e não está implementada.

**Consequências.** A consistência é estrutural e não revisada: a marcação não consegue afirmar um preço que a página não mostra. O custo é o acoplamento, porque uma mudança no formato do módulo de preços toca o construtor de dados estruturados, e o JSON-LD é tão correto quanto o Python que o monta. Nada valida a saída contra schema.org antes do deploy, então um bloco malformado vai para o ar e é descoberto em um relatório do search console.

---

## ADR-5: Um chassi em CSS como fallback para renders ausentes

**Contexto.** As fotos e renders de produto chegam tarde e mudam com frequência. O hero depende de um PNG transparente que o script de parallax move. Um arquivo ausente deixaria um buraco na seção mais importante da página, e o design não pode esperar pelos assets.

**Decisão.** Todo hero mantém o seu `<img>` como alvo do parallax, com o id na própria imagem. Um handler de erro inline revela um chassi desenhado em CSS posicionado onde a imagem estaria. Um observer pequeno espelha o transform da imagem no chassi, então o movimento sobrevive à substituição sem tocar no script de interação. `width` e `height` explícitos reservam o espaço nos dois casos.

**Alternativas consideradas.** Uma imagem de placeholder é uma caixa cinza com cara de defeito. Bloquear o build por asset ausente interrompe o trabalho de conteúdo por causa de uma dependência de design. Remover o parallax quando a imagem falta perde o movimento em torno do qual a seção foi desenhada.

**Consequências.** A página é apresentável antes de os assets existirem, e o parallax tem um único caminho de código. O custo é uma segunda representação do produto em CSS que precisa ser mantida junto com os renders, e uma restrição de marcação que sobrevive ao motivo dela: o id não pode migrar para um wrapper, e o chassi precisa continuar sendo o irmão anterior da imagem. O observer também roda em toda mutação de estilo da imagem.

---

## ADR-6: O sitemap é gerado a partir dos arquivos publicados

**Contexto.** O sitemap precisa listar exatamente as URLs indexáveis, com alternates `hreflang`. Uma lista mantida à mão está errada no momento em que uma página é adicionada, e um par `hreflang` errado é pior que nenhum, porque diz aos buscadores que duas páginas são traduções uma da outra quando não são.

**Decisão.** Uma etapa de pós-processamento percorre as árvores de idioma em busca de arquivos `index.html`, pula tudo cujo meta robots diga `noindex`, pula a pasta arquivada e pareia as páginas restantes pela chave de identidade, com um mapa de alias explícito para os slugs que são traduzidos. O `x-default` aponta para a URL em inglês. A data de modificação vem dos dados estruturados da página quando existem, senão vem do git: a data de hoje se a cópia de trabalho difere do último commit, e a data do commit se não difere.

**Alternativas consideradas.** Um manifesto de rotas mantido à mão é simples e desatualizado. Derivar o sitemap dos registros dos geradores é preciso para páginas geradas mas cego para qualquer outra coisa na árvore, incluindo páginas adicionadas por outros meios.

**Consequências.** O sitemap descreve o que está publicado, e uma página `noindex` se remove do índice sem uma segunda edição. O custo é a dependência de ordem: a etapa só está correta porque roda depois de todos os geradores, e uma página gerada mas não registrada no pipeline fica silenciosamente ausente do sitemap enquanto continua acessível. O mapa de alias é uma exceção manual que precisa ser atualizada quando aparece um novo slug traduzido.

---

## ADR-7: Uma barra de região apoiada em session storage, não em geolocalização

**Contexto.** O site tem duas árvores de idioma e duas moedas, e os visitantes chegam dos dois públicos. Um redirect automático baseado em endereço IP erra para quem viaja, para quem usa VPN e para qualquer pessoa lendo um link compartilhado a partir do outro idioma.

**Decisão.** Uma barra de região aparece uma vez por sessão no primeiro carregamento, oferecendo oito regiões mapeadas para dois destinos. A opção inicial segue o idioma da página. Mudar o select não navega; a troca acontece em um botão de continuar explícito, que preserva query string e âncora para que um link de checkout mantenha a seleção de produto. A dispensa é guardada em session storage, não em cookie, então nenhum consentimento é necessário para ela.

**Alternativas consideradas.** Redirect por geo-IP é invisível quando acerta e irritante quando erra. Um seletor de idioma permanente só no header é menos descobrível para um visitante de primeira viagem comparando preços. Um cookie exigiria tratamento de consentimento para uma preferência que não precisa persistir além da sessão.

**Consequências.** O visitante escolhe, a escolha é reversível, e nada é guardado entre sessões. O custo é uma decisão extra antes do conteúdo em uma primeira visita, e uma interação de teclado que precisou de um botão de continuar separado para não navegar enquanto se percorrem as opções com Tab. A lista de regiões é um mapeamento fixo, então um novo mercado é uma mudança de conteúdo, não de configuração.
