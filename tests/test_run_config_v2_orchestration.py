from core.run_config_v2 import RunConfig


def test_v2_default_promotion_is_explicitly_disabled():
    config = RunConfig()
    args = config.to_engine_args()
    assert config.promote_orchestrated_template is False
    assert "--no-orchestrator-template-promotion" in args
    assert "--promote-orchestrated-template" not in args


def test_v2_opt_in_promotion_is_serialized_and_round_trips():
    config = RunConfig(promote_orchestrated_template=True)
    args = config.to_engine_args()
    assert "--promote-orchestrated-template" in args
    assert "--no-orchestrator-template-promotion" not in args
    recovered = RunConfig.from_engine_args("master", args)
    assert recovered.promote_orchestrated_template is True
