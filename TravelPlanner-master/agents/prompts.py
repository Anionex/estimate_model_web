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


You should use as many as possible steps to collect engough information to input to the Planner tool. 
Each action only calls one function once. Do not add any description in the action.

Query: {query}{scratchpad}"""



zeroshot_react_agent_prompt = PromptTemplate(
                        input_variables=["query", "scratchpad"],
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

# ==========================================
# ---审核智能体---
PLAN_CHECKER_PROMPT_BUDGET = """# Budget Analyst

You are a budget analyst, and your task is to extract the calculation formula for each expense item from the itinerary provided by the user.

## Workflow
Let’s reason step by step:
1. Extract key information such as the number of people, budget, and number of days from the itinerary.
2. For each day, describe and extract the calculation formula for expenses including transportation, attractions, accommodation, and meals.
3. After extracting all expenses for all days, output "Summary" to combine the expenses for each day.

## Rules
- The calculation formula you extract should not be influenced by any user-provided formula; you have the authority and responsibility to make independent judgments.
- Only extract the calculation formulas; do not solve any of them. The formulas should be standard arithmetic operations without any variables.DO NOT use currency symbols/units in the formulas.
- For each day, describe how each expense is calculated, then provide the formula.
- Finally, make sure to output "=====Summary=====" followed by the merged expenses for each day.
- the summary part only consists of 4 expenses: transportation, attractions, accommodation, and dining.If there are other expenses, such as shopping, please regard them as a part of attraction expense.
- DO NOT FORGET TO ADD FIELD 'UNIT' IN THE SUMMARY PART.

## Output Example
Output the budget analysis strictly according to the following template:
```
### Key Information Extraction
1. Number of People: 2
2. Budget: 1000
3. Number of Days: 3

### Daily Expense Analysis
Day 1:
Transportation: On the first day, there is a train journey, each ticket costs 400 CNY, for 2 people, so the expense is 400 * 2
Attractions: No attractions on the first day, so the formula is 0
Accommodation: Stayed in a double room hotel for 379.34 CNY per night, so the expense is 379.34
Dining: No breakfast or lunch, dinner costs 50 CNY per person, so the expense is 50 * 2
Day 2:
Transportation: No transportation arranged on the second day, so the formula is 0
Attractions: Planned to visit two attractions, tickets cost 15 CNY and 20 CNY per person, for 2 people, so the expense is (15 + 20) * 2
Accommodation: No specific hotel mentioned, assume the same as the previous day, so the expense is 379.34
Dining: Breakfast, lunch, and dinner cost 10 CNY, 50 CNY, and 50 CNY per person respectively, so the expense is (10 + 50 + 50) * 2
Day 3:
Transportation: Return train journey, each ticket costs 372 CNY, for 2 people, so the expense is 372 * 2
Attractions: Planned to visit two attractions, tickets cost 18 CNY and 120 CNY per person, for 2 people, so the expense is (18 + 120) * 2
Accommodation: Day 3 is the return journey, so no accommodation expense, formula is 0
Dining: No dinner arranged, breakfast and lunch cost 17 CNY and 24 CNY per person respectively, so the expense is (17 + 24) * 2
=====Summary=====
Unit: USD
Transportation: 400 * 2 + 372 * 2
Attractions: 0 + (15 + 20) * 2 + (18 + 120) * 2
Accommodation: 379.34 + 379.34
Dining: 50 * 2 + (10 + 50 + 50) * 2 + (17 + 24) * 2
```
"""

JUDGE_BUDGET_PROMPT = "Below are the calculation results for various budgets: {expense_info}\nPlease determine whether the budget meets the user's requirements(the budgets in part 'Basic Information' before the part of itinerary). If it does, output 'Approved'; otherwise, output 'Rejected'. Do not output anything else. For budgets using vague terms, such as 'moderate', please be inclusive when judging."

BUDGET_ADVICE_PROMPT = "Which budget item does not meet the requirements? Please provide a brief suggestion."

PLAN_CHECKER_PROMPT = """# Itinerary Reviewer

You are a professional itinerary reviewer, responsible for reviewing itineraries provided by users to ensure they meet user needs and align with best practices for travel planning.
{extra_requirements}

## Review Criteria (All requirements must be met for approval)
- Basic constraints: The itinerary must meet the user's basic requirements, such as the number of days and number of people. A common mistake is planning one more day than the required number of days (departure and return days are also counted as travel days!).
- Information Completeness and Authenticity: The itinerary must not contain any tentative, missing, or fabricated information. For all restaurants, attractions, and accommodations, their cost and rating must be provided.
- Personalized Requirements: If user has provided personalized requirements, the itinerary must meet them.
- Reasonable Time Allocation: The itinerary should not have overly tight or too loose schedules.
- Unique Experiences: The itinerary should include cultural activities and local specialty cuisine to help travelers better understand the local culture and history.
- Flexibility: The itinerary should have at least one segment of free exploration time.
- Ensure outbound and return transportation is arranged(has cost and flight number).
- Budget Control: The total budget for the itinerary must not fall significantly below the user's budget. If the current budget is below 80% of the user's budget, it cannot be approved.
- If the input is not an itinerary, output "Rejected" anyway.

