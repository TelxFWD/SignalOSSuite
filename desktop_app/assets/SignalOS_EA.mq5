//+------------------------------------------------------------------+
//|                                                   SignalOS_EA.mq5 |
//|                        Copyright 2024, SignalOS Trading Platform |
//|                                          https://www.signalos.io |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, SignalOS Trading Platform"
#property link      "https://www.signalos.io"
#property version   "1.00"
#property description "SignalOS Expert Advisor for automated signal execution"

//--- Input parameters
input int      MagicNumber = 123456;        // Magic number for trades
input double   LotSize = 0.01;              // Default lot size
input int      Slippage = 3;                // Slippage in pips
input bool     EnableTrading = true;        // Enable/disable trading
input string   SignalFile = "signal.json";  // Signal file name
input int      CheckInterval = 1000;        // Check interval in milliseconds

//--- Global variables
datetime lastSignalTime = 0;
bool isProcessingSignal = false;
string signalFilePath;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("SignalOS EA initialized - Version 1.00");
    
    // Construct signal file path
    signalFilePath = TerminalInfoString(TERMINAL_COMMONDATA_PATH) + "\\Files\\" + SignalFile;
    
    // Create heartbeat file
    CreateHeartbeat();
    
    // Set timer for signal checking
    EventSetTimer(CheckInterval / 1000);
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                               |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("SignalOS EA deinitialized. Reason: ", reason);
    EventKillTimer();
}

//+------------------------------------------------------------------+
//| Expert tick function                                            |
//+------------------------------------------------------------------+
void OnTick()
{
    // Update heartbeat
    UpdateHeartbeat();
}

//+------------------------------------------------------------------+
//| Timer function                                                  |
//+------------------------------------------------------------------+
void OnTimer()
{
    if (!EnableTrading || isProcessingSignal)
        return;
        
    CheckForNewSignal();
}

//+------------------------------------------------------------------+
//| Check for new signal from SignalOS                             |
//+------------------------------------------------------------------+
void CheckForNewSignal()
{
    if (!FileIsExist(signalFilePath))
        return;
        
    // Read signal file
    int handle = FileOpen(SignalFile, FILE_READ | FILE_TXT | FILE_COMMON);
    if (handle == INVALID_HANDLE)
    {
        Print("Error opening signal file: ", GetLastError());
        return;
    }
    
    string signalData = "";
    while (!FileIsEnding(handle))
    {
        signalData += FileReadString(handle);
    }
    FileClose(handle);
    
    if (StringLen(signalData) == 0)
        return;
        
    // Parse and execute signal
    if (ParseAndExecuteSignal(signalData))
    {
        // Archive the signal file after successful processing
        ArchiveSignalFile();
    }
}

//+------------------------------------------------------------------+
//| Parse and execute signal                                        |
//+------------------------------------------------------------------+
bool ParseAndExecuteSignal(string jsonData)
{
    isProcessingSignal = true;
    
    // Simple JSON parsing for signal data
    string symbol = ExtractJsonValue(jsonData, "pair");
    string action = ExtractJsonValue(jsonData, "action");
    double entryPrice = StringToDouble(ExtractJsonValue(jsonData, "entry_price"));
    double stopLoss = StringToDouble(ExtractJsonValue(jsonData, "stop_loss"));
    double takeProfit = StringToDouble(ExtractJsonValue(jsonData, "take_profit"));
    double lotSize = StringToDouble(ExtractJsonValue(jsonData, "lot_size"));
    string signalId = ExtractJsonValue(jsonData, "signal_id");
    string comment = ExtractJsonValue(jsonData, "comment");
    
    // Validate signal data
    if (symbol == "" || action == "" || lotSize <= 0)
    {
        Print("Invalid signal data received");
        isProcessingSignal = false;
        return false;
    }
    
    // Normalize symbol name
    if (symbol == "GOLD" || symbol == "XAU") symbol = "XAUUSD";
    if (symbol == "SILVER" || symbol == "XAG") symbol = "XAGUSD";
    
    // Check if symbol exists
    if (SymbolSelect(symbol, true) == false)
    {
        Print("Symbol not found: ", symbol);
        isProcessingSignal = false;
        return false;
    }
    
    // Use default lot size if not specified
    if (lotSize <= 0) lotSize = LotSize;
    
    // Determine order type
    ENUM_ORDER_TYPE orderType;
    if (action == "BUY")
        orderType = ORDER_TYPE_BUY;
    else if (action == "SELL")
        orderType = ORDER_TYPE_SELL;
    else
    {
        Print("Invalid action: ", action);
        isProcessingSignal = false;
        return false;
    }
    
    // Execute the trade
    bool result = ExecuteTrade(symbol, orderType, lotSize, entryPrice, stopLoss, takeProfit, comment, signalId);
    
    isProcessingSignal = false;
    return result;
}

