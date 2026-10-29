def processar_dados(dados: list[int]) -> list[int]:
    return [valor * 2 for valor in dados]


def test_processar_dados_duplica_os_valores() -> None:
    assert processar_dados([1, 2, 3]) == [2, 4, 6]