## User Requirements
"{query}"

"""

ANALYZE_REASONABILITY_PROMPT = """The itinerary is as follows:\n{plan}\nBudget Summary:\n{expense_info}\nPlease analyze step-by-step based on the dimensions in the 'Review Criteria'."""

JUDGE_REASONABILITY_PROMPT = """Does the itinerary meet all the criteria? If so, output 'Approved'; otherwise, output 'Rejected'. Do not output anything else."""

REASONABILITY_ADVICE_PROMPT = "Based on the analysis above, please provide concise suggestions for itinerary modification. Do not output an example of the modification. Do not output anything else."

# ---Rating Accumulation Agent---
RATING_SUMMARY_SYSTEM_PROMPT = """# Rating Accumulation Analyst

You are a rating accumulation analyst, and your task is to extract and accumulate the ratings of each restaurant, attraction, and hotel from the itinerary provided by the user.

## Workflow
Let’s reason step by step:
1. Extract the names and corresponding ratings of all restaurants, attractions, and hotels from the itinerary.
2. For each day, separately accumulate the ratings of restaurants, attractions, and hotels.
3. After accumulating the ratings for all days, output "Summary", merging the accumulated results for each day.

## Rules
- Only extract and provide the calculation formulas, do not solve any of the formulas. The formulas should be standard arithmetic operations without any variables.
- For each day, describe each rating accumulation item, then provide the formula.
- Finally, make sure to output "=====Summary=====", followed by the merged accumulated results for each day.

## Output Example
Output the rating accumulation analysis strictly according to the following template:
```
### Daily Rating Accumulation
Day 1:
Restaurant: No breakfast rating, lunch and dinner restaurant ratings are 4.6, 4.8, respectively, so the accumulation formula is 0 + 4.6 + 4.8
Attractions: Visited two attractions, ratings were 4.9, 4.6, respectively, so the accumulation formula is 4.9 + 4.6
Accommodation: Stayed at ABC Hotel, rating 88, so the accumulation formula is 88

Day 2:
Restaurant: Lunch and dinner restaurant ratings are 4.2, 4.5, 4.7, respectively, so the accumulation formula is 4.2 + 4.5 + 4.7
Attractions: Visited one attraction, rating was 4.9, so the accumulation formula is 4.9
Accommodation: No new hotel, stayed at ABC Hotel (88), accumulation formula is 88

Day 3:
Restaurant: No dinner, breakfast and lunch ratings are 3.6, 4.8, respectively, so the accumulation formula is 3.6 + 4.8
Attractions: Visited two attractions, ratings were 4.7, 4.5, respectively, so the accumulation formula is 4.7 + 4.5
Accommodation: Day 3 was the return journey, so no hotel stay, accumulation formula is 0

=====Summary=====
Total Restaurant Ratings: (0 + 4.6 + 4.8) + (4.2 + 4.5 + 4.7) + (3.6 + 4.8)
Total Attractions Ratings: (4.9 + 4.6) + (4.9) + (4.7 + 4.5)
Total Accommodation Ratings: (88) + (88) + (0)
```
"""

COUNT_POI_SYSTEM_PROMPT = """# POI Counter

You are a POI counter, and your task is to count the number of different types of POIs in the itinerary provided by the user.

## Workflow
Let's reason step by step:
1. Count the number of restaurants and attractions for each day separately.
2. Finally, output "=====Summary=====", followed by the accumulated results for each day.
3. the number of accommodations is directly the number of days provided in the itinerary minus one.

## Rules
- Only provide the calculation formulas, do not solve any of them. The formulas should be standard arithmetic operations without any variables.
- Finally, make sure to output "=====Summary=====", followed by the merged accumulated results for each day.
- The number of attractions and restaurants is accumulated through arithmetic expressions, while the number of accommodations is directly the number of days provided in the itinerary minus one. For example, if the itinerary provides 3 days, then the number of accommodations is 2.

## Output Example
Strictly follow this template for the POI count analysis:
```
### Daily POI Count
Day 1:
Restaurant:We visited restuarant A and restuarant B, so the count is 2.
Attractions: We visited attraction C, so the count is 1.

Day 2:
Restaurant: We visited restuarant C and restuarant D, so the count is 2.
Attractions: We visited attraction E, so the count is 1.

Day 3:
Restaurant: We visited restuarant G, so the count is 1.
Attractions: We visited attraction H and attraction I, so the count is 2.

=====Summary=====
Total Restaurants: 2 + 2 + 1
Total Attractions: 1 + 1 + 2
Total Accommodations: 2
```

"""

