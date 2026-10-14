import time

from engines.live_data.dhan_live_service import DhanLiveService
from engines.live_hedge_universe import build_live_hedge_universe
from engines.hedging_optimizer_v02 import optimize_single_v02


SCENARIOS = [
    (
        "BALANCED",
        {
            "Delta": 42.0,
            "Gamma": -0.65,
            "Vega": -18.0,
            "Theta": -7.0,
        },
    ),
    (
        "BULLISH",
        {
            "Delta": 80.0,
            "Gamma": -0.40,
            "Vega": -10.0,
            "Theta": -5.0,
        },
    ),
    (
        "BEARISH",
        {
            "Delta": -80.0,
            "Gamma": -0.40,
            "Vega": -10.0,
            "Theta": -5.0,
        },
    ),
    (
        "SHORT_GAMMA",
        {
            "Delta": 20.0,
            "Gamma": -1.20,
            "Vega": -20.0,
            "Theta": -10.0,
        },
    ),
    (
        "LONG_GAMMA",
        {
            "Delta": 20.0,
            "Gamma": 1.20,
            "Vega": -20.0,
            "Theta": -10.0,
        },
    ),
    (
        "HIGH_VEGA",
        {
            "Delta": 20.0,
            "Gamma": -0.50,
            "Vega": -60.0,
            "Theta": -8.0,
        },
    ),
    (
        "LOW_VEGA",
        {
            "Delta": 20.0,
            "Gamma": -0.50,
            "Vega": -5.0,
            "Theta": -8.0,
        },
    ),
]


def main():
    print("=== IFIT HEDGING V0.2.3 ADAPTIVE MULTI-SCENARIO LIVE QA ===")
    print("Starting Dhan live service...")

    service = DhanLiveService()
    service.start()

    time.sleep(3)

    universe = build_live_hedge_universe(service)

    print("LIVE_CANDIDATES=", len(universe))
    print()

    green = 0
    yellow = 0
    red = 0


    for name, portfolio in SCENARIOS:

        before = (
            0.45 * abs(portfolio["Delta"])
            + 25.0 * abs(portfolio["Gamma"])
            + 0.20 * abs(portfolio["Vega"])
        )

        result = optimize_single_v02(
            portfolio,
            universe,
        )

        print("SCENARIO=", name)
        print("BEFORE_CORE_RISK=", round(before, 4))
        print("VALID_HEDGES=", len(result))

        if result.empty:
            print("STATUS=RED | NO EFFECTIVE HEDGE")
            red += 1
            print()
            continue

        best = result.iloc[0]

        after = float(best["After Core Risk"])
        reduction = float(best["Core Risk Reduction"])
        status = str(best["Target Status"])

        # --------------------------------------------------------
        # Adaptive QA classification
        #
        # GREEN:
        #   Core risk reduced + all preferred Greek targets met
        #
        # YELLOW:
        #   Core risk reduced, but one or more preferred
        #   Greek targets remain outside target range
        #
        # RED:
        #   No effective hedge
        # --------------------------------------------------------

        if after >= before or reduction <= 0:
            qa_status = "RED"
            red += 1

        elif status == "GREEN":
            qa_status = "GREEN"
            green += 1

        else:
            qa_status = "YELLOW"
            yellow += 1

        print("BEST=", best["Instrument"])
        print("TYPE=", best["Type"])
        print("QUANTITY=", int(best["Quantity"]))

        print(
            "AFTER_CORE_RISK=",
            round(after, 4),
        )

        print(
            "CORE_REDUCTION_PCT=",
            round(
                float(
                    best["Core Risk Reduction %"]
                ),
                4,
            ),
        )

        print(
            "DELTA=",
            round(float(best["Delta"]), 4),
        )

        print(
            "GAMMA=",
            round(float(best["Gamma"]), 4),
        )

        print(
            "VEGA=",
            round(float(best["Vega"]), 4),
        )

        print(
            "THETA=",
            round(float(best["Theta"]), 4),
        )

        print(
            "THETA_DETERIORATION=",
            round(
                float(
                    best["Theta Deterioration"]
                ),
                4,
            ),
        )

        print(
            "TARGET_STATUS=",
            status,
        )

        print(
            "FAILED_TARGETS=",
            best["Failed Targets"],
        )

        print(
            "COST=",
            round(float(best["Hedge Cost"]), 2),
        )

        print(
            "LIQUIDITY=",
            round(
                float(best["Liquidity Score"]),
                2,
            ),
        )

        print(
            "SCORE=",
            round(
                float(best["V0.2 Score"]),
                4,
            ),
        )

        print(
            "QA_STATUS=",
            qa_status,
        )

        print()


    print("=== FINAL QA SUMMARY ===")
    print("SCENARIOS=", len(SCENARIOS))
    print("GREEN=", green)
    print("YELLOW=", yellow)
    print("RED=", red)

    if red == 0:
        print("V0.2.3 ADAPTIVE QA=PASS")
    else:
        print("V0.2.3 ADAPTIVE QA=REVIEW")

    service.close()

    print("=== QA COMPLETE ===")
if __name__ == "__main__":
    main()
