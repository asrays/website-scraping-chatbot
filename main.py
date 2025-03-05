import os
from typing import List, Dict
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
import requests
from bs4 import BeautifulSoup
from tools import get_availability, get_delivery_time, get_price, get_rating, get_review_count, get_title, get_size, get_return_policy
from serpapi import GoogleSearch
from typing import List, Dict, Union
import re

# Add your anthropic key here
os.environ["ANTHROPIC_API_KEY"] = ""

@tool
def calculate_discount(price: Union[str, float], discount_code: str) -> Dict:
    """Calculate the discounted price given the original price and a discount code."""
    try:
        # Convert price to float if it's a string
        price = float(price.replace("₹", "").replace(",", "").strip()) if isinstance(price, str) else float(price)

        # Extract discount percentage from the code
        discount_percent = discount_code.upper()

        if discount_percent is None:
            # Try to extract numbers from the discount code (e.g., "SAVE10" → 10)
            match = re.search(r'\d+', discount_code)
            if match:
                discount_percent = int(match.group(0))  # Extract numeric part
            else:
                return {"error": "Invalid discount code"}

        # Calculate the discount
        discount_amount = (discount_percent / 100) * price
        final_price = price - discount_amount

        return {
            "original_price": price,
            "discount_code": discount_code.upper(),
            "discount_percent": discount_percent,
            "discount_amount": round(discount_amount, 2),
            "final_price": round(final_price, 2)
        }
    except Exception as e:
        return {"error": f"Invalid price or discount code: {e}"}
    
    
# Define the tool for e-commerce search
@tool
def search_website(user_query: str) -> List[Dict]:
    """Search for a product based on user query and return all related attributes."""
    params = {
    "q": f"{user_query} site:amazon.in",
    # Add your serpapi key here
    "api_key": ""
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    # Add your user agent here. You can find the user agent from https://www.whatismybrowser.com
    HEADERS = ({'User-Agent':'', 'Accept-Language': 'en-US, en;q=0.5'})

    scraped_result = []
    # Extract and display results

    for i, result in enumerate(results.get("organic_results", [])):
        # print(f"{result['link']}")
        
        if '%' in result['link']:
            webpage = requests.get(result['link'], headers=HEADERS)

            # Soup Object containing all data
            soup = BeautifulSoup(webpage.content, "html.parser")
            # Fetch links as List of Tag Objects
            links = soup.find_all("a", attrs={'class':'a-link-normal s-no-outline'})

            # Store the links
            links_list = []

            # Loop for extracting links from Tag Objects
            for link in links:
                    links_list.append(link.get('href'))
            
            for i, link in enumerate(links_list):
                d = {}

                new_webpage = requests.get("https://www.amazon.in" + link, headers=HEADERS)
                new_soup = BeautifulSoup(new_webpage.content, "html.parser")

                d['link'] = f"{'https://www.amazon.in' + link}"
                d['title'] = get_title(new_soup)
                d['price'] = get_price(new_soup)
                d['rating'] = get_rating(new_soup)
                d['reviews'] = get_review_count(new_soup)
                d['availability'] = get_availability(new_soup)
                d['delivery_date'] = get_delivery_time(new_soup)
                d['size'] = get_size(new_soup)
                d['return_policy'] = get_return_policy(new_soup)
                
                scraped_result.append(d)
                print(scraped_result[i])
                if len(scraped_result) > 20:
                    break
            
            break
        
        else:    
            d = {}
            # Loop for extracting product details from each link 
            webpage = requests.get(result['link'], headers=HEADERS)
            new_soup = BeautifulSoup(webpage.content, "html.parser")
            
            d['link'] = link
            d['title'] = get_title(new_soup)
            d['price'] = get_price(new_soup)
            d['rating'] = get_rating(new_soup)
            d['reviews'] = get_review_count(new_soup)
            d['availability'] = get_availability(new_soup)
            d['delivery_date'] = get_delivery_time(new_soup)
            d['size'] = get_size(new_soup)
            d['return_policy'] = get_return_policy(new_soup)
            
            scraped_result.append(d)
            
            # print(scraped_result[i])
            if len(scraped_result) > 20:
                break
    
    return scraped_result
    
# Define tools list
tools = [search_website]

# Bind tools to the model (using Anthropic as in your example)
llm = ChatAnthropic(model="claude-3-5-haiku-20241022")
model_with_tools = llm.bind_tools(tools)

# System message
sys_msg = SystemMessage(content="You are a helpful e-commerce search assistant.")

# Chatbot function
def chatbot(state: MessagesState) -> MessagesState:
    response = model_with_tools.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}

# Build the pipeline
pipeline = StateGraph(MessagesState)

pipeline.add_node("CHATBOT_AGENT", chatbot)
pipeline.add_node("tools", ToolNode(tools))

pipeline.add_edge(START, "CHATBOT_AGENT")
pipeline.add_conditional_edges("CHATBOT_AGENT", tools_condition)
pipeline.add_edge("tools", "CHATBOT_AGENT")

# Initialize memory
memory = MemorySaver()
config = {"configurable": {"thread_id": "1"}}

# Compile the pipeline
app = pipeline.compile(checkpointer=memory)

# Terminal-based chat interface
print("Welcome to the E-Commerce Search Assistant! Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Goodbye!")
        break
    
    # Invoke the pipeline with the user input
    response = app.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
    assistant_response = response["messages"][-1].content
    
    # Display the assistant's response
    print(f"Bot: {assistant_response}")
