from langchain.prompts import PromptTemplate


ZEROSHOT_REACT_INSTRUCTION = """Collect information for a query plan using interleaving 'Thought', 'Action', and 'Observation' steps. Ensure you gather valid information related to transportation, dining, attractions, and accommodation. All information should be written in Notebook, which will then be input into the Planner tool. Note that the nested use of tools is prohibited. 'Thought' can reason about the current situation, and 'Action' can have 8 different types:
(1) FlightSearch[Departure City IATA Code, Destination City IATA Code, Date]:
Description: A flight information retrieval tool.
Parameters:
Departure City IATA code: The IATA code of the city you'll be flying out from.
Destination City IATA code: The IATA code of the city you aim to reach.
Date: The date of your travel in YYYY-MM-DD format.
Example: FlightSearch[NYC, LON, 2022-10-01] would fetch flights from New York to London on October 1, 2022.

(2) GoogleDistanceMatrix[Origin, Destination, Mode]:
Description: Estimate the distance, time and cost between two cities.
Parameters:
Origin: The departure city of your journey.
Destination: The destination city of your journey.
Mode: The method of transportation. 
Example: GoogleDistanceMatrix[Paris, Lyon, driving] would provide driving distance, time and cost between Paris and Lyon.

(3) AccommodationSearch[City, Check-In Date, Check-Out Date, Adults]:
Description: Discover accommodations in your desired city.
Parameter: 
City - The name of the city where you're seeking accommodation.
Check-In Date - The date of you check-in in YYYY-MM-DD format.
Check-Out Date - The date of you check-out in YYYY-MM-DD format.    
Adults - The number of adults you're seeking accommodation for.
Example: AccommodationSearch[Rome, 2022-02-01, 2022-02-03, 2] would present a list of hotel rooms in Rome.

(4) RestaurantSearch[City, Query]:
Description: Explore dining options in a city of your choice.
Parameter: 
City – The name of the city where you're seeking restaurants.
Query - The type of restaurants you're seeking.
Example: 
RestaurantSearch[Tokyo, Japanese] would show a curated list of Japanese restaurants in Tokyo.
RestaurantSearch[Paris, must-visit restaurants] would show a curated list of must-visit restaurants in Paris.

(5) AttractionSearch[City, Query]:
Description: Find attractions in a city of your choice.
Parameter: 
City – The name of the city where you're seeking attractions.
Query - The type of attractions you're seeking.
Example: 
AttractionSearch[London, must-visit attractions] would return must-visit attractions in London.
AttractionSearch[Paris, museums] would return museums in Paris.

(6) CitySearch[State]
Description: Find cities in a state of your choice.
Parameter: State – The name of the state where you're seeking cities.
Example: CitySearch[California] would return cities in California.

(7) NotebookWrite[Short Description]
Description: Writes a new data entry into the Notebook tool with a short description. This tool should be used immediately after FlightSearch, AccommodationSearch, AttractionSearch, RestaurantSearch or GoogleDistanceMatrix. Only the data stored in Notebook can be seen by Planner. So you should write all the information you need into Notebook.
Parameters: Short Description - A brief description or label for the stored data. You don't need to write all the information in the description. The data you've searched for will be automatically stored in the Notebook.
Example: NotebookWrite[Flights from Rome to Paris in 2022-02-01] would store the informatrion of flights from Rome to Paris in 2022-02-01 in the Notebook.

(8) Planner[Query]
Description: A smart planning tool that crafts detailed plans based on user input and the information stroed in Notebook.
Parameters: 
Query: The query from user.
Example: Planner[Give me a 3-day trip plan from Seattle to New York] would return a detailed 3-day trip plan.

If no date specified, start planning from the day after {current_date}.
You should use as many as possible steps to collect engough information to input to the Planner tool. 
Each action only calls one function once. Do not add any description in the action.

Query: {query}{scratchpad}"""



zeroshot_react_agent_prompt = PromptTemplate(
                        input_variables=["query", "scratchpad", "current_date"],
                        template=ZEROSHOT_REACT_INSTRUCTION,
                        )

PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****

Given information: {text}
Query: {query}
Travel Plan:"""

COT_PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and hotel names together with thier ratings and expenses. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with common sense. Attraction visits and meals are expected to be diverse. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B). 

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413(Cost: $87/person), from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte(Cost: $12/person, Rating: 4.2).
Attraction: The Charlotte Museum of History, Charlotte(Cost: $9/person, Rating: 4.7).
Lunch: Cafe Maple Street, Charlotte(Cost: $14/person, Rating: 4.3).
Dinner: Bombay Vada Pav, Charlotte(Cost: $18/person, Rating: 4.6).
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte(Cost: $95/person/night, Rating: 4.4).

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte(Cost: $11/person, Rating: 4.1).
Attraction: The Mint Museum, Charlotte(Cost: $8/person, Rating: 4.8);Romare Bearden Park, Charlotte(Cost: free).
Lunch: Birbal Ji Dhaba, Charlotte(Cost: $13/person, Rating: 4.5).
Dinner: Pind Balluchi, Charlotte(Cost: $22/person, Rating: 4.9).
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte(Cost: $92/person/night, Rating: 4.4).

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167(Cost: $93/person), from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte(Cost: $7/person, Rating: 3.9).
Attraction: Books Monument, Charlotte(Cost: $6/person, Rating: 4.0).
Lunch: Olive Tree Cafe, Charlotte(Cost: $12/person, Rating: 4.1).
Dinner: Kylin Skybar, Charlotte(Cost: $19/person, Rating: 4.7).
Accommodation: -

***** Example Ends *****

Given information: {text}
If no date specified, start planning from the day after {current_date}.
Query: {query}
Travel Plan: Let's think step by step. First, """

