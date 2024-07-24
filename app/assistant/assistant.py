import openai
import os
from dotenv import load_dotenv
import json
import time
import logging
from datetime import datetime

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
    
class StockAnalysisAssistant:
    def __init__(self, stock_data_manager, assistant_id=None):
        self.stock_data_manager = stock_data_manager
        if assistant_id:
            self.assistant = self.get_assistant(assistant_id)
        else:
            self.assistant = self.create_assistant()

    def get_assistant(self, assistant_id):
        try:
            return openai.beta.assistants.retrieve(assistant_id)
        except Exception as e:
            logging.error(f"Error retrieving assistant: {str(e)}")
            raise

    def create_assistant(self):
        try:
            assistant = openai.beta.assistants.create(
                name="Stock Analysis Assistant",
                instructions="""
                You are a stock analysis assistant. Your role is to analyze stock data and provide insightful reports.
                You have access to various financial data and metrics for stocks. When asked about a specific stock,
                you should retrieve the necessary data, process it, and provide a comprehensive analysis.
                Your analysis should include:
                1. Basic stock information (price, volume, market cap)
                2. Fundamental Analysis
                3. Technical indicators (moving averages, RSI, MACD)
                4. Financial ratios and metrics
                5. Potential risks and opportunities
                6. A summary and recommendation (buy, sell or hold). Include a recommended entry price.
                
                Use the provided tools to fetch and analyze data. Always provide clear explanations and justify your analysis.
                """,
                model="gpt-4o-mini",
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "get_stock_data",
                        "description": "Retrieve various types of stock data",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "The stock symbol to retrieve data for"
                                },
                                "data_type": {
                                    "type": "string",
                                    "enum": ["summary", "income_statement", "balance_sheet", "cash_flow_statement", "financial_metrics"],
                                    "description": "The type of data to retrieve"
                                }
                            },
                            "required": ["symbol", "data_type"]
                        }
                    }
                }]
            )
            return assistant.id
        except Exception as e:
            logging.error(f"Error creating assistant: {str(e)}")
            raise

    def get_stock_data(self, symbol, data_type="summary"):
        try:
            if data_type == "summary":
                data = self.stock_data_manager.get_stock_summary(symbol)
            elif data_type in ["income_statement", "balance_sheet", "cash_flow_statement"]:
                data = self.stock_data_manager.get_financial_statement(symbol, data_type)
            elif data_type == "financial_metrics":
                data = self.stock_data_manager.get_financial_metrics(symbol)
            else:
                return {"error": f"Invalid data type: {data_type}"}
            
            # Use the custom JSON encoder to handle datetime objects
            return json.loads(json.dumps(data, cls=CustomJSONEncoder))
        except Exception as e:
            logging.error(f"Error getting stock data: {str(e)}")
            return {"error": f"Failed to retrieve {data_type} for {symbol}: {str(e)}"}

    def create_thread(self):
        try:
            thread = openai.beta.threads.create()
            return thread
        except Exception as e:
            logging.error(f"Error creating thread: {str(e)}")
            raise

    def add_message_to_thread(self, thread_id, content):
        try:
            message = openai.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=content
            )
            return message
        except Exception as e:
            logging.error(f"Error adding message to thread: {str(e)}")
            raise

    def run_assistant(self, thread_id, instructions=None):
        try:
            run = openai.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant.id,
                instructions=instructions
            )
            return run
        except Exception as e:
            logging.error(f"Error running assistant: {str(e)}")
            raise

    def process_tool_calls(self, thread_id, run_id, tool_calls):
        try:
            tool_outputs = []
            for tool_call in tool_calls:
                if tool_call.function.name == "get_stock_data":
                    args = json.loads(tool_call.function.arguments)
                    symbol = args.get("symbol")
                    data_type = args.get("data_type", "summary")  # Default to summary if not provided
                    
                    if not symbol:
                        raise ValueError("Symbol is required for get_stock_data function")
                    
                    data = self.get_stock_data(symbol, data_type)
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(data, cls=CustomJSONEncoder)
                    })
            
            openai.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs
            )
        except Exception as e:
            logging.error(f"Error processing tool calls: {str(e)}")
            raise

    def get_run_status(self, thread_id, run_id):
        try:
            run = openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            return run.status
        except Exception as e:
            logging.error(f"Error getting run status: {str(e)}")
            raise

    def get_messages(self, thread_id):
        try:
            messages = openai.beta.threads.messages.list(thread_id=thread_id)
            return messages
        except Exception as e:
            logging.error(f"Error getting messages: {str(e)}")
            raise

    def analyze_stock(self, symbol):
        try:
            thread = self.create_thread()
            self.add_message_to_thread(thread.id, f"Analyze the stock {symbol}")
            run = self.run_assistant(thread.id)
            
            while True:
                time.sleep(1)  # Wait for 1 second before checking status
                status = self.get_run_status(thread.id, run.id)
                if status == 'completed':
                    break
                elif status == 'requires_action':
                    run_details = openai.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                    try:
                        self.process_tool_calls(
                            thread.id,
                            run.id,
                            run_details.required_action.submit_tool_outputs.tool_calls
                        )
                    except Exception as e:
                        logging.error(f"Error in process_tool_calls: {str(e)}")
                        raise
                elif status in ['failed', 'cancelled', 'expired']:
                    error_message = f"Run ended with status: {status}"
                    if hasattr(run, 'last_error'):
                        error_message += f". Error: {run.last_error}"
                    raise Exception(error_message)
            
            messages = self.get_messages(thread.id)
            for message in reversed(messages.data):
                if message.role == 'assistant':
                    return message.content[0].text.value

            return "No analysis generated."
        except Exception as e:
            logging.error(f"Error analyzing stock {symbol}: {str(e)}", exc_info=True)
            return f"An error occurred while analyzing the stock: {str(e)}"

# Usage example
# assistant = StockAnalysisAssistant(StockDataManager())
# analysis = assistant.analyze_stock("AAPL")
# print(analysis)