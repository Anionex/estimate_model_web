import { BrowserRouter, createBrowserRouter } from "react-router-dom";
import HomePage from "./Page/HomePage";
import AboutPage from "./Page/AboutUs";
import DevAdminPage from "./Page/DevAdminPage";

const router=createBrowserRouter([
    {
        path:'/',
        element:<HomePage/>
    },
    {
        path:'/about',
        element:<AboutPage/>
    },
    {
        path:'/dev_admin',
        element:<DevAdminPage/>
    },
   
])
export default router;