def test_package_imports() -> None:
    import live15_quant_v2

    assert live15_quant_v2.__all__ == []


def test_data_root_does_not_reexport_child_capabilities() -> None:
    import live15_quant_v2.data as data_public

    assert data_public.__all__ == []
    assert not hasattr(data_public, "KalshiGateway")
