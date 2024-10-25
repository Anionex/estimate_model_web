import React, { useState, useEffect } from "react";
import axios from "axios";
import ApiUtill from "../ApiUtill";
import '../App.css';
import {Card, CardHeader, CardBody, Button,Textarea,CardFooter, Divider, Link, Image} from "@nextui-org/react";
import {Select, SelectSection, SelectItem} from "@nextui-org/select";
import {CircularProgress} from "@nextui-org/react";
import ReactMarkdown from 'react-markdown';

// Define rating options array
const ratingOptions = [...Array(11)].map((_, i) => ({
  value: String(i),
  label: String(i)
}));

// Create a reusable rating selector component
const RatingSelect = ({ label, value, onChange }) => (
  <div className="flex flex-col max-w-xs">
    <div className="block text-sm font-medium text-gray-700">{label}</div>
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

    const systemMessage = {"role": "system", "content": "Please plan the route in detail according to the following specific rules: 1) Each travel day must have detailed activity arrangements, including main attractions and transportation methods. 2) Ensure that the accommodation suggestions are convenient and within budget. 3) Provide at least one restaurant suggestion and note its specialty dishes. 4) At the end, you must accurately assess and provide values for Accommodation Rating, Attractions Average Rating, Restaurant Average Rating, Overall Rating, with a maximum score of 5, expressed in x/5 format. Note: Do not change the output names, ensure these rating information are listed separately in the last part of the output. Strictly follow the above instructions and format the results as required."};
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
      const newConversationId = response.data.conversation_id;
      setConversationId(newConversationId);
      
      // Update conversation_id in ratings
      setRatings(prevRatings => ({
        ...prevRatings,
        conversation_id: newConversationId
      }));

    } catch (error) {
      console.error("Error starting session:", error);
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
    try {
      // ChatGPT request
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
  
      // Our model request
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
  
      // xx model request
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
    const allRatingTypes = ['overallRating', 'routeReasonabilityRating', 'representativeRating'];

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
          overall_rating: ratings.gpt.overallRating,
          route_reasonability_rating: ratings.gpt.routeReasonabilityRating,
          representative_rating: ratings.gpt.representativeRating
        },
        ourmodel: {
          overall_rating: ratings.ourmodel.overallRating,
          route_reasonability_rating: ratings.ourmodel.routeReasonabilityRating,
          representative_rating: ratings.ourmodel.representativeRating
        },
        xxmodel: {
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
        setInput("");
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
              <ReactMarkdown>{message.content}</ReactMarkdown>
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
              <ReactMarkdown>{message.content}</ReactMarkdown>
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
              <ReactMarkdown>{message.content}</ReactMarkdown>
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

      <div className="flex justify-center" style={{ marginTop: '30px' }}>
        <Button onClick={handleSubmitRatings} style={{ marginRight: '10px' }}>
          Submit all ratings and feedback
        </Button>
        
        <Button onClick={handleShowFeedback} style={{ marginLeft: '10px' }}>
          Additional feedback after ratings (Optional)
        </Button>
      </div>
    </div>
  );
}

export default HomePage;
