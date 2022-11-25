from numpy import log, polyfit, sqrt, std, subtract

"""
// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © balipour

//@version=4
study("Hurst Exponent - Detrended Fluctuation Analysis", "BA🐷HE (DFA)", precision = 3, max_bars_back=5000)

//Input Strings
group1        = "Sample Settings"
group2        = "Log Scaling"
group3        = "Style"
L             = "Line"
CL            = "Columns"
Ci            = "Circles"
ON            = "On"
OFF           = "Off"
//Inputs{

useRange   = input("ALL",        "Date Range",                 input.string,  options = ["HOURS", "DAYS", "WEEKS", "ALL"],  inline = "Date",        group   = group1)
number     = input(300,          "Number",                     input.float,   minval  = 0,                                  group = group1,         inline  = "Date", tooltip = "Select Script Calculation Date to Reduce loading time when using high lookback")
len        = input(100,          "Sample Size",                input.integer, minval  = 40,                                 group   = group1,       tooltip = "lookback period for HE, Optimal Size > 50, Larger Size More Accurate and More lag")
showma     = input(false,        "Show Filter",                input.bool,    inline  = "Show MA")
slen       = input(18,           "Length",                     input.integer, minval  = 4,                                  inline  = "Show MA",    tooltip = "Smoothed Moving Averge of HE")
Bsc        = input(8,            "Base Scale",                 input.integer, options = [4, 8, 16],                         inline  = "Base Scale", group   = group2)
Msc        = input(2,            "Max Scale",                  input.integer, options = [2, 4],                             inline  = "Base Scale", group   = group2, tooltip = "Select larger Value(Max and Base scale) when Sample Size is larger")
stl        = input(Ci,           "Plot Style ",                input.string,  inline  = "Plot Style",                       options = [Ci, L, CL],  group   = group3)
lT         = input(1,            "Line Thickness",             input.integer, inline  = "Plot Style",                       options = [1,2,3],      group   = group3)
c_ma       = input(color.orange, "MA",                         input.color,   inline  = "MA",                               group   = group3)
lTma       = input(1,            "Line Thickness",             input.integer, inline  = "MA",                               options = [1,2,3],      group   = group3)
c_t        = input(color.aqua,   "> 0.5",                      input.color,   inline  = "> 0.5",                            group   = group3)
c_m        = input(#FF0080ff,    "< 0.5",                      input.color,   inline  = "> 0.5",                            group   = group3)
c_st       = input(color.lime,   "Significant Trend",          input.color,   inline  = "Significant Trend",                group   = group3)
c_sm       = input(color.yellow, "Significant Mean Reversion", input.color,   inline  = "Significant Trend",                group   = group3)
c_cv       = input(color.white,  "Confidence Interval",        input.color,   inline  = "Confidence Interval",              group   = group3)
c_mid      = input(color.white,  "Mid Line",                   input.color,   inline  = "Confidence Interval",              group   = group3)
dt         = input(ON,           "Show Table",                 input.string,  options = [ON, OFF],                          inline  = "table",      group   = group3) == ON
bg         = input(ON,           "Dark Background",            input.string,  options = [OFF,ON],                           group   = group3) == ON
tsize      = input("normal",     "Size",                       input.string,  options = ["tiny", "small", "normal", "large", "huge", "auto"],       inline = "table", group = group3)

//Background Color
bgcolor(bg ? color.new(#000000,20) : na, title = "Dark Background")

//Start Time Calculation (Credit to Allanster)
oneHour  = 60 * 60 * 1000
oneDay   = 24 * 60 * 60 * 1000
oneWeek  = 7 * oneDay
present  = timenow
start    = useRange == "HOURS" ? present - number * oneHour: 
          useRange == "DAYS" ? present - number * oneDay : 
          useRange == "WEEKS" ? present - number * oneWeek : na

//Condition to save Computing time
t = useRange == "ALL" ? true : time >= start


//Declaration
int   Min     = Bsc
int   Max     = Msc
var   fluc    = array.new_float(10)
var   scale   = array.new_float(10)
float slope   = na

//Functions
ss(Series, Period) => // Super Smoother Function
    var PI    = 2.0 * asin(1.0)
    var SQRT2 = sqrt(2.0)
    lambda = PI * SQRT2 / Period
    a1     = exp(-lambda)
    coeff2 = 2.0 * a1 * cos(lambda)
    coeff3 = - pow(a1, 2.0)
    coeff1 = 1.0 - coeff2 - coeff3
    filt1  = 0.0
    filt1 := coeff1 * (Series + nz(Series[1])) * 0.5 + coeff2 * nz(filt1[1]) + coeff3 * nz(filt1[2])
    filt1

//}

//Calculation{

//Log Return
r = log(close/close[1])
//Mean of Log Return
mean = sma(r,len)

//Cumulative Sum
var csum = array.new_float(len)
if t 
    sum = 0.0
    for i = 0 to len-1
        sum := (r[i] - mean) + sum
        array.set(csum,i,sum)

//Root Mean Sum (FLuctuation) function linear trend to calculate error between linear trend and cumulative sum
RMS(N1,N)=>
    if t
        //Slicing the array into different segments
        var seq = array.new_float(N)
        int count = 0
        for i = 0 to N-1
            count := count + 1
            array.set(seq,i,count)
        y = array.slice(csum,N1,N1+N)
        
        //Linear regression measuing trend (N/(N-1) for sample unbiased adjustedment)
        sdx = array.stdev(seq)       *sqrt(N/(N-1))
        sdy = array.stdev(y)         *sqrt(N/(N-1))
        cov = array.covariance(seq,y)*(N/(N-1))
        
        //Linear Regression Root Mean Square Error (Detrend)
        r2 = pow(cov/(sdx*sdy),2)
        rms = sqrt(1 - r2)*sdy

//Average of Root Mean Sum Measured each block (Log Scale)
Arms(bar)=>
    if t
        num = floor(len / bar)
        sumr = 0.0
        for i = 0 to num-1
            sumr := sumr + RMS(i*bar,bar)
        //Log Scale
        avg = log10(sumr/num)

//Approximating Log Scale Function (Saves Sample Size)
fs(x)=>
    if t
        round(Min*pow(pow(len/(Max*Min),0.1111111111),x))

if t
    //Set Ten points of Root Mean Square Average along the Y log axis
    array.set(fluc,0,Arms(fs(0)))
    array.set(fluc,1,Arms(fs(1)))
    array.set(fluc,2,Arms(fs(2)))
    array.set(fluc,3,Arms(fs(3)))
    array.set(fluc,4,Arms(fs(4)))
    array.set(fluc,5,Arms(fs(5)))
    array.set(fluc,6,Arms(fs(6)))
    array.set(fluc,7,Arms(fs(7)))
    array.set(fluc,8,Arms(fs(8)))
    array.set(fluc,9,Arms(fs(9)))
    
    //Set Ten Points of data scale along the X log axis
    for i = 0 to 9
        array.set(scale,i,log10(fs(i)))

    //SLope Measured From RMS and Scale on Log log plot using linear regression
    slope := array.covariance(scale,fluc) / array.variance(scale)

//Moving Average Smoothed Hurst Exponent 
smooth = showma ? ss(slope,slen)  : na

//Critical Value based on Confidence Interval (95% Confidence)
ci = 1.645 * (0.3912 / pow(len,0.3))
//Expected Value plus Crtical Value
cu = 0.5 + ci 
cd = 0.5 - ci

//}

//Plots{

//plotstyle
pstyle  = stl == L ? plot.style_linebr : 
         stl == CL ? plot.style_columns :
         stl == Ci ? plot.style_circles :
         plot.style_line

//Color of HE
c  = slope > cu ? c_st : slope >= 0.5 ? c_t : slope < cd ? c_sm  : slope < 0.5 ?  c_m : na
//Text of Table
text = slope > cu ? "Significant Trend" : slope >= 0.5 ? "Trend" : slope < cd ? "Significant Mean Reversion" : slope < 0.5 ? "Mean Reversion" : na

//Plotting
plot(slope, "Hurst Exponent", color=c, style = pstyle, linewidth = lT)

plot(cu, "Confidence Interval", color = c_cv, trackprice = true, show_last = 1)
plot(cd, "Confidence Interval", color = c_cv, trackprice = true, show_last = 1)

plot(smooth, "MA", color=c_ma, linewidth = lTma)

//0.5 Mid Level
line mid = na
if barstate.islast
    mid := line.new(bar_index-1, 0.5, bar_index, 0.5, xloc.bar_index, extend.left, color=c_mid, style = line.style_dashed )
    line.delete(mid[1])

//Table
var table htable = table.new(position.middle_right,2 , 2, bgcolor = color.new(color.black,100), frame_color = #000000, frame_width = 2, border_color = color.new(color.black,100), border_width = 3)
if barstate.islast and dt
    table.cell(htable, column = 0, row = 0, text = "Hurst Exponent:",        text_color = color.white, bgcolor = color.new(color.gray,50), text_size = tsize)
    table.cell(htable, column = 1, row = 0, text = tostring(round(slope,3)), text_color = c,           bgcolor = color.new(c,85),          text_size = tsize)
    table.cell(htable, column = 0, row = 1, text = "State:",                 text_color = color.white, bgcolor = color.new(color.gray,50), text_size = tsize)
    table.cell(htable, column = 1, row = 1, text = text,                     text_color = c,           bgcolor = color.new(c,85),          text_size = tsize)
//}


"""

"""
If the Hurst exponent is above 0.5, the market shows a trending
If the Hurst Exponent is below 0.5, the market shows a reverting
"""


def hurst(ts):
    """Returns the Hurst Exponent of the time series vector ts"""  # Create the range of lag values
    lags = range(2, 100)
    # Calculate the array of the variances of the lagged differences
    tau = [sqrt(std(subtract(ts[lag:], ts[:-lag]))) for lag in lags]  # Use a linear fit to estimate the Hurst Exponent
    poly = polyfit(log(lags), log(tau), 1)
    # Return the Hurst exponent from the polyfit output
    return poly[0] * 2.0


def get_hurst_exponent(time_series, max_lag=55):
    """Returns the Hurst Exponent of the time series"""
    lags = range(2, max_lag)
    # variances of the lagged differences
    tau = [std(subtract(time_series[lag:], time_series[:-lag])) for lag in lags]
    # calculate the slope of the log plot -> the Hurst Exponent
    reg = polyfit(log(lags), log(tau), 1)
    return reg[0] * 2
