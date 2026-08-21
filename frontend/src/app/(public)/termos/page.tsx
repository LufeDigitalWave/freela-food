import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Termos de Uso | freela-food",
  description: "Termos de uso do freela-food — marketplace de food service.",
};

export default function TermosPage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-20">
      <h1
        className="text-4xl md:text-5xl font-bold mb-8"
        style={{ fontFamily: "var(--font-heading)" }}
      >
        Termos de Uso
      </h1>

      <div className="prose prose-gray max-w-none space-y-6 text-muted-foreground">
        <p className="text-sm italic">Última atualização: agosto de 2026</p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          1. Aceitação dos termos
        </h2>
        <p>
          Ao acessar ou usar o freela-food (&ldquo;Plataforma&rdquo;), você concorda com estes Termos de Uso.
          Se não concordar, não utilize a plataforma.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          2. Descrição do serviço
        </h2>
        <p>
          O freela-food é um marketplace bidirecional que conecta profissionais freelancers de food service
          (garçons, bartenders, cozinheiros, auxiliares) a bares, restaurantes e estabelecimentos que precisam
          de mão de obra avulsa.
        </p>
        <p>
          A plataforma facilita a conexão. O freela-food <strong>não é parte</strong> na relação de trabalho
          entre freelancer e estabelecimento.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          3. Cadastro e contas
        </h2>
        <ul className="list-disc pl-6 space-y-2">
          <li>Você deve fornecer informações verídicas no cadastro.</li>
          <li>É responsável por manter a segurança de sua senha.</li>
          <li>Uma conta por pessoa/estabelecimento.</li>
          <li>Menores de 18 anos não podem se cadastrar.</li>
        </ul>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          4. Uso aceitável
        </h2>
        <p>Ao usar a plataforma, você concorda em:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Não publicar informações falsas ou enganosas.</li>
          <li>Não discriminar candidatos por raça, gênero, orientação sexual, religião ou deficiência.</li>
          <li>Respeitar os compromissos firmados (vagas aceitas, horários combinados).</li>
          <li>Não usar a plataforma para atividades ilegais.</li>
        </ul>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          5. Avaliações
        </h2>
        <p>
          Após cada serviço concluído, ambas as partes podem avaliar a outra (1 a 5 estrelas + comentário).
          As avaliações são protegidas por regra anti-retaliação: ficam ocultas até que ambos avaliem ou
          7 dias após a primeira avaliação. Moderação pode ocultar avaliações ofensivas.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          6. Cancelamentos e no-shows
        </h2>
        <p>
          Cancelamentos com menos de 24 horas de antecedência geram registro de &ldquo;no-show&rdquo; público
          no perfil do responsável.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          7. Pagamentos
        </h2>
        <p>
          O freela-food pode intermediar pagamentos via Pix. As condições são acordadas entre freelancer e
          estabelecimento. A plataforma não se responsabiliza por inadimplência entre as partes.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          8. Propriedade intelectual
        </h2>
        <p>
          O código-fonte do freela-food é distribuído sob licença MIT. O conteúdo enviado por usuários
          (avaliações, fotos de perfil) permanece propriedade do autor, com licença de uso pela plataforma.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          9. Limitação de responsabilidade
        </h2>
        <p>
          O freela-food é fornecido &ldquo;como está&rdquo;. Não garantimos disponibilidade ininterrupta,
          resultados de contratação, nem a veracidade das informações fornecidas por outros usuários.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          10. Modificações
        </h2>
        <p>
          Podemos alterar estes termos a qualquer momento. Alterações significativas serão comunicadas
          por notificação na plataforma com pelo menos 30 dias de antecedência.
        </p>

        <h2 className="text-xl font-semibold text-foreground mt-8" style={{ fontFamily: "var(--font-sans)" }}>
          11. Contato
        </h2>
        <p>
          Dúvidas sobre estes termos podem ser enviadas para{" "}
          <a href="mailto:contato@freela-food.com.br" className="text-primary hover:underline">
            contato@freela-food.com.br
          </a>.
        </p>
      </div>
    </div>
  );
}
