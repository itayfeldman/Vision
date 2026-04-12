export interface Holding {
  ticker: string;
  weight: number;
}

export interface Portfolio {
  id: string;
  name: string;
  holdings: Holding[];
}

export interface ValuedHolding {
  ticker: string;
  weight: number;
  current_price: number;
  shares: number;
  market_value: number;
}

export interface ValuedPortfolio {
  id: string;
  name: string;
  holdings: ValuedHolding[];
  total_value: number;
}

export interface RiskSummary {
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  var_95: number;
}

export interface FactorExposureSummary {
  factor_name: string;
  beta: number;
}

export interface PortfolioSummary {
  id: string;
  name: string;
  holdings: Holding[];
  risk: RiskSummary;
  factor_exposures: FactorExposureSummary[];
}

export interface RiskMetrics {
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  max_drawdown_duration: number;
  var_95: number;
  var_99: number;
  cvar_95: number;
  cvar_99: number;
}

export interface CorrelationMatrix {
  tickers: string[];
  matrix: number[][];
}

export interface RiskReport {
  metrics: RiskMetrics;
  correlation: CorrelationMatrix;
}

export interface FactorExposure {
  factor_name: string;
  beta: number;
  t_statistic: number;
  p_value: number;
}

export interface FactorDecomposition {
  exposures: FactorExposure[];
  r_squared: number;
  alpha: number;
  alpha_t_stat: number;
  residual_risk: number;
}

export interface PerformancePoint {
  date: string;
  cumulative_return: number;
  volume: number;
}

export interface PerformanceSeries {
  points: PerformancePoint[];
}

export interface WeightConstraint {
  ticker: string;
  min_weight: number;
  max_weight: number;
}

export interface OptimizeRequest {
  tickers: string[];
  objective: string;
  constraints?: WeightConstraint[];
  lookback_years?: number;
}

export interface OptimizeResult {
  weights: Record<string, number>;
  expected_return: number;
  expected_volatility: number;
  sharpe_ratio: number;
}

export interface FrontierPoint {
  expected_return: number;
  expected_volatility: number;
  sharpe_ratio: number;
  weights: Record<string, number>;
}

export interface FrontierRequest {
  tickers: string[];
  constraints?: WeightConstraint[];
  lookback_years?: number;
  points?: number;
}

export interface FrontierResult {
  points: FrontierPoint[];
  min_volatility: FrontierPoint;
  max_sharpe: FrontierPoint;
  equal_weight: FrontierPoint;
}

export interface SpreadPoint {
  date: string;
  portfolio_cum: number;
  benchmark_cum: number;
  spread: number;
}

export interface PriceHistory {
  ticker: string;
  dates: string[];
  close_prices: number[];
  volumes: number[];
}

export interface BenchmarkComparison {
  benchmark_ticker: string;
  tracking_error: number;
  beta: number;
  alpha: number;
  up_capture: number;
  down_capture: number;
  spread_series: SpreadPoint[];
}
