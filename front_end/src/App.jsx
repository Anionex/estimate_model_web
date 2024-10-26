import {Card, CardHeader, CardBody, CardFooter, Divider, Link, Image} from "@nextui-org/react";
import NavBar from "./NavBar";
import { RouterProvider } from "react-router-dom"
import router from './Router';
export default function App() {
  return (
    <div className="w-full flex flex-col">
    <NavBar />
    <RouterProvider router={router} />
  </div>
  );
}
