"""Validadores de documentos brasileiros (CPF, CNPJ, CEP)."""

import re


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def normalize_cpf(cpf: str) -> str:
    """Remove tudo que não é dígito."""
    return _digits(cpf)


def is_valid_cpf(cpf: str) -> bool:
    """Valida CPF brasileiro: 11 dígitos + 2 dígitos verificadores."""
    cpf = _digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    s1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (s1 * 10 % 11) % 10
    if d1 != int(cpf[9]):
        return False
    s2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (s2 * 10 % 11) % 10
    return d2 == int(cpf[10])


def normalize_cnpj(cnpj: str) -> str:
    return _digits(cnpj)


def is_valid_cnpj(cnpj: str) -> bool:
    """Valida CNPJ brasileiro: 14 dígitos + 2 dígitos verificadores."""
    cnpj = _digits(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, *weights1]
    s1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
    d1 = (s1 % 11)
    d1 = 0 if d1 < 2 else 11 - d1
    if d1 != int(cnpj[12]):
        return False
    s2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
    d2 = (s2 % 11)
    d2 = 0 if d2 < 2 else 11 - d2
    return d2 == int(cnpj[13])


def normalize_cep(cep: str) -> str:
    return _digits(cep)


def is_valid_cep(cep: str) -> bool:
    cep = _digits(cep)
    return len(cep) == 8
