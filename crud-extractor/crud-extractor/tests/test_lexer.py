import pytest

from crud.lexer import LexError, TokenType as T, tokenize


def types(src):
    return [t.type for t in tokenize(src)]


def values(src):
    return [t.value for t in tokenize(src) if t.type != T.EOF]


def test_token_dasar():
    assert types("SELECT id FROM t;") == [T.KEYWORD, T.IDENT, T.KEYWORD, T.IDENT, T.SEMICOLON, T.EOF]


def test_keyword_huruf_kecil():
    toks = tokenize("select id from t")
    assert toks[0].type == T.KEYWORD and toks[0].value == "SELECT"
    assert toks[2].type == T.KEYWORD and toks[2].value == "FROM"


def test_operator_multi_karakter():
    assert values("a <= 1 >= 2 != 3") == ["a", "<=", "1", ">=", "2", "!=", "3"]


def test_parameter():
    toks = tokenize("? :id :batas_awal")
    assert [t.type for t in toks[:3]] == [T.PARAM, T.PARAM, T.PARAM]
    assert [t.value for t in toks[:3]] == ["?", ":id", ":batas_awal"]


def test_komentar_baris():
    toks = tokenize("-- hapus data lama\nSELECT")
    assert toks[0].value == "SELECT" and toks[0].line == 2


def test_komentar_blok():
    toks = tokenize("/* komentar\n   dua baris */ SELECT")
    assert toks[0].value == "SELECT" and toks[0].line == 2


def test_string_biasa():
    toks = tokenize("'LUNAS'")
    assert toks[0].type == T.STRING and toks[0].value == "LUNAS"


def test_posisi_token():
    toks = tokenize("SELECT a\n  FROM t")
    assert (toks[2].line, toks[2].col) == (2, 3)


def test_karakter_tidak_dikenal():
    with pytest.raises(LexError) as info:
        tokenize("SELECT\n$")
    assert info.value.line == 2



def test_l1_keyword_huruf_kecil_dikenali():
    assert types("select id from t") == [T.KEYWORD, T.IDENT, T.KEYWORD, T.IDENT, T.EOF]


def test_l1_keyword_dinormalisasi_ke_huruf_besar():
    assert values("select id from t") == ["SELECT", "id", "FROM", "t"]
    assert values("SeLeCt id FrOm t") == ["SELECT", "id", "FROM", "t"]


def test_l1_identifier_tetap_huruf_asli():
    # perbaikan tidak boleh ikut mengubah identifier biasa
    assert values("SELECT Users FROM Orders") == ["SELECT", "Users", "FROM", "Orders"]
    assert types("selected") == [T.IDENT, T.EOF]



def test_l2_operator_tidak_sama_satu_token():
    assert values("a <> b") == ["a", "<>", "b"]
    assert values("a<>b") == ["a", "<>", "b"]
    assert types("a <> b") == [T.IDENT, T.OP, T.IDENT, T.EOF]


def test_l2_operator_lain_tidak_berubah():
    # penjaga: harus lulus sebelum dan sesudah perbaikan
    assert values("a < b") == ["a", "<", "b"]
    assert values("a <= b") == ["a", "<=", "b"]
    assert values("a > b") == ["a", ">", "b"]


def test_l3_kutip_ganda_jadi_satu_string():
    toks = [(t.type, t.value) for t in tokenize("'it''s'") if t.type != T.EOF]
    assert toks == [(T.STRING, "it's")]


def test_l3_string_biasa_tidak_berubah():
    # penjaga: harus lulus sebelum dan sesudah perbaikan
    assert values("'abc'") == ["abc"]
    assert values("''") == [""]
    assert types("'abc' 'def'") == [T.STRING, T.STRING, T.EOF]



def test_t3_komentar_blok_dilewati():
    assert values("SELECT /* catatan */ id FROM t") == ["SELECT", "id", "FROM", "t"]
    assert values("/* hanya komentar */") == []


def test_t3_komentar_blok_banyak_baris_menjaga_nomor_baris():
    toks = [t for t in tokenize("/* a\nb\nc */\nSELECT") if t.type != T.EOF]
    assert [t.value for t in toks] == ["SELECT"]
    assert toks[0].line == 4


def test_t3_komentar_blok_tidak_ditutup():
    with pytest.raises(LexError, match="tidak ditutup"):
        tokenize("SELECT /* tidak ditutup")