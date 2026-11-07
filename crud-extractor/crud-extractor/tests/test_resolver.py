from crud import ast_nodes as ast
from crud.parser import parse_sql
from crud.resolver import Resolver


def resolve(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    diagnostics = Resolver().resolve_script(script)
    return script, diagnostics


def columns(node):
    return [n for n in ast.iter_nodes(node) if isinstance(n, ast.ColumnRef)]


def test_alias_qualified_teresolusi():
    script, diags = resolve("SELECT p.nama FROM pelanggan p JOIN pesanan o ON o.pelanggan_id = p.id")
    resolved = {(c.qualifier, c.name): c.resolved for c in columns(script)}
    assert resolved[("p", "nama")] == "pelanggan"
    assert resolved[("o", "pelanggan_id")] == "pesanan"
    assert diags == []


def test_alias_tidak_terdefinisi():
    _, diags = resolve("SELECT q.nama FROM pelanggan p")
    assert [d.level for d in diags] == ["error"]
    assert "'q'" in diags[0].message


def test_kolom_tanpa_qualifier_satu_tabel():
    script, diags = resolve("SELECT nama FROM pelanggan WHERE aktif = 1")
    assert {c.resolved for c in columns(script)} == {"pelanggan"}
    assert diags == []


def test_subquery_in_alias_dalam():
    script, diags = resolve(
        "SELECT p.id FROM pelanggan p WHERE p.id IN (SELECT o.pelanggan_id FROM pesanan o)")
    inner = [c for c in columns(script) if c.qualifier == "o"][0]
    assert inner.resolved == "pesanan"
    assert diags == []



def test_r1_alias_sama_dipakai_scope_terdalam():
    script, diagnostics = resolve(
        "SELECT p.id FROM pelanggan p "
        "WHERE p.id IN (SELECT p.pelanggan_id FROM pesanan p)"
    )
    resolved = {c.name: c.resolved for c in columns(script)}
    assert resolved["id"] == "pelanggan"
    assert resolved["pelanggan_id"] == "pesanan"


def test_r1_alias_luar_tetap_terlihat_dari_subquery():
    # penjaga: harus lulus sebelum dan sesudah perbaikan
    script, diagnostics = resolve(
        "SELECT p.id FROM pelanggan p "
        "WHERE p.id IN (SELECT o.pelanggan_id FROM pesanan o)"
    )
    resolved = {c.name: c.resolved for c in columns(script)}
    assert resolved["id"] == "pelanggan"
    assert resolved["pelanggan_id"] == "pesanan"

def test_r2_alias_delete_tidak_bocor_ke_statement_berikutnya():
    _, diagnostics = resolve(
        "DELETE FROM pelanggan WHERE pelanggan.id = 1; "
        "SELECT pelanggan.nama FROM pesanan o"
    )
    assert [d.level for d in diagnostics] == ["error"]
    assert "'pelanggan'" in diagnostics[0].message


def test_r2_delete_sendiri_tetap_teresolusi():
    script, diagnostics = resolve("DELETE FROM pelanggan WHERE pelanggan.id = 1")
    assert {c.resolved for c in columns(script)} == {"pelanggan"}
    assert diagnostics == []

def test_t2_kolom_tanpa_qualifier_scope_terdalam():
    script, diagnostics = resolve(
        "SELECT p.id FROM pelanggan p "
        "WHERE p.id IN (SELECT pelanggan_id FROM pesanan o)"
    )
    inner = [c for c in columns(script) if c.name == "pelanggan_id"][0]
    assert inner.resolved == "pesanan"
    assert diagnostics == []


def test_t2_kolom_tanpa_qualifier_ambigu_beri_warning():
    script, diagnostics = resolve(
        "SELECT nama FROM pelanggan p JOIN pesanan o ON o.pelanggan_id = p.id"
    )
    nama = [c for c in columns(script) if c.name == "nama"][0]
    assert nama.resolved is None
    assert [d.level for d in diagnostics] == ["warning"]
    assert "ambigu" in diagnostics[0].message