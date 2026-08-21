import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Política de Privacidade | freela-food",
  description: "Política de privacidade do freela-food — LGPD-compliant, proteção de dados desde o primeiro commit.",
};

export default function PrivacidadePage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-20">
      <h1
        className="text-4xl md:text-5xl font-bold mb-8"
        style={{ fontFamily: "var(--font-heading)" }}
      >
        Política de Privacidade
      </h1>

      <div className="prose prose-gray max-w-none space-y-6 text-muted-foreground">
        <p className="text-sm italic">Última atualização: agosto de 2026</p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          1. Introdução
        </h2>
        <p>
          O freela-food respeita sua privacidade e está em conformidade com a Lei Geral de Proteção de Dados (LGPD).
          Esta política explica como coletamos, usamos e protegemos seus dados.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          2. Dados coletados
        </h2>
        <p>Coletamos:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li><strong>Cadastro:</strong> nome, email, senha (hash), telefone, endereço, CPF/CNPJ (criptografados).</li>
          <li><strong>Perfil profissional:</strong> skills, certificações, disponibilidade, área de atuação.</li>
          <li><strong>Contratos:</strong> datas, valores, status, histórico de trabalhos.</li>
          <li><strong>Avaliações:</strong> ratings e comentários de outros usuários.</li>
          <li><strong>Técnico:</strong> endereço IP, agente de navegador, logs de acesso.</li>
        </ul>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          3. Criptografia e segurança
        </h2>
        <ul className="list-disc pl-6 space-y-2">
          <li>CPF e RG são criptografados em repouso (pgcrypto).</li>
          <li>Senhas são hash com bcrypt (cost factor ≥ 12).</li>
          <li>Comunicação via HTTPS (TLS 1.2+).</li>
          <li>Acesso ao banco de dados protegido por IP whitelist.</li>
        </ul>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          4. Uso dos dados
        </h2>
        <p>Seus dados são usados para:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Autenticação e gerenciamento de conta.</li>
          <li>Matching entre freelancers e estabelecimentos.</li>
          <li>Notificações sobre oportunidades, convites e contratos.</li>
          <li>Auditoria e compliance (registro de todas as operações sensíveis).</li>
          <li>Moderação e prevenção de abuso.</li>
        </ul>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          5. Compartilhamento de dados
        </h2>
        <p>
          Seus dados <strong>não são vendidos</strong> a terceiros. Compartilhamos informações apenas quando necessário para:
        </p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Executar contratos (ex: dados visíveis no contrato para ambas as partes).</li>
          <li>Cumprir obrigações legais (ordem judicial).</li>
          <li>Provedores de infraestrutura (AWS, etc.) sob contrato de confidencialidade.</li>
        </ul>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          6. Seus direitos (LGPD)
        </h2>
        <p>Você tem o direito de:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li><strong>Acesso:</strong> solicitar cópia de todos os seus dados. Use <code className="text-sm bg-muted px-2 py-1 rounded">GET /me/export</code>.</li>
          <li><strong>Retificação:</strong> corrigir informações incorretas.</li>
          <li><strong>Exclusão:</strong> solicitar exclusão permanente de sua conta. Use <code className="text-sm bg-muted px-2 py-1 rounded">DELETE /me</code>.</li>
          <li><strong>Portabilidade:</strong> receber seus dados em formato estruturado.</li>
          <li><strong>Oposição:</strong> recusar uso para fins específicos.</li>
        </ul>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          7. Logs e auditoria
        </h2>
        <p>
          Mantemos um registro de auditoria de todas as operações sensíveis: login, mudanças de perfil,
          criação/aceitação de contratos, pagamentos. Esses logs incluem timestamp, IP, agente de navegador
          e ação realizada. Logs são retidos por 12 meses.
        </p>
        <p>
          Dados pessoais (CPF, email, telefone, senha) nunca aparecem em logs — filtro automático os remove.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          8. Cookies e rastreamento
        </h2>
        <p>
          Usamos cookies apenas para autenticação (JWT) e preferências de sessão. Não rastreamos você fora da plataforma.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          9. Retenção de dados
        </h2>
        <p>
          Após exclusão de conta, seus dados pessoais são anonimizados ou deletados em até 30 dias.
          Históricos de contratos podem ser retidos anonimizados para fins estatísticos.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          10. Alterações na política
        </h2>
        <p>
          Podemos atualizar esta política. Você será notificado de mudanças significativas com
          pelo menos 30 dias de antecedência.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          11. Contato — Encarregado de Proteção de Dados
        </h2>
        <p>
          Para questões sobre privacidade ou para exercer seus direitos LGPD, entre em contato:
        </p>
        <p>
          <strong>Email:</strong>{" "}
          <a href="mailto:privacidade@freela-food.com.br" className="text-primary hover:underline">
            privacidade@freela-food.com.br
          </a>
        </p>
      </div>
    </div>
  );
}
