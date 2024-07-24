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
                Be conversational and engaging in your responses. Remember the context of the ongoing conversation.
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
            return assistant
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
                data = self.stock_data_manager.get_key_metrics(symbol)
            else:
                return {"error": f"Invalid data type: {data_type}"}
            
            return json.loads(json.dumps(data, cls=CustomJSONEncoder))
        except Exception as e:
            logging.error(f"Error getting stock data: {str(e)}")
            return {"error": f"Failed to retrieve {data_type} for {symbol}: {str(e)}"}

    def process_stock_conversation(self, stock_symbol, message, conversation_history):
        try:
            thread = openai.beta.threads.create()
            
            # Add conversation history to the thread
            for msg in conversation_history:
                openai.beta.threads.messages.create(
                    thread_id=thread.id,
                    role=msg['role'],
                    content=msg['content']
                )
            
            # Add the new user message
            openai.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Regarding {stock_symbol}: {message}"
            )
            
            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant.id,
                instructions=f"You are analyzing the stock {stock_symbol}. Provide relevant and detailed information based on the user's query. Use the get_stock_data function to retrieve necessary information."
            )
            
            while True:
                time.sleep(1)
                run_status = openai.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                logging.debug(f"Run status: {run_status.status}")
                
                if run_status.status == 'completed':
                    break
                elif run_status.status == 'requires_action':
                    tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []
                    for tool_call in tool_calls:
                        if tool_call.function.name == "get_stock_data":
                            arguments = json.loads(tool_call.function.arguments)
                            data_type = arguments.get('data_type', 'summary')
                            output = self.get_stock_data(stock_symbol, data_type)
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": json.dumps(output)
                            })
                    openai.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                elif run_status.status in ['failed', 'cancelled', 'expired']:
                    raise Exception(f"Run ended with status: {run_status.status}")
            
            messages = openai.beta.threads.messages.list(thread_id=thread.id)
            for message in reversed(messages.data):
                if message.role == 'assistant':
                    content = message.content[0].text.value if isinstance(message.content, list) else message.content
                    return content

            raise Exception("No assistant message found")
        except Exception as e:
            logging.error(f"Error in process_stock_conversation: {str(e)}", exc_info=True)
            return f"I apologize, but I encountered an error while processing your request. Error details: {str(e)}"