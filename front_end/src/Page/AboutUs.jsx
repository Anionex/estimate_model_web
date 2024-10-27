import React from 'react';
import {Card, CardHeader, CardBody, Image} from "@nextui-org/react";

function AboutPage() {
  return (
    <div className="aboutus-content">
      <div className='about-head'>
      <Card className="py-4">
      <CardHeader className="pb-0 pt-2 px-4 flex-col items-start">
        <p className="text-tiny uppercase font-bold">JINAN UNIVERSITY</p>
      </CardHeader>
      <CardBody className="overflow-visible py-2">
        <Image
          alt="JNU Card background"
          className="object-cover rounded-xl"
          src="/jnu.jpg"
          width={270}
        />
      </CardBody>
    </Card>
          <h1>Introduction to our GeoAI survey</h1>
          <Card className="py-4">
      <CardHeader className="pb-0 pt-2 px-4 flex-col items-start">
        <p className="text-tiny uppercase font-bold">KENNESAW STATE UNIVERSITY</p>
      </CardHeader>
      <CardBody className="overflow-visible py-2">
        <Image
          alt="Card background"
          className="object-cover rounded-xl"
          src="/ksu.jpg"
          width={270}
        />
      </CardBody>
    </Card>
      </div>
      <div className="about-content">
        
        <h2>Welcome to Our GeoAI Survey!</h2>
        <p>We are a research team focused on exploring and improving the practical applications of GeoAI and generative AI  in the tourism industry.
           Our team consists of members from Kennesaw State University and Jinan University.
            In this survey, we are comparing user satisfaction with three AI models: ChatGPT, the TravelPlanner Agent, and our own improved GeoAI model.
             (Please note, the names of the three models will be hidden during testing.)</p>
        <p>We invite you to evaluate the search results provided by each model and rate their performance. 
          Rest assured, all information collected will remain strictly confidential and will be used exclusively for academic research.
           If you have any questions, please feel free to contact us at<a href=""> qqiu@kennesaw.edu.</a></p>
      </div>
    </div>
  );
}

export default AboutPage;
