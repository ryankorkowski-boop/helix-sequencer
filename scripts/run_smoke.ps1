python -m compileall core ai xlights tools tests main.py gui_launcher.py
python main.py --list-profiles
python -m pytest -q tests/test_sequence_builder.py tests/test_effects_orchestrator_bridge.py tests/test_xlights_contract_validator.py
