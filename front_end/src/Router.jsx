import { BrowserRouter, createBrowserRouter } from "react-router-dom";
import HomePage from "./Page/HomePage";
import AboutPage from "./Page/AboutUs";

const router=createBrowserRouter([
    {
        path:'/',
        element:<HomePage/>
    },
    {
        path:'/about',
        element:<AboutPage/>
    },
   
])
export default router;