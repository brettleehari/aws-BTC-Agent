"""
Technical Indicators Module

Implements common technical analysis indicators:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)

Designed for cryptocurrency trading signals and backtesting.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class PricePoint:
    """Single price data point"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class RSIReading:
    """RSI indicator reading"""
    value: float  # 0-100
    timestamp: datetime
    period: int
    
    # Signal interpretation
    signal: str  # "OVERBOUGHT", "OVERSOLD", "NEUTRAL"
    strength: float  # 0-1 (how strong the signal is)
    
    # Metadata
    avg_gain: float
    avg_loss: float


@dataclass
class MACDReading:
    """MACD indicator reading"""
    macd_line: float  # MACD line (fast EMA - slow EMA)
    signal_line: float  # Signal line (EMA of MACD)
    histogram: float  # MACD - Signal
    timestamp: datetime
    
    # Parameters
    fast_period: int
    slow_period: int
    signal_period: int
    
    # Signal interpretation
    signal: str  # "BULLISH_CROSSOVER", "BEARISH_CROSSOVER", "BULLISH", "BEARISH", "NEUTRAL"
    strength: float  # 0-1
    
    # Divergence detection
    divergence: Optional[str] = None  # "BULLISH_DIVERGENCE", "BEARISH_DIVERGENCE"


@dataclass
class BollingerBands:
    """Bollinger Bands reading"""
    upper_band: float
    middle_band: float  # SMA
    lower_band: float
    bandwidth: float  # Upper - Lower
    percent_b: float  # Where price is relative to bands (0-1)
    timestamp: datetime
    
    # Parameters
    period: int
    std_dev: float
    
    # Signal interpretation
    signal: str  # "OVERBOUGHT", "OVERSOLD", "SQUEEZE", "BREAKOUT", "NEUTRAL"
    volatility: str  # "HIGH", "NORMAL", "LOW"


@dataclass
class MovingAverage:
    """Moving average reading"""
    value: float
    timestamp: datetime
    period: int
    ma_type: str  # "SMA" or "EMA"
    
    # Trend
    trend: str  # "UPTREND", "DOWNTREND", "SIDEWAYS"
    slope: float  # Rate of change


