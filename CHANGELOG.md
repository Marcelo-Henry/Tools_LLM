# Changelog - v2.0

## 🎉 Novas Funcionalidades

### 1. Sistema de Undo
- **Snapshots automáticos**: Backup antes de write/edit/delete
- **Comando `/undo`**: Reverte última operação
- **Histórico persistente**: Salvo em `.undo_history/`
- **Restauração inteligente**: 
  - write/edit → restaura versão anterior
  - delete → recupera arquivo deletado
  - Rollback seguro em caso de erro

**Exemplo:**
```bash
> crie arquivo test.txt com "hello"
[write_file] ✓ Executado
> delete test.txt
[delete_file] Arquivo deletado
> /undo
✅ Restaurado: ./sandbox/test.txt
```

### 2. Planejamento Multi-Step
- **Detecção automática**: Identifica tarefas complexas
- **Preview do plano**: Mostra todas as ações antes de executar
- **Confirmação interativa**: Usuário aprova/rejeita (y/n)
- **Keywords detectadas**: todos, cada, múltiplos, delete, analise, procure

**Exemplo:**
```bash
> delete todos os arquivos que dizem "temp"

🤔 Analisando tarefa...

📋 Plano de execução:

  1. Listar arquivos no diretório
  2. Ler conteúdo de cada arquivo
  3. Identificar arquivos com "temp"
  4. Deletar arquivos identificados
  5. Reportar resultado

Executar este plano? (y/n): y
```

### 3. Gerenciamento de Contexto
- **Compressão de histórico**: Resume mensagens antigas automaticamente
- **Truncamento de outputs**: Limita outputs longos (500 chars)
- **Estimativa de tokens**: Previne overflow de context window
- **Resumo inteligente**: Preserva informações essenciais

**Comportamento:**
- Mantém últimas 4 mensagens completas
- Resume histórico antigo em 1 mensagem
- Trunca outputs >500 chars (mostra início + fim)
- Limite padrão: 6000 tokens

## 🔧 Arquivos Adicionados

- `undo_system.py` - Sistema de snapshots e rollback
- `planner.py` - Detecção e planejamento de tarefas
- `context_manager.py` - Compressão e truncamento

## 📝 Modificações

### agent.py
- Importa `ContextManager`
- Adiciona `self.context_manager` no `__init__`
- Substitui lógica de histórico por `compress_history()`
- Trunca outputs longos com `truncate_output()`

### tools.py
- Importa `UndoSystem`
- Adiciona `undo.snapshot()` antes de write/edit/delete
- Expõe `undo` para uso em main.py

### main.py
- Adiciona comando `/undo`
- Integra `Planner` no loop principal
- Detecta tarefas complexas automaticamente
- Solicita confirmação quando necessário

## 🎯 Impacto

**Segurança:**
- ✅ Operações destrutivas agora são reversíveis
- ✅ Confirmação antes de ações em lote
- ✅ Histórico completo de modificações

**Estabilidade:**
- ✅ Previne overflow de context window
- ✅ Mantém conversas longas funcionais
- ✅ Outputs grandes não quebram o sistema

**UX:**
- ✅ Transparência: usuário vê o plano antes
- ✅ Controle: pode cancelar operações
- ✅ Confiança: pode desfazer erros

## 🧪 Testes

Todos os sistemas foram testados e validados:
- ✅ Undo: snapshot, restore, rollback
- ✅ Context: compressão, truncamento, estimativa
- ✅ Planner: detecção, geração de plano, confirmação
- ✅ Integração: todos os módulos funcionando juntos
