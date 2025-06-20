//+------------------------------------------------------------------+
//|                                                    SignalOS_EA.mq5 |
//|                                  Copyright 2025, SignalOS Team |
//|                                    https://www.signalos.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, SignalOS Team"
#property link      "https://www.signalos.com"
#property version   "1.00"
#property description "SignalOS Expert Advisor - Automated Signal Execution"

//--- Input parameters
input string SignalPath = "Files/SignalOS/";           // Signal file path
input bool   AutoTrade = true;                         // Enable auto trading
input double DefaultLotSize = 0.01;                    // Default lot size
input int    MagicNumber = 12345;                      // Magic number
input int    Slippage = 3;                             // Maximum slippage
input bool   EnableLogging = true;                     // Enable detailed logging

//--- Global variables
string signal_file = "signal.json";
string status_file = "ea_status.json";
string heartbeat_file = "heartbeat.json";
datetime last_signal_check;
datetime last_heartbeat;
int file_check_interval = 1; // seconds

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Check if auto trading is enabled
    if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
    {
        Alert("Auto trading is disabled in terminal settings!");
        return INIT_FAILED;
    }
    
    if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
    {
        Alert("Auto trading is disabled for this EA!");
        return INIT_FAILED;
    }
    
    // Initialize variables
    last_signal_check = TimeCurrent();
    last_heartbeat = TimeCurrent();
    
    // Create status file
    WriteStatusFile("initialized", "EA successfully initialized");
    
    if(EnableLogging)
        Print("SignalOS EA initialized successfully");
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    WriteStatusFile("stopped", "EA stopped, reason: " + IntegerToString(reason));
    
    if(EnableLogging)
        Print("SignalOS EA stopped, reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check for new signals every second
    if(TimeCurrent() - last_signal_check >= file_check_interval)
    {
        CheckForSignals();
        last_signal_check = TimeCurrent();
    }
    
    // Update heartbeat every 5 seconds
    if(TimeCurrent() - last_heartbeat >= 5)
    {
        WriteHeartbeat();
        last_heartbeat = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Check for new signal files                                       |
//+------------------------------------------------------------------+
void CheckForSignals()
{
    string filepath = SignalPath + signal_file;
    
    if(FileIsExist(filepath))
    {
        if(EnableLogging)
            Print("Signal file found: ", filepath);
        
        ProcessSignalFile(filepath);
    }
}

//+------------------------------------------------------------------+
//| Process signal file                                             |
//+------------------------------------------------------------------+
void ProcessSignalFile(string filepath)
{
    int file_handle = FileOpen(filepath, FILE_READ|FILE_TXT);
    
    if(file_handle == INVALID_HANDLE)
    {
        if(EnableLogging)
            Print("Error opening signal file: ", GetLastError());
        return;
    }
    
    string json_content = "";
    while(!FileIsEnding(file_handle))
    {
        json_content += FileReadString(file_handle);
    }
    FileClose(file_handle);
    
    if(EnableLogging)
        Print("Signal file content: ", json_content);
    
    // Parse JSON and execute signal
    if(ParseAndExecuteSignal(json_content))
    {
        // Move processed file to archive
        string archive_path = SignalPath + "processed_" + TimeToString(TimeCurrent()) + "_signal.json";
        if(!FileMove(filepath, 0, archive_path, 0))
        {
            FileDelete(filepath); // Delete if move fails
        }
        
        if(EnableLogging)
            Print("Signal processed and archived");
    }
    else
    {
        if(EnableLogging)
            Print("Failed to process signal");
    }
}

//+------------------------------------------------------------------+
//| Parse JSON and execute signal                                   |
//+------------------------------------------------------------------+
bool ParseAndExecuteSignal(string json_content)
{
    // Simple JSON parsing for signal execution
    string pair = ExtractJsonValue(json_content, "pair");
    string action = ExtractJsonValue(json_content, "action");
    double entry_price = StringToDouble(ExtractJsonValue(json_content, "entry_price"));
    double stop_loss = StringToDouble(ExtractJsonValue(json_content, "stop_loss"));
    double take_profit = StringToDouble(ExtractJsonValue(json_content, "take_profit"));
    double lot_size = StringToDouble(ExtractJsonValue(json_content, "lot_size"));
    string comment = ExtractJsonValue(json_content, "comment");
    
    if(pair == "" || action == "")
    {
        WriteStatusFile("error", "Invalid signal format");
        return false;
    }
    
    // Default lot size if not specified
    if(lot_size <= 0)
        lot_size = DefaultLotSize;
    
    // Execute the trade
    ENUM_ORDER_TYPE order_type;
    if(StringFind(action, "BUY") >= 0)
        order_type = ORDER_TYPE_BUY;
    else if(StringFind(action, "SELL") >= 0)
        order_type = ORDER_TYPE_SELL;
    else
    {
        WriteStatusFile("error", "Unknown action: " + action);
        return false;
    }
    
    // Place the order
    MqlTradeRequest request;
    MqlTradeResult result;
    
    ZeroMemory(request);
    request.action = TRADE_ACTION_DEAL;
    request.symbol = pair;
    request.volume = lot_size;
    request.type = order_type;
    request.price = (entry_price > 0) ? entry_price : SymbolInfoDouble(pair, SYMBOL_ASK);
    request.sl = stop_loss;
    request.tp = take_profit;
    request.deviation = Slippage;
    request.magic = MagicNumber;
    request.comment = comment;
    
    if(!OrderSend(request, result))
    {
        WriteStatusFile("error", "Order failed: " + IntegerToString(GetLastError()));
        return false;
    }
    
    WriteStatusFile("executed", "Signal executed successfully, ticket: " + IntegerToString(result.order));
    
    if(EnableLogging)
        Print("Signal executed: ", pair, " ", action, " ", lot_size, " lots, ticket: ", result.order);
    
    return true;
}

//+------------------------------------------------------------------+
//| Extract value from simple JSON                                  |
//+------------------------------------------------------------------+
string ExtractJsonValue(string json, string key)
{
    string search_pattern = "\"" + key + "\"";
    int start_pos = StringFind(json, search_pattern);
    
    if(start_pos < 0)
        return "";
    
    start_pos = StringFind(json, ":", start_pos);
    if(start_pos < 0)
        return "";
    
    start_pos++;
    
    // Skip whitespace
    while(start_pos < StringLen(json) && (StringGetCharacter(json, start_pos) == ' ' || StringGetCharacter(json, start_pos) == '\t'))
        start_pos++;
    
    // Handle quoted strings
    if(StringGetCharacter(json, start_pos) == '"')
    {
        start_pos++;
        int end_pos = StringFind(json, "\"", start_pos);
        if(end_pos > start_pos)
            return StringSubstr(json, start_pos, end_pos - start_pos);
    }
    else
    {
        // Handle numbers/booleans
        int end_pos = start_pos;
        while(end_pos < StringLen(json))
        {
            ushort char_code = StringGetCharacter(json, end_pos);
            if(char_code == ',' || char_code == '}' || char_code == '\n' || char_code == '\r')
                break;
            end_pos++;
        }
        
        string value = StringSubstr(json, start_pos, end_pos - start_pos);
        StringTrimLeft(value);
        StringTrimRight(value);
        return value;
    }
    
    return "";
}

//+------------------------------------------------------------------+
//| Write status file                                               |
//+------------------------------------------------------------------+
void WriteStatusFile(string status, string message)
{
    string filepath = SignalPath + status_file;
    int file_handle = FileOpen(filepath, FILE_WRITE|FILE_TXT);
    
    if(file_handle != INVALID_HANDLE)
    {
        string json_status = StringFormat("{\n  \"status\": \"%s\",\n  \"message\": \"%s\",\n  \"timestamp\": \"%s\",\n  \"terminal\": \"%s\",\n  \"account\": %d\n}",
                                         status, message, TimeToString(TimeCurrent()), TerminalInfoString(TERMINAL_NAME), AccountInfoInteger(ACCOUNT_LOGIN));
        
        FileWriteString(file_handle, json_status);
        FileClose(file_handle);
    }
}

//+------------------------------------------------------------------+
//| Write heartbeat file                                            |
//+------------------------------------------------------------------+
void WriteHeartbeat()
{
    string filepath = SignalPath + heartbeat_file;
    int file_handle = FileOpen(filepath, FILE_WRITE|FILE_TXT);
    
    if(file_handle != INVALID_HANDLE)
    {
        string json_heartbeat = StringFormat("{\n  \"timestamp\": \"%s\",\n  \"terminal_connected\": %s,\n  \"auto_trade_enabled\": %s,\n  \"account\": %d,\n  \"balance\": %.2f,\n  \"equity\": %.2f\n}",
                                            TimeToString(TimeCurrent()),
                                            TerminalInfoInteger(TERMINAL_CONNECTED) ? "true" : "false",
                                            TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) ? "true" : "false",
                                            AccountInfoInteger(ACCOUNT_LOGIN),
                                            AccountInfoDouble(ACCOUNT_BALANCE),
                                            AccountInfoDouble(ACCOUNT_EQUITY));
        
        FileWriteString(file_handle, json_heartbeat);
        FileClose(file_handle);
    }
}