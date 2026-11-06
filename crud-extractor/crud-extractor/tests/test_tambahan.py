import pytest

from crud import ast_nodes as ast
from crud.lexer import tokenize, LexError
from crud.parser import parse_sql
from crud.resolver import Resolver
from crud.analyzer import analyze_statement


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

def test_regresi_p1_presedensi_and_lebih_kuat_dari_or():
    # Sebelum perbaikan: semua operator di satu tingkat, "a OR b AND c"
    # terbaca (a OR b) AND c.
    s = _first("SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3")
    assert s.where.op == "OR"
    assert s.where.right.op == "AND"


def test_regresi_p1_not_lebih_kuat_dari_and():
    # Pengaman: NOT sudah benar sebelum P1 (hanya mengikat satu perbandingan).
    # Tes ini menjaga agar rantai _or -> _and -> _not tidak merusaknya.
    s = _first("SELECT id FROM t WHERE NOT a = 1 AND b = 2")
    assert s.where.op == "AND"
    assert isinstance(s.where.left, ast.UnaryOp)
    assert s.where.left.op == "NOT"


def test_regresi_a1_subquery_update_hanya_target_yang_u():
    # Sebelum perbaikan: tabel di subquery UPDATE ikut ditandai U.
    script = parse_sql("UPDATE a SET x = 1 WHERE id IN (SELECT a_id FROM b)")
    assert script.errors == []
    assert analyze_statement(script.statements[0]) == {"a": {"U"}, "b": {"R"}}

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