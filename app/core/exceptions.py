"""Hierarquia de erros de domínio e mapeamento HTTP."""

from fastapi import HTTPException, status


class DomainError(Exception):
    """Base de todas as exceções de domínio."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "Erro de domínio"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail is not None:
            self.detail = detail

    def to_http(self) -> HTTPException:
        return HTTPException(status_code=self.status_code, detail=self.detail)


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Recurso não encontrado"


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Conflito de estado"


class PermissionDenied(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Permissão negada"


class ValidationError(DomainError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = "Erro de validação"


class AuthenticationError(DomainError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Credenciais inválidas"


# ── Sprint 3 ────────────────────────────────────────────────────────────────


class JobNotOpen(ConflictError):
    detail = "Vaga não está aberta para candidaturas"


class SelfApplicationForbidden(PermissionDenied):
    detail = "Estabelecimento não pode se candidatar à própria vaga"


class ProfileRequired(ConflictError):
    detail = "É necessário ter perfil de freelancer para candidatar-se"


class DuplicateApplication(ConflictError):
    detail = "Já existe candidatura sua nesta vaga"


class ApplicationNotPending(ConflictError):
    detail = "Candidatura já foi decidida"


class FreelancerOverlap(ConflictError):
    detail = "Freelancer já tem contrato sobreposto no horário"


class ContractAlreadyTerminal(ConflictError):
    detail = "Contrato já está em estado final (completed ou cancelled)"


class NotificationNotFound(NotFoundError):
    detail = "Notificação não encontrada"


# ── Sprint 4 (Fluxo B) ───────────────────────────────────────────────────────


class EstablishmentProfileRequired(ConflictError):
    detail = "É necessário ter perfil de estabelecimento para esta ação"


class InvalidInvitationTarget(DomainError):
    detail = "Convidado precisa ser um freelancer ativo"


class InvalidInvitationWindow(DomainError):
    detail = "Janela do convite inválida (início no futuro e fim após início)"


class DuplicateInvitation(ConflictError):
    detail = "Já existe convite pendente sobreposto para este freelancer"


class InvitationNotPending(ConflictError):
    detail = "Convite já foi decidido"


class InvitationExpired(ConflictError):
    detail = "Convite expirou"


# ── Sprint 5 (Reviews) ───────────────────────────────────────────────────────


class ContractNotCompleted(ConflictError):
    detail = "Contrato precisa estar completed para avaliação"


class ReviewWindowClosed(ConflictError):
    detail = "Janela de avaliação encerrada (30 dias)"


class DuplicateReview(ConflictError):
    detail = "Você já avaliou este contrato"


# ── Sprint 8 (Moderação) ─────────────────────────────────────────────────────


class SelfReportForbidden(PermissionDenied):
    detail = "Não é possível reportar a si mesmo"


class DuplicateReport(ConflictError):
    detail = "Já existe denúncia pendente para este alvo"


class ReportNotPending(ConflictError):
    detail = "Denúncia já foi resolvida"


class ReviewAlreadyHidden(ConflictError):
    detail = "Review já está oculta"


class ReviewNotHidden(ConflictError):
    detail = "Review não está oculta"
