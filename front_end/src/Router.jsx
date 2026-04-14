import { BrowserRouter, createBrowserRouter } from "react-router-dom";
import HomePage from "./Page/HomePage";
import AboutPage from "./Page/AboutUs";
import DevAdminPage from "./Page/DevAdminPage";
import EvalPage from "./Page/EvalPage";

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
    {
        path:'/eval',
        element:<EvalPage/>
    },

])
export default router;