REACT_PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and hotel names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with common sense. Attraction visits and meals are expected to be diverse. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B). Solve this task by alternating between Thought, Action, and Observation steps. The 'Thought' phase involves reasoning about the current situation. The 'Action' phase can be of two types:
(1) CostEnquiry[Sub Plan]: This function calculates the cost of a detailed sub plan, which you need to input the people number and plan in JSON format. The sub plan should encompass a complete one-day plan. An example will be provided for reference.
(2) Finish[Final Plan]: Use this function to indicate the completion of the task. You must submit a final, complete plan as an argument.
***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
You can call CostEnquiry like CostEnquiry[{{"people_number": 7,"day": 1,"current_city": "from Ithaca to Charlotte","transportation": "Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46","breakfast": "Nagaland's Kitchen, Charlotte","attraction": "The Charlotte Museum of History, Charlotte","lunch": "Cafe Maple Street, Charlotte","dinner": "Bombay Vada Pav, Charlotte","accommodation": "Affordable Spacious Refurbished Room in Bushwick!, Charlotte"}}]
You can call Finish like Finish[Day: 1
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -]
***** Example Ends *****

You must use Finish to indict you have finished the task. And each action only calls one function once.
Given information: {text}
Query: {query}{scratchpad} """

REFLECTION_HEADER = 'You have attempted to give a sub plan before and failed. The following reflection(s) give a suggestion to avoid failing to answer the query in the same way you did previously. Use them to improve your strategy of correctly planning.\n'

REFLECT_INSTRUCTION = """You are an advanced reasoning agent that can improve based on self refection. You will be given a previous reasoning trial in which you were given access to an automatic cost calculation environment, a travel query to give plan and relevant information. Only the selection whose name and city match the given information will be calculated correctly. You were unsuccessful in creating a plan because you used up your set number of reasoning steps. In a few sentences, Diagnose a possible reason for failure and devise a new, concise, high level plan that aims to mitigate the same failure. Use complete sentences.  

Given information: {text}

Previous trial:
Query: {query}{scratchpad}

Reflection:"""

REACT_REFLECT_PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and hotel names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with common sense. Attraction visits and meals are expected to be diverse. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B). Solve this task by alternating between Thought, Action, and Observation steps. The 'Thought' phase involves reasoning about the current situation. The 'Action' phase can be of two types:
(1) CostEnquiry[Sub Plan]: This function calculates the cost of a detailed sub plan, which you need to input the people number and plan in JSON format. The sub plan should encompass a complete one-day plan. An example will be provided for reference.
(2) Finish[Final Plan]: Use this function to indicate the completion of the task. You must submit a final, complete plan as an argument.
***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
You can call CostEnquiry like CostEnquiry[{{"people_number": 7,"day": 1,"current_city": "from Ithaca to Charlotte","transportation": "Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46","breakfast": "Nagaland's Kitchen, Charlotte","attraction": "The Charlotte Museum of History, Charlotte","lunch": "Cafe Maple Street, Charlotte","dinner": "Bombay Vada Pav, Charlotte","accommodation": "Affordable Spacious Refurbished Room in Bushwick!, Charlotte"}}]
You can call Finish like Finish[Day: 1
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -]
***** Example Ends *****

{reflections}

You must use Finish to indict you have finished the task. And each action only calls one function once.
Given information: {text}
Query: {query}{scratchpad} """

planner_agent_prompt = PromptTemplate(
                        input_variables=["text","query"],
                        template = PLANNER_INSTRUCTION,
                        )

cot_planner_agent_prompt = PromptTemplate(
                        input_variables=["text","query"],
                        template = COT_PLANNER_INSTRUCTION,
                        )

react_planner_agent_prompt = PromptTemplate(
                        input_variables=["text","query", "scratchpad"],
                        template = REACT_PLANNER_INSTRUCTION,
                        )

reflect_prompt = PromptTemplate(
                        input_variables=["text", "query", "scratchpad"],
                        template = REFLECT_INSTRUCTION,
                        )

react_reflect_planner_agent_prompt = PromptTemplate(
                        input_variables=["text", "query", "reflections", "scratchpad"],
                        template = REACT_REFLECT_PLANNER_INSTRUCTION,
                        )