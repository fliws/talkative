from talkative.safety import SafetyGuards


def test_dedupe_and_cooldown():
    s = SafetyGuards(dedupe_window=2)
    assert not s.is_duplicate("hello")
    assert s.is_duplicate("Hello")
    # Initially allowed
    assert s.can_post(1, 1, "a")
    # After cooldown set in future, it should block
    s.cooldown(1, 1, "a", 1.0)
    assert not s.can_post(1, 1, "a")
