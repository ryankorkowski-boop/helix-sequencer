from market_pulse.signals import SignalEngine

def test_volume_anomaly():
    e = SignalEngine(window=20)
    for _ in range(12):
        e.update("TEST", 100.0, 100.0)
    signals = e.update("TEST", 100.0, 500.0)
    assert any(s.kind == "volume_anomaly" for s in signals)

def test_price_anomaly():
    e = SignalEngine(window=20)
    for _ in range(12):
        e.update("TEST", 100.0, 100.0)
    signals = e.update("TEST", 110.0, 100.0)
    assert any(s.kind == "price_anomaly" for s in signals)
