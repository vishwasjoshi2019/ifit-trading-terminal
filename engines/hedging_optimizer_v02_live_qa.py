import time

from engines.live_data.dhan_live_service import DhanLiveService
from engines.live_hedge_universe import build_live_hedge_universe
from engines.hedging_engine import (
    PortfolioExposure,
    _risk_distance,
    _apply_hedge,
)


def main():
    print("=== IFIT HEDGING V0.2 LIVE QA ===")

    # ---------------------------------------------------------
    # 1. Start live Dhan service
    # ---------------------------------------------------------
    print("Starting Dhan live service...")

    service = DhanLiveService()
    service.start()

    time.sleep(3)

    # ---------------------------------------------------------
    # 2. Build live hedge universe
    # ---------------------------------------------------------
    universe = build_live_hedge_universe(service)

    print("LIVE_CANDIDATES=", len(universe))

    if universe.empty:
        print("ERROR: Live hedge universe is empty.")
        service.close()
        return

    # ---------------------------------------------------------
    # 3. Test portfolio
    # ---------------------------------------------------------
    portfolio = PortfolioExposure(
        delta=42.0,
        gamma=-0.65,
        vega=-18.0,
        theta=-7.0,
    )

    baseline_risk = _risk_distance(portfolio)

    print("BASELINE_RISK=", round(baseline_risk, 4))

    # ---------------------------------------------------------
    # 4. Test every live hedge
    # ---------------------------------------------------------
    total_tests = 0
    reducing_tests = 0
    increasing_tests = 0
    unchanged_tests = 0

    best_after_risk = float("inf")
    best_hedge = None

    worst_after_risk = float("-inf")
    worst_hedge = None

    for _, row in universe.iterrows():

        # Convert pandas row to dictionary-like Series.
        hedge = row

        for quantity in range(-10, 11):

            if quantity == 0:
                continue

            total_tests += 1

            # IMPORTANT:
            # _apply_hedge signature is:
            # _apply_hedge(portfolio, hedge, quantity)

            after_exposure = _apply_hedge(
                portfolio,
                hedge,
                quantity,
            )

            after_risk = _risk_distance(after_exposure)

            reduction = baseline_risk - after_risk

            # -------------------------------------------------
            # Risk classification
            # -------------------------------------------------
            if after_risk < baseline_risk:
                reducing_tests += 1

                if after_risk < best_after_risk:
                    best_after_risk = after_risk

                    best_hedge = {
                        "Instrument": hedge.get("Instrument"),
                        "Type": hedge.get("Type"),
                        "Strike": hedge.get("Strike"),
                        "Quantity": quantity,
                        "After Risk": after_risk,
                        "Risk Reduction": reduction,
                        "Cost": abs(quantity)
                        * abs(float(hedge.get("Cost", 0))),
                        "Liquidity": hedge.get(
                            "Liquidity Score"
                        ),
                    }

            elif after_risk > baseline_risk:
                increasing_tests += 1

                if after_risk > worst_after_risk:
                    worst_after_risk = after_risk

                    worst_hedge = {
                        "Instrument": hedge.get("Instrument"),
                        "Type": hedge.get("Type"),
                        "Strike": hedge.get("Strike"),
                        "Quantity": quantity,
                        "After Risk": after_risk,
                        "Risk Change": after_risk
                        - baseline_risk,
                    }

            else:
                unchanged_tests += 1

    # ---------------------------------------------------------
    # 5. Print QA summary
    # ---------------------------------------------------------
    print()
    print("=== LIVE HEDGE QA RESULTS ===")

    print("LIVE_CANDIDATES=", len(universe))
    print("TOTAL_TESTS=", total_tests)

    print(
        "RISK_REDUCING_TESTS=",
        reducing_tests,
    )

    print(
        "RISK_INCREASING_TESTS=",
        increasing_tests,
    )

    print(
        "UNCHANGED_TESTS=",
        unchanged_tests,
    )

    # ---------------------------------------------------------
    # 6. Best hedge
    # ---------------------------------------------------------
    print()
    print("=== BEST RISK-REDUCING HEDGE ===")

    if best_hedge is None:

        print("BEST_HEDGE= NONE")

    else:

        print(
            "Instrument=",
            best_hedge["Instrument"],
        )

        print(
            "Type=",
            best_hedge["Type"],
        )

        print(
            "Strike=",
            best_hedge["Strike"],
        )

        print(
            "Quantity=",
            best_hedge["Quantity"],
        )

        print(
            "After_Risk=",
            round(best_hedge["After Risk"], 4),
        )

        print(
            "Risk_Reduction=",
            round(best_hedge["Risk Reduction"], 4),
        )

        print(
            "Hedge_Cost=",
            round(best_hedge["Cost"], 2),
        )

        print(
            "Liquidity=",
            best_hedge["Liquidity"],
        )

    # ---------------------------------------------------------
    # 7. Worst hedge
    # ---------------------------------------------------------
    print()
    print("=== WORST RISK-INCREASING HEDGE ===")

    if worst_hedge is None:

        print("WORST_HEDGE= NONE")

    else:

        print(
            "Instrument=",
            worst_hedge["Instrument"],
        )

        print(
            "Type=",
            worst_hedge["Type"],
        )

        print(
            "Strike=",
            worst_hedge["Strike"],
        )

        print(
            "Quantity=",
            worst_hedge["Quantity"],
        )

        print(
            "After_Risk=",
            round(worst_hedge["After Risk"], 4),
        )

        print(
            "Risk_Increase=",
            round(worst_hedge["Risk Change"], 4),
        )

    # ---------------------------------------------------------
    # 8. Final QA decision
    # ---------------------------------------------------------
    print()
    print("=== V0.2 QA DECISION ===")

    if reducing_tests > 0:
        print("RISK_REDUCTION_LOGIC= PASS")
    else:
        print("RISK_REDUCTION_LOGIC= FAIL")

    if increasing_tests > 0:
        print(
            "RISK_INCREASE_DETECTION= PASS"
        )
    else:
        print(
            "RISK_INCREASE_DETECTION= NOT_OBSERVED"
        )

    if best_hedge is not None:
        print("BEST_HEDGE_SELECTION= PASS")
    else:
        print("BEST_HEDGE_SELECTION= FAIL")

    # ---------------------------------------------------------
    # 9. Close live service
    # ---------------------------------------------------------
    service.close()

    print()
    print("=== QA COMPLETE ===")


if __name__ == "__main__":
    main()