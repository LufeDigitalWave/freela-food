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
