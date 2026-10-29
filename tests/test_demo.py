def validar_soma(x: int, y: int) -> int:
    return x + y

def test_validar_soma() -> None:
    assert validar_soma(20, 30) == 50
