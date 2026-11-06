import pytest

from crud import ast_nodes as ast
from crud.lexer import tokenize, LexError
from crud.parser import parse_sql
from crud.resolver import Resolver


def _first(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    return script.statements[0]


# ================= Regresi bug milik Abi (Parser) =================
def test_regresi_p2_synchronize_berhenti_setelah_titik_koma():
    # Sebelum perbaikan: statement valid setelah yang rusak ikut terbuang (1 0).
    script = parse_sql("SELEKT x; SELECT id FROM t;")
    assert len(script.errors) == 1
    assert len(script.statements) == 1


def test_regresi_p3_left_outer_join_diterima():
    # Sebelum perbaikan: OUTER setelah LEFT menimbulkan ParseError.
    script = parse_sql("SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id")
    assert script.errors == []


def test_regresi_t1_insert_select_diterima():
    # Sebelum perbaikan: "INSERT ... SELECT belum didukung".
    s = _first("INSERT INTO arsip (id) SELECT id FROM pesanan")
    assert isinstance(s, ast.Insert)
    assert s.query is not None


# ================= Kasus tepi (2 dari Abi, untuk modul Lexer/Resolver) =================
def test_tepi_komentar_blok_tidak_ditutup():
    # Risiko: komentar /* tanpa penutup menggantung diam-diam, atau loop tak berhenti.
    with pytest.raises(LexError):
        tokenize("SELECT 1 /* belum ditutup")


def test_tepi_kolom_ambigu_dua_tabel():
    # Risiko: kolom tanpa qualifier di scope 2 tabel salah ditebak ke satu tabel.
    script = parse_sql("SELECT nama FROM a, b")
    diags = Resolver().resolve_script(script)
    assert [d.level for d in diags] == ["warning"]