//+------------------------------------------------------------------+
//| Execute trade                                                   |
//+------------------------------------------------------------------+
bool ExecuteTrade(string symbol, ENUM_ORDER_TYPE orderType, double lot, double price, 
                  double sl, double tp, string comment, string signalId)
{
    MqlTradeRequest request;
    MqlTradeResult result;
    
    ZeroMemory(request);
    ZeroMemory(result);
    
    // Get current prices
    MqlTick tick;
    if (!SymbolInfoTick(symbol, tick))
    {
        Print("Failed to get tick for ", symbol);
        return false;
    }
    
    // Set trade request parameters
    request.action = TRADE_ACTION_DEAL;
    request.symbol = symbol;
    request.volume = lot;
    request.type = orderType;
    request.deviation = Slippage;
    request.magic = MagicNumber;
    request.comment = comment + "_" + signalId;
    
    // Set price based on order type
    if (orderType == ORDER_TYPE_BUY)
    {
        request.price = tick.ask;
        if (price > 0 && MathAbs(tick.ask - price) / Point > Slippage)
        {
            Print("Price deviation too large for BUY order");
            return false;
        }
    }
    else
    {
        request.price = tick.bid;
        if (price > 0 && MathAbs(tick.bid - price) / Point > Slippage)
        {
            Print("Price deviation too large for SELL order");
            return false;
        }
    }
    
    // Set stop loss and take profit
    if (sl > 0) request.sl = sl;
    if (tp > 0) request.tp = tp;
    
    // Send order
    if (!OrderSend(request, result))
    {
        Print("OrderSend failed for ", symbol, ". Error: ", GetLastError());
        LogTradeResult(false, symbol, orderType, lot, request.price, sl, tp, signalId, result.comment);
        return false;
    }
    
    if (result.retcode == TRADE_RETCODE_DONE)
    {
        Print("Trade executed successfully. Ticket: ", result.order, " Symbol: ", symbol, 
              " Type: ", EnumToString(orderType), " Volume: ", lot, " Price: ", result.price);
        LogTradeResult(true, symbol, orderType, lot, result.price, sl, tp, signalId, "Success");
        return true;
    }
    else
    {
        Print("Trade execution failed. Return code: ", result.retcode, " Comment: ", result.comment);
        LogTradeResult(false, symbol, orderType, lot, request.price, sl, tp, signalId, result.comment);
        return false;
    }
}

//+------------------------------------------------------------------+
//| Extract value from JSON string                                 |
//+------------------------------------------------------------------+
string ExtractJsonValue(string json, string key)
{
    string searchKey = "\"" + key + "\"";
    int startPos = StringFind(json, searchKey);
    if (startPos == -1) return "";
    
    startPos = StringFind(json, ":", startPos);
    if (startPos == -1) return "";
    
    startPos++;
    while (startPos < StringLen(json) && (StringGetCharacter(json, startPos) == ' ' || 
           StringGetCharacter(json, startPos) == '\t' || StringGetCharacter(json, startPos) == '"'))
        startPos++;
    
    int endPos = startPos;
    bool inQuotes = StringGetCharacter(json, startPos - 1) == '"';
    
    if (inQuotes)
    {
        while (endPos < StringLen(json) && StringGetCharacter(json, endPos) != '"')
            endPos++;
    }
    else
    {
        while (endPos < StringLen(json) && StringGetCharacter(json, endPos) != ',' && 
               StringGetCharacter(json, endPos) != '}' && StringGetCharacter(json, endPos) != '\n')
            endPos++;
    }
    
    return StringSubstr(json, startPos, endPos - startPos);
}

