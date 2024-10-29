import React, { useState, useEffect } from "react";
import axios from "axios";
import ApiUtill from "../ApiUtill";
import '../App.css';
import {Card, CardHeader, CardBody, Button,Textarea,CardFooter, Divider, Link, Image} from "@nextui-org/react";
import {Select, SelectSection, SelectItem} from "@nextui-org/select";
import {CircularProgress} from "@nextui-org/react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'

// Define rating options array
const ratingOptions = [...Array(11)].map((_, i) => ({
  value: String(i),
  label: String(i)
}));

// Create a reusable rating selector component
const RatingSelect = ({ label, value, onChange }) => (
  <div className="flex flex-col max-w-xs">
    <div className="block text-sm font-medium text-white">{label}</div>
    <Select
      label="Select rating"
      placeholder="Select rating"
      selectedKeys={value ? [value] : []}  
      onChange={(e) => onChange(e.target.value)}
    >
      {ratingOptions.map(option => (
        <SelectItem key={option.value} value={option.value}>
          {option.label}
        </SelectItem>
      ))}
    </Select>
  </div>
);

const ModelRatings = ({ model, ratings, onRatingChange }) => (
  <>
    <RatingSelect 
      key={`${model}-level-of-details`}
      label="Level of Details"
      value={ratings[model].levelOfDetails}
      onChange={(value) => onRatingChange(model, 'levelOfDetails', value)}
    />
    <RatingSelect 
      key={`${model}-reasonability`}
      label="Reasonability"
      value={ratings[model].routeReasonabilityRating}
      onChange={(value) => onRatingChange(model, 'routeReasonabilityRating', value)}
    />
    <RatingSelect 
      key={`${model}-representative`}
      label="Representativeness"
      value={ratings[model].representativeRating}
      onChange={(value) => onRatingChange(model, 'representativeRating', value)}
    />
    <RatingSelect 
      key={`${model}-overall`}
      label="Overall rating"
      value={ratings[model].overallRating}
      onChange={(value) => onRatingChange(model, 'overallRating', value)}
    />
  </>
);