class TechnicalIndicators:
    """
    Technical indicators calculator for cryptocurrency analysis.
    
    Features:
    - RSI with overbought/oversold detection
    - MACD with crossover signals
    - Bollinger Bands with squeeze detection
    - SMA/EMA with trend analysis
    - Signal strength scoring
    - Divergence detection
    """
    
    # RSI thresholds
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    RSI_EXTREME_OVERBOUGHT = 80
    RSI_EXTREME_OVERSOLD = 20
    
    # Bollinger Bands thresholds
    BB_SQUEEZE_THRESHOLD = 0.05  # 5% bandwidth indicates squeeze
    BB_OVERBOUGHT = 0.8  # %B > 80%
    BB_OVERSOLD = 0.2  # %B < 20%
    
    def __init__(self):
        """Initialize technical indicators calculator"""
        self._price_cache: Dict[str, List[PricePoint]] = {}
        logger.info("Technical indicators calculator initialized")
    
    def calculate_rsi(
        self,
        prices: List[float],
        period: int = 14,
        timestamp: Optional[datetime] = None
    ) -> RSIReading:
        """
        Calculate Relative Strength Index (RSI).
        
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
        
        Args:
            prices: List of closing prices (newest last)
            period: RSI period (default 14)
            timestamp: Timestamp for reading
            
        Returns:
            RSIReading with value and signal interpretation
        """
        if len(prices) < period + 1:
            raise ValueError(f"Need at least {period + 1} prices for RSI calculation")
        
        # Calculate price changes
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [max(change, 0) for change in changes]
        losses = [abs(min(change, 0)) for change in changes]
        
        # Calculate initial averages
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        # Calculate RS and RSI
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # Determine signal
        if rsi >= self.RSI_EXTREME_OVERBOUGHT:
            signal = "EXTREME_OVERBOUGHT"
            strength = min((rsi - self.RSI_OVERBOUGHT) / (100 - self.RSI_OVERBOUGHT), 1.0)
        elif rsi >= self.RSI_OVERBOUGHT:
            signal = "OVERBOUGHT"
            strength = (rsi - self.RSI_OVERBOUGHT) / (self.RSI_EXTREME_OVERBOUGHT - self.RSI_OVERBOUGHT)
        elif rsi <= self.RSI_EXTREME_OVERSOLD:
            signal = "EXTREME_OVERSOLD"
            strength = min((self.RSI_OVERSOLD - rsi) / self.RSI_OVERSOLD, 1.0)
        elif rsi <= self.RSI_OVERSOLD:
            signal = "OVERSOLD"
            strength = (self.RSI_OVERSOLD - rsi) / (self.RSI_OVERSOLD - self.RSI_EXTREME_OVERSOLD)
        else:
            signal = "NEUTRAL"
            strength = 0.0
        
        return RSIReading(
            value=rsi,
            timestamp=timestamp or datetime.now(),
            period=period,
            signal=signal,
            strength=strength,
            avg_gain=avg_gain,
            avg_loss=avg_loss
        )
    
    def calculate_sma(
        self,
        prices: List[float],
        period: int,
        timestamp: Optional[datetime] = None
    ) -> MovingAverage:
        """
        Calculate Simple Moving Average (SMA).
        
        SMA = Sum of prices / Period
        
        Args:
            prices: List of closing prices (newest last)
            period: SMA period
            timestamp: Timestamp for reading
            
        Returns:
            MovingAverage reading
        """
        if len(prices) < period:
            raise ValueError(f"Need at least {period} prices for SMA calculation")
        
        sma = sum(prices[-period:]) / period
        
        # Calculate trend
        if len(prices) >= period + 5:
            old_sma = sum(prices[-(period+5):-5]) / period
            slope = (sma - old_sma) / old_sma
            
            if slope > 0.01:
                trend = "UPTREND"
            elif slope < -0.01:
                trend = "DOWNTREND"
            else:
                trend = "SIDEWAYS"
        else:
            trend = "INSUFFICIENT_DATA"
            slope = 0.0
        
        return MovingAverage(
            value=sma,
            timestamp=timestamp or datetime.now(),
            period=period,
            ma_type="SMA",
            trend=trend,
            slope=slope
        )
    
    def calculate_ema(
        self,
        prices: List[float],
        period: int,
        timestamp: Optional[datetime] = None
    ) -> MovingAverage:
        """
        Calculate Exponential Moving Average (EMA).
        
        EMA = Price * multiplier + EMA(previous) * (1 - multiplier)
        Multiplier = 2 / (period + 1)
        
        Args:
            prices: List of closing prices (newest last)
            period: EMA period
            timestamp: Timestamp for reading
            
        Returns:
            MovingAverage reading
        """
        if len(prices) < period:
            raise ValueError(f"Need at least {period} prices for EMA calculation")
        
        multiplier = 2 / (period + 1)
        
        # Start with SMA as initial EMA
        ema = sum(prices[:period]) / period
        
        # Calculate EMA for remaining prices
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        # Calculate trend
        if len(prices) >= period + 5:
            # Calculate old EMA
            old_ema = sum(prices[:period]) / period
            for price in prices[period:-5]:
                old_ema = (price * multiplier) + (old_ema * (1 - multiplier))
            
            slope = (ema - old_ema) / old_ema
            
            if slope > 0.01:
                trend = "UPTREND"
            elif slope < -0.01:
                trend = "DOWNTREND"
            else:
                trend = "SIDEWAYS"
        else:
            trend = "INSUFFICIENT_DATA"
            slope = 0.0
        
        return MovingAverage(
            value=ema,
            timestamp=timestamp or datetime.now(),
            period=period,
            ma_type="EMA",
            trend=trend,
            slope=slope
        )
    
    def calculate_macd(
        self,
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        timestamp: Optional[datetime] = None
    ) -> MACDReading:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        MACD Line = Fast EMA - Slow EMA
        Signal Line = EMA of MACD Line
        Histogram = MACD Line - Signal Line
        
        Args:
            prices: List of closing prices (newest last)
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line EMA period (default 9)
            timestamp: Timestamp for reading
            
        Returns:
            MACDReading with signals and interpretation
        """
        if len(prices) < slow_period + signal_period:
            raise ValueError(f"Need at least {slow_period + signal_period} prices for MACD")
        
        # Calculate EMAs
        fast_ema = self.calculate_ema(prices, fast_period).value
        slow_ema = self.calculate_ema(prices, slow_period).value
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Calculate MACD values for all points to get signal line
        macd_values = []
        for i in range(slow_period, len(prices) + 1):
            f_ema = self.calculate_ema(prices[:i], fast_period).value
            s_ema = self.calculate_ema(prices[:i], slow_period).value
            macd_values.append(f_ema - s_ema)
        
        # Calculate signal line (EMA of MACD)
        signal_line = self.calculate_ema(macd_values, signal_period).value
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        # Determine signal
        if len(macd_values) > signal_period:
            # Previous histogram for crossover detection
            prev_macd = macd_values[-2]
            prev_signal_ema = self.calculate_ema(macd_values[:-1], signal_period).value
            prev_histogram = prev_macd - prev_signal_ema
            
            # Detect crossovers
            if prev_histogram <= 0 and histogram > 0:
                signal = "BULLISH_CROSSOVER"
                strength = min(abs(histogram) / abs(prev_histogram), 1.0)
            elif prev_histogram >= 0 and histogram < 0:
                signal = "BEARISH_CROSSOVER"
                strength = min(abs(histogram) / abs(prev_histogram), 1.0)
            elif histogram > 0:
                signal = "BULLISH"
                strength = min(histogram / max(macd_values), 1.0) if max(macd_values) > 0 else 0.5
            elif histogram < 0:
                signal = "BEARISH"
                strength = min(abs(histogram) / abs(min(macd_values)), 1.0) if min(macd_values) < 0 else 0.5
            else:
                signal = "NEUTRAL"
                strength = 0.0
        else:
            signal = "INSUFFICIENT_DATA"
            strength = 0.0
        
        return MACDReading(
            macd_line=macd_line,
            signal_line=signal_line,
            histogram=histogram,
            timestamp=timestamp or datetime.now(),
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            signal=signal,
            strength=strength
        )
    
    def calculate_bollinger_bands(
        self,
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0,
        timestamp: Optional[datetime] = None
    ) -> BollingerBands:
        """
        Calculate Bollinger Bands.
        
        Middle Band = SMA
        Upper Band = SMA + (std_dev * standard deviation)
        Lower Band = SMA - (std_dev * standard deviation)
        
        Args:
            prices: List of closing prices (newest last)
            period: Period for SMA (default 20)
            std_dev: Standard deviations for bands (default 2.0)
            timestamp: Timestamp for reading
            
        Returns:
            BollingerBands reading with signals
        """
        if len(prices) < period:
            raise ValueError(f"Need at least {period} prices for Bollinger Bands")
        
        # Calculate middle band (SMA)
        middle_band = sum(prices[-period:]) / period
        
        # Calculate standard deviation
        variance = sum((p - middle_band) ** 2 for p in prices[-period:]) / period
        stdev = math.sqrt(variance)
        
        # Calculate bands
        upper_band = middle_band + (std_dev * stdev)
        lower_band = middle_band - (std_dev * stdev)
        
        # Calculate bandwidth
        bandwidth = (upper_band - lower_band) / middle_band
        
        # Calculate %B (where price is relative to bands)
        current_price = prices[-1]
        if upper_band != lower_band:
            percent_b = (current_price - lower_band) / (upper_band - lower_band)
        else:
            percent_b = 0.5
        
        # Determine signal
        if bandwidth < self.BB_SQUEEZE_THRESHOLD:
            signal = "SQUEEZE"
            volatility = "LOW"
        elif percent_b > self.BB_OVERBOUGHT:
            signal = "OVERBOUGHT"
            volatility = "NORMAL" if bandwidth < 0.2 else "HIGH"
        elif percent_b < self.BB_OVERSOLD:
            signal = "OVERSOLD"
            volatility = "NORMAL" if bandwidth < 0.2 else "HIGH"
        elif current_price > upper_band:
            signal = "BREAKOUT"
            volatility = "HIGH"
        elif current_price < lower_band:
            signal = "BREAKDOWN"
            volatility = "HIGH"
        else:
            signal = "NEUTRAL"
            volatility = "NORMAL" if bandwidth < 0.2 else "HIGH"
        
        return BollingerBands(
            upper_band=upper_band,
            middle_band=middle_band,
            lower_band=lower_band,
            bandwidth=bandwidth,
            percent_b=percent_b,
            timestamp=timestamp or datetime.now(),
            period=period,
            std_dev=std_dev,
            signal=signal,
            volatility=volatility
        )
    
    def generate_trading_signals(
        self,
        prices: List[float],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive trading signals from all indicators.
        
        Args:
            prices: List of closing prices (newest last)
            timestamp: Timestamp for reading
            
        Returns:
            Dictionary with all indicators and composite signal
        """
        if len(prices) < 50:
            return {
                "error": "Need at least 50 price points for reliable signals",
                "price_count": len(prices)
            }
        
        try:
            # Calculate all indicators
            rsi = self.calculate_rsi(prices, period=14, timestamp=timestamp)
            macd = self.calculate_macd(prices, timestamp=timestamp)
            bb = self.calculate_bollinger_bands(prices, timestamp=timestamp)
            sma_20 = self.calculate_sma(prices, period=20, timestamp=timestamp)
            sma_50 = self.calculate_sma(prices, period=50, timestamp=timestamp)
            ema_12 = self.calculate_ema(prices, period=12, timestamp=timestamp)
            
            # Calculate composite signal score (-1 to 1)
            signal_score = 0.0
            signal_count = 0
            signals = []
            
            # RSI signals
            if rsi.signal in ["OVERSOLD", "EXTREME_OVERSOLD"]:
                signal_score += rsi.strength
                signal_count += 1
                signals.append(f"RSI {rsi.signal} ({rsi.value:.1f})")
            elif rsi.signal in ["OVERBOUGHT", "EXTREME_OVERBOUGHT"]:
                signal_score -= rsi.strength
                signal_count += 1
                signals.append(f"RSI {rsi.signal} ({rsi.value:.1f})")
            
            # MACD signals
            if macd.signal == "BULLISH_CROSSOVER":
                signal_score += macd.strength
                signal_count += 1
                signals.append(f"MACD BULLISH CROSSOVER")
            elif macd.signal == "BEARISH_CROSSOVER":
                signal_score -= macd.strength
                signal_count += 1
                signals.append(f"MACD BEARISH CROSSOVER")
            elif macd.signal == "BULLISH":
                signal_score += 0.5 * macd.strength
                signal_count += 0.5
            elif macd.signal == "BEARISH":
                signal_score -= 0.5 * macd.strength
                signal_count -= 0.5
            
            # Bollinger Bands signals
            if bb.signal == "OVERSOLD":
                signal_score += 0.5
                signal_count += 1
                signals.append(f"BB OVERSOLD (%B: {bb.percent_b:.2f})")
            elif bb.signal == "OVERBOUGHT":
                signal_score -= 0.5
                signal_count += 1
                signals.append(f"BB OVERBOUGHT (%B: {bb.percent_b:.2f})")
            elif bb.signal == "SQUEEZE":
                signals.append(f"BB SQUEEZE (low volatility)")
            
            # Moving average trend
            current_price = prices[-1]
            if current_price > sma_50.value and sma_20.value > sma_50.value:
                signal_score += 0.3
                signals.append(f"GOLDEN CROSS (uptrend)")
            elif current_price < sma_50.value and sma_20.value < sma_50.value:
                signal_score -= 0.3
                signals.append(f"DEATH CROSS (downtrend)")
            
            # Normalize score
            if signal_count > 0:
                composite_score = signal_score / max(signal_count, 1)
            else:
                composite_score = 0.0
            
            # Determine composite signal
            if composite_score > 0.5:
                composite_signal = "STRONG_BUY"
            elif composite_score > 0.2:
                composite_signal = "BUY"
            elif composite_score < -0.5:
                composite_signal = "STRONG_SELL"
            elif composite_score < -0.2:
                composite_signal = "SELL"
            else:
                composite_signal = "HOLD"
            
            return {
                "timestamp": timestamp or datetime.now(),
                "current_price": current_price,
                "composite_signal": composite_signal,
                "composite_score": composite_score,
                "signals": signals,
                "indicators": {
                    "rsi": {
                        "value": rsi.value,
                        "signal": rsi.signal,
                        "strength": rsi.strength
                    },
                    "macd": {
                        "macd_line": macd.macd_line,
                        "signal_line": macd.signal_line,
                        "histogram": macd.histogram,
                        "signal": macd.signal,
                        "strength": macd.strength
                    },
                    "bollinger_bands": {
                        "upper": bb.upper_band,
                        "middle": bb.middle_band,
                        "lower": bb.lower_band,
                        "percent_b": bb.percent_b,
                        "signal": bb.signal,
                        "volatility": bb.volatility
                    },
                    "moving_averages": {
                        "sma_20": sma_20.value,
                        "sma_50": sma_50.value,
                        "ema_12": ema_12.value,
                        "sma_20_trend": sma_20.trend,
                        "sma_50_trend": sma_50.trend
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating trading signals: {e}")
            return {
                "error": str(e),
                "timestamp": timestamp or datetime.now()
            }