//+------------------------------------------------------------------+
//| Create heartbeat file                                          |
//+------------------------------------------------------------------+
void CreateHeartbeat()
{
    string heartbeatFile = "signalos_heartbeat.txt";
    int handle = FileOpen(heartbeatFile, FILE_WRITE | FILE_TXT | FILE_COMMON);
    if (handle != INVALID_HANDLE)
    {
        FileWrite(handle, "SignalOS EA Active - " + TimeToString(TimeCurrent()));
        FileClose(handle);
    }
}

//+------------------------------------------------------------------+
//| Update heartbeat                                               |
//+------------------------------------------------------------------+
void UpdateHeartbeat()
{
    static datetime lastHeartbeat = 0;
    if (TimeCurrent() - lastHeartbeat < 30) // Update every 30 seconds
        return;
        
    lastHeartbeat = TimeCurrent();
    
    string heartbeatFile = "signalos_heartbeat.txt";
    int handle = FileOpen(heartbeatFile, FILE_WRITE | FILE_TXT | FILE_COMMON);
    if (handle != INVALID_HANDLE)
    {
        FileWrite(handle, "SignalOS EA Active - " + TimeToString(TimeCurrent()));
        FileWrite(handle, "Magic Number: " + IntegerToString(MagicNumber));
        FileWrite(handle, "Trading Enabled: " + (EnableTrading ? "Yes" : "No"));
        FileWrite(handle, "Processing Signal: " + (isProcessingSignal ? "Yes" : "No"));
        FileClose(handle);
    }
}

//+------------------------------------------------------------------+
//| Archive signal file after processing                           |
//+------------------------------------------------------------------+
void ArchiveSignalFile()
{
    string archiveFile = "processed_signals\\" + TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS) + "_signal.json";
    
    // Copy signal file to archive
    if (FileIsExist(SignalFile))
    {
        int sourceHandle = FileOpen(SignalFile, FILE_READ | FILE_TXT | FILE_COMMON);
        if (sourceHandle != INVALID_HANDLE)
        {
            string content = "";
            while (!FileIsEnding(sourceHandle))
            {
                content += FileReadString(sourceHandle) + "\n";
            }
            FileClose(sourceHandle);
            
            int archiveHandle = FileOpen(archiveFile, FILE_WRITE | FILE_TXT | FILE_COMMON);
            if (archiveHandle != INVALID_HANDLE)
            {
                FileWriteString(archiveHandle, content);
                FileClose(archiveHandle);
            }
        }
        
        // Delete original signal file
        FileDelete(SignalFile);
    }
}

//+------------------------------------------------------------------+
//| Log trade result                                               |
//+------------------------------------------------------------------+
void LogTradeResult(bool success, string symbol, ENUM_ORDER_TYPE type, double volume, 
                    double price, double sl, double tp, string signalId, string comment)
{
    string logFile = "signalos_trades.log";
    int handle = FileOpen(logFile, FILE_WRITE | FILE_TXT | FILE_COMMON);
    if (handle != INVALID_HANDLE)
    {
        string logEntry = TimeToString(TimeCurrent()) + " | " +
                         (success ? "SUCCESS" : "FAILED") + " | " +
                         symbol + " | " +
                         EnumToString(type) + " | " +
                         DoubleToString(volume, 2) + " | " +
                         DoubleToString(price, 5) + " | " +
                         "SL:" + DoubleToString(sl, 5) + " | " +
                         "TP:" + DoubleToString(tp, 5) + " | " +
                         "ID:" + signalId + " | " +
                         comment;
        
        FileSeek(handle, 0, SEEK_END);
        FileWrite(handle, logEntry);
        FileClose(handle);
    }
}