def senkou_span_a_b(high, low):
    high_9 = high.rolling(9).max()
    low_9 = low.rolling(9).min()
    tenkan_sen_line = (high_9 + low_9) / 2
    # Calculate Kijun-sen
    high_26 = high.rolling(26).max()
    low_26 = low.rolling(26).min()
    kijun_sen_line = (high_26 + low_26) / 2
    # Calculate Senkou Span A
    senkou_span_A = ((tenkan_sen_line + kijun_sen_line) / 2).shift(26)
    # Calculate Senkou Span B
    high_52 = high.rolling(52).max()
    low_52 = high.rolling(52).min()
    senkou_span_B = ((high_52 + low_52) / 2).shift(26)
    return senkou_span_A, senkou_span_B
