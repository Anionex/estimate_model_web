import React, { useState, useEffect } from "react";
import axios from "axios";
import ApiUtill from "../ApiUtill";
import '../App.css';
import {Card, CardHeader, CardBody, Button,Textarea,CardFooter, Divider, Link, Image} from "@nextui-org/react";
import {Select, SelectSection, SelectItem} from "@nextui-org/select";
import {CircularProgress} from "@nextui-org/react";
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
    feedback:"",
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

    const systemMessage = {"role": "system", "content": "请详细规划所述路线。要求遵循以下具体规则：1) 每个旅行日必须有详细的活动安排，包括主要景点和交通方式。2) 确保提供的住宿建议方便且符合预算。3) 给出至少一个餐厅建议，并注明特色菜。4) 在结尾部分，必须准确评估并给出你的计划的Accommodation Rating, Attractions Average Rating, Restaurant Average Rating, Overall Rating的值，满分为5，并以x/5的格式表示。注意：不得更改输出的名字，确保这些评级信息单独列出在输出的最后一部分。严格执行上述指令，将结果按要求格式化。"};
    const userMessage = {"role": "user", "content": input};
    
    setNewMessage({
      gpt: [systemMessage, userMessage],
      ourmodel: [userMessage],
      xxmodel: [userMessage]
    });
    

    setgptLoading(true);
    setourmodelLoading(true);
    setxxmodelLoading(true);

    try {
      const response = await axios.post(ApiUtill.url_root + 'start_session', { query: input });
      setConversationId(response.data.conversation_id);
    } catch (error) {
      console.error("Error starting session:", error);
      setgptLoading(false);
      setourmodelLoading(false);
      setxxmodelLoading(false); 
    } finally {
      //setInput("");
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
    try {
      // ChatGPT 请求
      setgptLoading(true);
      try {
        const gptResponse = await axios.post(ApiUtill.url_root + ApiUtill.url_gpt, {
          query: newMessage.gpt,
          conversation_id: conversationId,
        });
        setgptMessages((prevMessages) => [
          ...prevMessages,
          { role: "assistant", content: gptResponse.data.gpt_response,accommodationRating:gptResponse.data.accommodationRating,
            restaurantAvgRating:gptResponse.data.restaurantAvgRating,
            attractionsAvgRating:gptResponse.data.attractionsAvgRating,
          overallRating:gptResponse.data.overall_rating }
        ]);
      } catch (error) {
        console.error("Error fetching GPT response:", error);
      } finally {
        setgptLoading(false);
      }
  
      // 我们的模型请求
      setourmodelLoading(true);
      try {
        const ourmodelResponse = await axios.post(ApiUtill.url_root + ApiUtill.url_ourmodel, {
          query: newMessage.ourmodel,
          conversation_id: conversationId,
        });
        setourmodelMessages((prevMessages) => [
          ...prevMessages,
          { role: "assistant", content: ourmodelResponse.data.our_response,accommodationRating:ourmodelResponse.data.accommodationRating,
            restaurantAvgRating:ourmodelResponse.data.restaurantAvgRating,
            attractionsAvgRating:ourmodelResponse.data.attractionsAvgRating,
            overallRating:ourmodelResponse.data.overall_rating    }
        ]);
      } catch (error) {
        console.error("Error fetching our model response:", error);
      } finally {
        setourmodelLoading(false);
      }
  
      // xx模型请求
      setxxmodelLoading(true);
      try {
        const xxmodelResponse = await axios.post(ApiUtill.url_root + ApiUtill.url_xxmodel, {
          query: newMessage.xxmodel,
          conversation_id: conversationId,
        });
        setxxmodelMessages((prevMessages) => [
          ...prevMessages,
          { role: "assistant", content: xxmodelResponse.data.xxmodel_response,accommodationRating:xxmodelResponse.data.accommodationRating,
            restaurantAvgRating:xxmodelResponse.data.restaurantAvgRating,
            attractionsAvgRating:xxmodelResponse.data.attractionsAvgRating,
            overallRating:xxmodelResponse.data.overall_rating    }
        ]);
      } catch (error) {
        console.error("Error fetching xx model response:", error);
      } finally {
        setxxmodelLoading(false);
      }
  
    } catch (error) {
      console.error("Error in fetchAllModelResponses:", error);
    }
  };
  

  const handleRatingChange = (model, ratingType, value) => {
    const numericalValue = parseInt(value.replace(/[^\d]/g, ''), 10) || null;
    setRatings((prevRatings) => ({
      ...prevRatings,
    [model]: {
      ...prevRatings[model], 
      [ratingType]: numericalValue
      }
    }));
  };

  const areAllRatingsComplete = () => {
    const { gpt, ourmodel, xxmodel } = ratings;
    return [gpt, ourmodel, xxmodel].every((model) =>
      Object.values(model).every((rating) => rating !== null)
    );
  };

  const handleSubmitRatings = async () => {
    console.log(ratings)
    if (ratings.conversation_id === null) {
      alert("Conversation hasn't started.");
      return;
  }
    if (!areAllRatingsComplete()) {
      alert("Please rate all criteria!");
      return;
    }

    try {
      await axios.post(ApiUtill.url_root + ApiUtill.url_rating, {
        conversation_id: conversationId,
        ratings: {
          gpt: ratings.gpt,
          ourmodel: ratings.ourmodel,
          xxmodel: ratings.xxmodel,
        },
        feedback: feedback
      });
      alert("The ratings and feedback have been successfully submitted!");
      setRatings({
        conversation_id: null,
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
        }
      });
      setFeedback("");
      setFeedbackVisible(false);
    } catch (error) {
      console.error("Error submitting ratings:", error);
      alert("Failed to submit the rating!");
    } 
  };

  const handleShowFeedback = () => {
    if (areAllRatingsComplete()) {
      setFeedbackVisible(true);
    }else{
      alert("Please finish all ratings frist!")
    }
  };

  return (
    <div className="App">
      <h1>Plan a trip within the United States</h1>

      <div className="input-box">
        <Textarea
      label="Enter your question"
      placeholder="e.g.Please help me plan a trip from St. Petersburg to Rockford spanning 3 days from March 16th to March 18th, 2022. The travel should be planned for a single person with a budget of $1,700."
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
              <p>{message.content}</p>
            </div>
          ))}
          {gptloading && <p>Loading... <CircularProgress aria-label="Loading..." /></p>}
        </div>
        <Card>
      <CardBody>
        <CardHeader tag="h5">Ratings Overview</CardHeader>
       
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
    

      <div className="flex flex-col max-w-xs">
        <p className="block text-sm font-medium text-gray-700">Route Reasonability</p>
        <Select
          label="Select rating"
          placeholder="Select rating"
          value={ratings.gpt.routeReasonabilityRating || 0}
          onChange={(e) => handleRatingChange('gpt', 'routeReasonabilityRating', e.target.value)}
        >
           <SelectItem value={0}>0</SelectItem>
          <SelectItem value={1}>1</SelectItem>
          <SelectItem value={2}>2</SelectItem>
          <SelectItem value={3}>3</SelectItem>
          <SelectItem value={4}>4</SelectItem>
          <SelectItem value={5}>5</SelectItem>
          <SelectItem value={6}>6</SelectItem>
          <SelectItem value={7}>7</SelectItem>
          <SelectItem value={8}>8</SelectItem>
          <SelectItem value={9}>9</SelectItem>
          <SelectItem value={10}>10</SelectItem>
        </Select>
      </div>

      <div className="flex flex-col max-w-xs">
        <p className="block text-sm font-medium text-gray-700">Representativeness</p>
        <Select
          label="Select rating"
          placeholder="Select rating"
          value={ratings.gpt.representativeRating || 0}
          onChange={(e) => handleRatingChange('gpt', 'representativeRating', e.target.value)}
        >
          <SelectItem value={0}>0</SelectItem>
          <SelectItem value={1}>1</SelectItem>
          <SelectItem value={2}>2</SelectItem>
          <SelectItem value={3}>3</SelectItem>
          <SelectItem value={4}>4</SelectItem>
          <SelectItem value={5}>5</SelectItem>
          <SelectItem value={6}>6</SelectItem>
          <SelectItem value={7}>7</SelectItem>
          <SelectItem value={8}>8</SelectItem>
          <SelectItem value={9}>9</SelectItem>
          <SelectItem value={10}>10</SelectItem>
        </Select>
          </div>
          <div className="flex flex-col max-w-xs">
    <p className="block text-sm font-medium text-gray-700">Overall rating</p>
            <Select
          label="Select rating"
          placeholder="Select rating"
          value={ratings.gpt.overallRating || 0}
          onChange={(e) => handleRatingChange('gpt', 'overallRating', e.target.value)}
        >
           <SelectItem value={0}>0</SelectItem>
          <SelectItem value={1}>1</SelectItem>
          <SelectItem value={2}>2</SelectItem>
          <SelectItem value={3}>3</SelectItem>
          <SelectItem value={4}>4</SelectItem>
          <SelectItem value={5}>5</SelectItem>
          <SelectItem value={6}>6</SelectItem>
          <SelectItem value={7}>7</SelectItem>
          <SelectItem value={8}>8</SelectItem>
          <SelectItem value={9}>9</SelectItem>
          <SelectItem value={10}>10</SelectItem>
        </Select>
    </div>
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
              <p>{message.content}</p>
            </div>
          ))}
          {ourmodelloading && <p>Loading... <CircularProgress aria-label="Loading..." /></p>}
          
        </div>
        <Card>
      <CardBody>
        <CardHeader tag="h5">Ratings Overview</CardHeader>
       
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
      <div className="flex flex-col max-w-xs">
        <p className="block text-sm font-medium text-gray-700">Route Reasonability</p>
        <Select
          label="Select rating"
          placeholder="Select rating"
          value={ratings.ourmodel.routeReasonabilityRating || ''}
          onChange={(e) => handleRatingChange('ourmodel', 'routeReasonabilityRating', e.target.value)}
        >
           <SelectItem value={0}>0</SelectItem>
          <SelectItem value={1}>1</SelectItem>
          <SelectItem value={2}>2</SelectItem>
          <SelectItem value={3}>3</SelectItem>
          <SelectItem value={4}>4</SelectItem>
          <SelectItem value={5}>5</SelectItem>
          <SelectItem value={6}>6</SelectItem>
          <SelectItem value={7}>7</SelectItem>
          <SelectItem value={8}>8</SelectItem>
          <SelectItem value={9}>9</SelectItem>
          <SelectItem value={10}>10</SelectItem>
        </Select>
      </div>

      <div className="flex flex-col max-w-xs">
        <p className="block text-sm font-medium text-gray-700">Representativeness</p>
        <Select
          label="Select rating"
          placeholder="Select rating"
          value={ratings.ourmodel.representativeRating || ''}
          onChange={(e) => handleRatingChange('ourmodel', 'representativeRating', e.target.value)}
        >
          <SelectItem value={0}>0</SelectItem>
          <SelectItem value={1}>1</SelectItem>
          <SelectItem value={2}>2</SelectItem>
          <SelectItem value={3}>3</SelectItem>
          <SelectItem value={4}>4</SelectItem>
          <SelectItem value={5}>5</SelectItem>
          <SelectItem value={6}>6</SelectItem>
          <SelectItem value={7}>7</SelectItem>
          <SelectItem value={8}>8</SelectItem>
          <SelectItem value={9}>9</SelectItem>
          <SelectItem value={10}>10</SelectItem>
        </Select>
        </div>
        <div className="flex flex-col max-w-xs">
    <p className="block text-sm font-medium text-gray-700">Overall rating</p>
            <Select
          label="Select rating"
          placeholder="Select rating"
          value={ratings.ourmodel.overallRating || ''}
          onChange={(e) => handleRatingChange('ourmodel', 'overallRating', e.target.value)}
        >
           <SelectItem value={0}>0</SelectItem>
          <SelectItem value={1}>1</SelectItem>
          <SelectItem value={2}>2</SelectItem>
          <SelectItem value={3}>3</SelectItem>
          <SelectItem value={4}>4</SelectItem>
          <SelectItem value={5}>5</SelectItem>
          <SelectItem value={6}>6</SelectItem>
          <SelectItem value={7}>7</SelectItem>
          <SelectItem value={8}>8</SelectItem>
          <SelectItem value={9}>9</SelectItem>
          <SelectItem value={10}>10</SelectItem>
        </Select>
    </div>
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
            <p>No chat  available</p>
          )}
          {xxmodelmessages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <p>{message.content}</p>
            </div>
          ))}
          {xxmodelloading && <p>Loading... <CircularProgress aria-label="Loading..." /></p>}
        </div>
        <Card>
      <CardBody>
        <CardHeader tag="h5">Ratings Overview</CardHeader>
       
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
    

      <div className="flex flex-col max-w-xs">
        <p className="block text-sm font-medium text-gray-700">Route Reasonability</p>
        <Select
          label="Select rating"
          placeholder="Select rating"
          value={ratings.ourmodel.routeReasonabilityRating || ''}
          onChange={(e) => handleRatingChange('xxmodel', 'routeReasonabilityRating', e.target.value)}
        >
          <SelectItem value={0}>0</SelectItem>
          <SelectItem value={2}>2</SelectItem>
          <SelectItem value={1}>1</SelectItem>
          <SelectItem value={3}>3</SelectItem>
          <SelectItem value={4}>4</SelectItem>
          <SelectItem value={5}>5</SelectItem>
          <SelectItem value={6}>6</SelectItem>
          <SelectItem value={7}>7</SelectItem>
          <SelectItem value={8}>8</SelectItem>
          <SelectItem value={9}>9</SelectItem>
          <SelectItem value={10}>10</SelectItem>
        </Select>
      </div>

      <div className="flex flex-col max-w-xs">
        <p className="block text-sm font-medium text-gray-700">Representativeness</p>
        <Select
          label="Select rating"
          placeholder="Select rating"
          value={ratings.xxmodel.representativeRating || ''}
          onChange={(e) => handleRatingChange('xxmodel', 'representativeRating', e.target.value)}
        >
           <SelectItem value={0}>0</SelectItem>
          <SelectItem value={1}>1</SelectItem>
          <SelectItem value={2}>2</SelectItem>
          <SelectItem value={3}>3</SelectItem>
          <SelectItem value={4}>4</SelectItem>
          <SelectItem value={5}>5</SelectItem>
          <SelectItem value={6}>6</SelectItem>
          <SelectItem value={7}>7</SelectItem>
          <SelectItem value={8}>8</SelectItem>
          <SelectItem value={9}>9</SelectItem>
          <SelectItem value={10}>10</SelectItem>
        </Select>
          </div>
          <div className="flex flex-col max-w-xs">
    <p className="block text-sm font-medium text-gray-700">Overall rating</p>
            <Select
          label="Select rating"
          placeholder="Select rating"
          value={ratings.xxmodel.overallRating || ''}
              onChange={(e) => handleRatingChange('xxmodel', 'overallRating', e.target.value)}
        >
          <SelectItem value={0}>0</SelectItem>
          <SelectItem value={1}>1</SelectItem>
          <SelectItem value={2}>2</SelectItem>
          <SelectItem value={3}>3</SelectItem>
          <SelectItem value={4}>4</SelectItem>
          <SelectItem value={5}>5</SelectItem>
          <SelectItem value={6}>6</SelectItem>
          <SelectItem value={7}>7</SelectItem>
          <SelectItem value={8}>8</SelectItem>
          <SelectItem value={9}>9</SelectItem>
          <SelectItem value={10}>10</SelectItem>
        </Select>
    </div>  
        </div>
      </div>

      {feedbackVisible && (
      <div className="advice-area">
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

      <div className="submit-section">
        <Button onClick={handleSubmitRatings}  >Submit all ratings and feedback</Button>
        
        <Button onClick={handleShowFeedback} >Additional feedback after ratings (Optional)</Button>
      </div>
    </div>
  );
}

export default HomePage;

