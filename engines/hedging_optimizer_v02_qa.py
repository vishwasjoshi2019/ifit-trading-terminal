from engines.hedging_engine import PortfolioExposure, _risk_distance, _apply_hedge
import pandas as pd

def risk_test(name, portfolio, hedge, quantity):
    before = _risk_distance(portfolio)
    after_exposure = _apply_hedge(portfolio, hedge, quantity)
    after = _risk_distance(after_exposure)
    reduction = before - after
    status = 'PASS' if reduction > 0 else 'REJECT'
    print(f'{name}: {status} | before={before:.4f} | after={after:.4f} | reduction={reduction:.4f}')
    return reduction

if __name__ == '__main__':
    portfolio = PortfolioExposure(delta=42.0, gamma=-0.65, vega=-18.0, theta=-7.0)

    risk_increasing = pd.Series({'Delta': 0.0, 'Gamma': 0.0, 'Vega': 0.0, 'Theta': 20.0})
    risk_reducing = pd.Series({'Delta': -20.0, 'Gamma': 0.10, 'Vega': 5.0, 'Theta': 2.0})

    print('=== IFIT HEDGING V0.2 QA BASELINE ===')
    print('PORTFOLIO RISK=', round(_risk_distance(portfolio), 4))
    print()
    risk_test('RISK-INCREASING HEDGE', portfolio, risk_increasing, 1)
    risk_test('RISK-REDUCING HEDGE', portfolio, risk_reducing, 1)
