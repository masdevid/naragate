import pytest

from app.services.case_study import (
    CASE_STUDIES, CaseStudy, timing_status, run_case_study,
    run_case_studies, summarize, format_report_markdown,
)


class TestPennyTestAcceptance:
    def test_real_flip_from_mixed_to_clear_exists(self):
        summary = run_case_studies()
        assert len(summary["flips"]) >= 1, (
            "At least one real claim must flip MIXED -> SUPPORTED/CONTRADICTED"
        )
        flipped = summary["flips"][0]
        assert flipped["before"]["verdict"] == "mixed"
        assert flipped["after"]["verdict"] in ("supported", "contradicted")

    def test_negative_controls_unchanged(self):
        summary = run_case_studies()
        assert summary["control_deltas"], "expected negative controls in the run"
        assert all(abs(d) < 1e-9 for d in summary["control_deltas"])

    def test_negative_control_verdict_identical(self):
        for study in [s for s in CASE_STUDIES if s.is_control]:
            result = run_case_study(study)
            assert result["before"]["verdict"] == result["after"]["verdict"]
            assert round(result["delta"], 4) == 0

    def test_timing_violation_never_signals(self):
        for r in run_case_studies()["real"]:
            if r["timing"] == "VIOLATION":
                assert r["signal_allowed"] is False
                assert r["after"]["policy_dimension"] == 50.0

    def test_timing_ok_case(self):
        result = run_case_study(next(s for s in CASE_STUDIES if s.id == "bbm_subsidi_q3_2025"))
        assert result["timing"] == "OK"
        assert result["signal_allowed"] is True

    def test_report_states_pass_fail(self):
        summary = run_case_studies()
        report = format_report_markdown(summary)
        assert "**PASS**" in report or "**FAIL**" in report
        assert "Claims flipped MIXED -> clear" in report
        assert "Negative control max |delta|" in report


class TestTimingStatus:
    def test_ok(self):
        study = CaseStudy(
            id="x", title="x", narrative="x", sector="coal", members=["ADRO"],
            category="market", direction="above",
            policy_reaction={"policy_date": "2025-06-09", "post_return": 3.0, "prior_return": 0.0},
        )
        assert timing_status(study)[0] == "OK"

    def test_violation_when_prior_period_moves(self):
        study = CaseStudy(
            id="x", title="x", narrative="x", sector="coal", members=["ADRO"],
            category="market", direction="above",
            policy_reaction={"policy_date": "2025-06-09", "post_return": 3.0, "prior_return": 1.0},
        )
        status, note = timing_status(study)
        assert status == "VIOLATION"
        assert "prior period" in note

    def test_inert_when_post_move_too_small(self):
        study = CaseStudy(
            id="x", title="x", narrative="x", sector="coal", members=["ADRO"],
            category="market", direction="above",
            policy_reaction={"policy_date": "2025-06-09", "post_return": 0.1, "prior_return": 0.0},
        )
        assert timing_status(study)[0] == "INERT"

    def test_control_no_timing_check(self):
        study = CaseStudy(
            id="x", title="x", narrative="x", sector="coal", members=["ADRO"],
            category="market", direction="above", is_control=True,
        )
        assert timing_status(study)[0] == "N/A"


class TestSummarize:
    def test_pass_requires_flip_controls_and_timing(self):
        control = {
            "id": "c", "is_control": True, "direction": "above", "category": "market",
            "before": {"verdict": "mixed", "score": 50.0},
            "after": {"verdict": "mixed", "score": 50.0},
            "delta": 0.0, "flip": False, "contradiction_added": False,
            "timing": "N/A", "timing_note": "", "signal_allowed": False,
        }
        good = {
            "id": "r", "is_control": False, "direction": "above", "category": "market",
            "before": {"verdict": "mixed", "score": 50.0},
            "after": {"verdict": "supported", "score": 70.0},
            "delta": 20.0, "flip": True, "contradiction_added": False,
            "timing": "OK", "timing_note": "", "signal_allowed": True,
        }

        failing_by_no_flip = summarize([dict(good, flip=False, after={"verdict": "mixed", "score": 50.0}), control])
        assert failing_by_no_flip["pass"] is False

        failing_by_control_delta = summarize([good, dict(control, delta=5.0)])
        assert failing_by_control_delta["pass"] is False

        # A timing violation that produced a signal must fail the run.
        violating_with_signal = dict(good, timing="VIOLATION", signal_allowed=True)
        failing_by_violation_signal = summarize([violating_with_signal, control])
        assert failing_by_violation_signal["pass"] is False

        # A suppressed violation (no signal) is expected discipline, not a failure.
        suppressed_violation = dict(good, flip=False, timing="VIOLATION", signal_allowed=False,
                                    before={"verdict": "mixed", "score": 54.0},
                                    after={"verdict": "mixed", "score": 54.0}, delta=0.0)
        passing_with_suppressed_violation = summarize([good, suppressed_violation, control])
        assert passing_with_suppressed_violation["pass"] is True

        passing = summarize([good, control])
        assert passing["pass"] is True