function HomePage() {
  const [gptmessages, setgptMessages] = useState([]);
  const [ourmodelmessages, setourmodelMessages] = useState([]);
  const [xxmodelmessages, setxxmodelMessages] = useState([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [newMessage, setNewMessage] = useState(null);
  const [feedback, setFeedback] = useState("");
  const [ratings, setRatings] = useState({
    gpt: {
      levelOfDetails: null,
      overallRating: null,
      routeReasonabilityRating: null,
      representativeRating: null,
    },
    ourmodel: {
      levelOfDetails: null,
      overallRating: null,
      routeReasonabilityRating: null,
      representativeRating: null,
    },
    xxmodel: {
      levelOfDetails: null,
      overallRating: null,
      routeReasonabilityRating: null,
      representativeRating: null,
    },
    conversation_id: null,
    feedback: "",
  });


  const [feedbackVisible, setFeedbackVisible] = useState(false);
  const [gptloading, setgptLoading] = useState(false);
  const [xxmodelloading, setxxmodelLoading] = useState(false);
  const [ourmodelloading, setourmodelLoading] = useState(false);

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };
 

  const handleSendMessage = async () => {
    if (input.trim() === "") return;

    const systemMessage = {"role": "system", "content": "You are a professional itinerary planner. Output the itinerary based on the user's request directly, do not ask for any additional information."};
    const userMessage = {"role": "user", "content": input};

    try {
      // 首先检查查询是否可用
      const availabilityResponse = await axios.post(ApiUtill.url_root + 'is_query_available', { query: input });
      
      if (availabilityResponse.status !== 200) {
        // 如果查询不可用,显示错误消息并返回
        alert(availabilityResponse.data.error || "Invalid Query");
        return;
      }

      // 如果查询可用,继续执行原有的逻辑
      setNewMessage({
        gpt: [systemMessage, userMessage],
        ourmodel: [userMessage],
        xxmodel: [userMessage]
      });

      setgptLoading(true);
      setourmodelLoading(true);
      setxxmodelLoading(true);

      const response = await axios.post(ApiUtill.url_root + 'start_session', { query: input });
      const newConversationId = response.data.conversation_id;
      setConversationId(newConversationId);
      
      // Update conversation_id in ratings
      setRatings(prevRatings => ({
        ...prevRatings,
        conversation_id: newConversationId
      }));

    } catch (error) {
      console.error("Error:", error);
      alert(error.response?.data?.error || "Something wrong, please retry");
      setgptLoading(false);
      setourmodelLoading(false);
      setxxmodelLoading(false); 
    } finally {
      document.querySelector('input[type="text"]').focus();
    }
  };

  useEffect(() => {
    if (conversationId && newMessage) {
      fetchAllModelResponses(newMessage, conversationId);
      setNewMessage(null);
    }
  }, [conversationId, newMessage]);

  const fetchAllModelResponses = async (newMessage, conversationId) => {
    // 设置所有模型的loading状态
    setgptLoading(true);
    setourmodelLoading(true);
    setxxmodelLoading(true);

    const modelRequests = [
      // GPT请求
      {
        request: axios.post(ApiUtill.url_root + ApiUtill.url_gpt, {
          query: newMessage.gpt,
          conversation_id: conversationId,
        }),
        type: 'gpt',
        setLoading: setgptLoading,
        setMessages: setgptMessages,
      },
      // Our model请求
      {
        request: axios.post(ApiUtill.url_root + ApiUtill.url_ourmodel, {
          query: newMessage.ourmodel,
          conversation_id: conversationId,
        }),
        type: 'ourmodel',
        setLoading: setourmodelLoading,
        setMessages: setourmodelMessages,
      },
      // XX model请求
      {
        request: axios.post(ApiUtill.url_root + ApiUtill.url_xxmodel, {
          query: newMessage.xxmodel,
          conversation_id: conversationId,
        }),
        type: 'xxmodel',
        setLoading: setxxmodelLoading,
        setMessages: setxxmodelMessages,
      }
    ];

    const requests = modelRequests.map(async ({ request, type, setLoading, setMessages }) => {
      try {
        const response = await request;
        const responseData = response.data;
        
        // 根据不同模型类型处理响应数据
        const messageContent = {
          gpt: responseData.gpt_response,
          ourmodel: responseData.our_response,
          xxmodel: responseData.xxmodel_response,
        }[type];

        setMessages((prevMessages) => [
          ...prevMessages,
          {
            role: "assistant",
            content: messageContent,
            accommodationRating: responseData.accommodationRating,
            restaurantAvgRating: responseData.restaurantAvgRating,
            attractionsAvgRating: responseData.attractionsAvgRating,
            overallRating: responseData.overall_rating
          }
        ]);
      } catch (error) {
        console.error(`Error fetching ${type} response:`, error);
      } finally {
        setLoading(false);
      }
    });

    try {
      await Promise.allSettled(requests);
    } catch (error) {
      console.error("Error in fetchAllModelResponses:", error);
    }
  };
  

  const handleRatingChange = (model, ratingType, value) => {
    setRatings((prevRatings) => ({
      ...prevRatings,
      [model]: {
        ...prevRatings[model],
        [ratingType]: value
      }
    }));
  };

  const areAllRatingsComplete = () => {
    const { gpt, ourmodel, xxmodel } = ratings;
    return [gpt, ourmodel, xxmodel].every((model) =>
      Object.values(model).every((rating) => rating !== null && rating !== undefined)
    );
  };

  const handleSubmitRatings = async () => {
    if (conversationId === null) {
      alert("Conversation has not started yet");
      return;
    }

    console.log('Current ratings:', ratings);

    const isValidRating = (rating) => {
      console.log('Checking rating:', rating, typeof rating);
      if (rating === null || rating === undefined) {
        return false;
      }
      const numRating = Number(rating);
      return !isNaN(numRating) && numRating >= 0 && numRating <= 10;
    };

    const allModels = ['gpt', 'ourmodel', 'xxmodel'];
    const allRatingTypes = ['overallRating', 'routeReasonabilityRating', 'representativeRating', 'levelOfDetails'];

    const hasEmptyRatings = allModels.some(model => 
      allRatingTypes.some(type => {
        const rating = ratings[model][type];
        console.log(`${model}.${type}:`, rating);
        return rating === null || rating === undefined;
      })
    );

    if (hasEmptyRatings) {
      alert("Please ensure all ratings are filled out!");
      return;
    }

    const hasInvalidRatings = allModels.some(model => 
      allRatingTypes.some(type => 
        !isValidRating(ratings[model][type])
      )
    );

    if (hasInvalidRatings) {
      alert("Please ensure all ratings are between 0 and 10!");
      return;
    }

    try {
      const ratingData = {
        conversation_id: conversationId,
        gpt: {
          level_of_details: ratings.gpt.levelOfDetails,
          overall_rating: ratings.gpt.overallRating,
          route_reasonability_rating: ratings.gpt.routeReasonabilityRating,
          representative_rating: ratings.gpt.representativeRating
        },
        ourmodel: {
          level_of_details: ratings.ourmodel.levelOfDetails,
          overall_rating: ratings.ourmodel.overallRating,
          route_reasonability_rating: ratings.ourmodel.routeReasonabilityRating,
          representative_rating: ratings.ourmodel.representativeRating
        },
        xxmodel: {
          level_of_details: ratings.xxmodel.levelOfDetails,
          overall_rating: ratings.xxmodel.overallRating,
          route_reasonability_rating: ratings.xxmodel.routeReasonabilityRating,
          representative_rating: ratings.xxmodel.representativeRating
        },
        feedback: ratings.feedback || ""
      };

      console.log('Submitting ratings:', ratingData);

      const response = await axios.post(ApiUtill.url_root + ApiUtill.url_rating, ratingData);
      
      if (response.status === 200) {
        alert("Ratings and feedback submitted successfully!");
        
        // 重置评分和反馈,但保留对话内容
        const initialRatings = {
          gpt: {
            overallRating: null,
            routeReasonabilityRating: null,
            representativeRating: null,
          },
          ourmodel: {
            overallRating: null,
            routeReasonabilityRating: null,
            representativeRating: null,
          },
          xxmodel: {
            overallRating: null,
            routeReasonabilityRating: null,
            representativeRating: null,
          },
          conversation_id: null,
          feedback: ""
        };
        
        setRatings(initialRatings);
        setFeedbackVisible(false);
        setConversationId(null);
        // 注意:不清空以下内容
        // setInput("")
        // setgptMessages([])
        // setourmodelMessages([])
        // setxxmodelMessages([])
      }
    } catch (error) {
      console.error("Error submitting ratings:", error);
      alert("Failed to submit ratings!");
    }
  };

  const handleShowFeedback = () => {
    if (areAllRatingsComplete()) {
      setFeedbackVisible(true);
    }else{
      alert("Please finish all ratings first!")
    }
  };
  return (
    <div className="App">

      <h1>Plan a trip within the United States</h1>

      <div className="input-box">
        <Textarea
      label="Enter your question"
      placeholder="e.g.Please help me plan a trip from St. Petersburg to Rockford spanning 3 days October 27th to October 29th, 2024. The travel should be planned for a single person with a budget of $1,700."
      className="max-w-xs"
      size="lg"
      value={input}
      onChange={handleInputChange}
    />
     
        <Button onClick={handleSendMessage} radius="full">
        Submit
      </Button>
      <div className="note-area">
      <p>Enter your question and wait for the results (you may temporarily leave the page as generating the results could take up to 10 minutes). After reviewing the results, rate the output for each plan.</p>
      </div>
      </div>

      <div className="flex-chat-container">
        <div className="chat-box">
          <h1>Plan 1</h1>
          <Card className="py-4">
      <CardHeader className="pb-0 pt-2 px-4 flex-col items-start">
        <h4 className="font-bold text-large">Chat</h4>
      </CardHeader>
      <CardBody className="overflow-visible py-2">
        <div className="gpt-chat-box">
          {gptmessages.length === 0 && !gptloading && (
            <p>No chat available</p>
          )}
          {gptmessages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <ReactMarkdown className="myMdStyle" remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          ))}
          {gptloading && <p>Loading... <CircularProgress aria-label="Loading..." /></p>}
        </div>
        <Card>
      <CardBody>
        <CardHeader tag="h5">Ratings overview</CardHeader>
       
        {gptmessages.slice(-1).map((message) => (
  <div >
    <strong>Accommodation Rating: {message.accommodationRating}</strong>
    <br />
    <strong>Restaurant Avg Rating: {message.restaurantAvgRating}</strong>
    <br />
    <strong>Attractions Avg Rating: {message.attractionsAvgRating}</strong>
    <br/>
    <strong>Overall Rating:{message.overallRating}</strong>
  </div>
))}

      </CardBody>
    </Card>
      </CardBody>
      </Card>
    

      <ModelRatings 
        model="gpt"
        ratings={ratings}
        onRatingChange={handleRatingChange}
      />
    </div>

    <div className="chat-box">
          <h1>Plan 2</h1>
            <Card className="py-4">
      <CardHeader className="pb-0 pt-2 px-4 flex-col items-start">
        <h4 className="font-bold text-large">Chat</h4>
      </CardHeader>
      <CardBody className="overflow-visible py-2">
        <div className="ourmodel-chat-box">
          {ourmodelmessages.length === 0 && !ourmodelloading && (
            <p>No chat available</p>
          )}
          {ourmodelmessages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <ReactMarkdown className="myMdStyle" remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          ))}
          {ourmodelloading && <p>Loading... <CircularProgress aria-label="Loading..." /></p>}
          
        </div>
        <Card>
      <CardBody>
        <CardHeader tag="h5">Ratings overview</CardHeader>
       
        {ourmodelmessages.slice(-1).map((message) => (
  <div >
    <strong>Accommodation Rating: {message.accommodationRating}</strong>
    <br />
    <strong>Restaurant Avg Rating: {message.restaurantAvgRating}</strong>
    <br />
    <strong>Attractions Avg Rating: {message.attractionsAvgRating}</strong>
    <br/>
    <strong>Overall Rating:{message.overallRating}</strong>
  </div>
))}
        
      </CardBody>
    </Card>
      </CardBody>
    </Card>
      <ModelRatings 
        model="ourmodel"
        ratings={ratings}
        onRatingChange={handleRatingChange}
      />
      </div>
        <div className="chat-box">
          <h1>Plan 3</h1>
          <Card className="py-4">
      <CardHeader className="pb-0 pt-2 px-4 flex flex-col items-start">
        <h4 className="font-bold text-large">Chat </h4>
      </CardHeader>
      <CardBody className="overflow-visible py-2">
        <div className="xxmodel-chat-box">
          {xxmodelmessages.length === 0 && !xxmodelloading && (
            <p>No chat available</p>
          )}
          {xxmodelmessages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <ReactMarkdown className="myMdStyle" remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          ))}
          {xxmodelloading && <p>Loading... <CircularProgress aria-label="Loading..." /></p>}
        </div>
        <Card>
      <CardBody>
        <CardHeader tag="h5">Ratings overview</CardHeader>
       
        {xxmodelmessages.slice(-1).map((message) => (
  <div >
    <strong>Accommodation Rating: {message.accommodationRating}</strong>
    <br />
    <strong>Restaurant Avg Rating: {message.restaurantAvgRating}</strong>
    <br />
    <strong>Attractions Avg Rating: {message.attractionsAvgRating}</strong>
    <br/>
    <strong>Overall Rating:{message.overallRating}</strong>
  </div>
))}
        
      </CardBody>
    </Card>
      </CardBody>
    </Card>
    

      <ModelRatings 
        model="xxmodel"
        ratings={ratings}
        onRatingChange={handleRatingChange}
      />
    </div>
      </div>

      {feedbackVisible && (
        <div className="advice-area mb-8">
          <Textarea
            label="Description"
            variant="bordered"
            placeholder="Enter your description"
            disableAnimation
            disableAutosize
            classNames={{
              base: "max-w-xs",
              input: "resize-y min-h-[40px]",
            }}
            value={ratings.feedback}
            onChange={(e) => 
              setRatings((prevRatings) => ({
                ...prevRatings,
                feedback: e.target.value  
              }))
            }
          />
        </div>
      )}

      <div className="flex flex-col sm:flex-row justify-between sm:justify-center items-center gap-4 w-full max-w-4xl mx-auto px-4" style={{ marginTop: '30px' }}>
        <Button onClick={handleSubmitRatings} className="w-full sm:w-auto text-sm sm:text-base whitespace-normal h-auto py-2">
        Submit all ratings and feedback
        </Button>
        
        <Button onClick={handleShowFeedback} className="w-full sm:w-auto text-sm sm:text-base whitespace-normal h-auto py-2">
        Additional feedback after ratings (Optional)
        </Button>
      </div>
    </div>
  );
}

export default HomePage;
